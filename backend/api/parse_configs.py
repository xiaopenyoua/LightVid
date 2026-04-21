from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models.parse_config import ParseConfig
from schemas.parse_config import ParseConfigCreate, ParseConfigUpdate, ParseConfigResponse
import asyncio

router = APIRouter(prefix="/api/parse-configs", tags=["parse-configs"])


def get_configs(db: Session):
    return db.query(ParseConfig).filter_by(status="active").order_by(ParseConfig.priority.desc()).all()


@router.get("", response_model=list[ParseConfigResponse])
def list_configs(db: Session = Depends(get_db)):
    return get_configs(db)


@router.post("", response_model=ParseConfigResponse)
def create_config(data: ParseConfigCreate, db: Session = Depends(get_db)):
    config = ParseConfig(**data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.put("/{config_id}", response_model=ParseConfigResponse)
def update_config(config_id: int, data: ParseConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(ParseConfig).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(ParseConfig).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    db.delete(config)
    db.commit()
    return {"ok": True}


@router.post("/speed-test/{config_id}", response_model=ParseConfigResponse)
async def speed_test_single(config_id: int, db: Session = Depends(get_db)):
    """对单个解析服务进行两轮测速"""
    config = db.query(ParseConfig).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # 标记为测速中
    config.testing = True
    db.commit()

    try:
        from services.speed_tester import run_speed_test

        # 执行两轮测速
        latency1, latency2 = await run_speed_test(config.base_url)

        # 更新结果
        config.latency1 = latency1
        config.latency2 = latency2
    finally:
        config.testing = False
        db.commit()
        db.refresh(config)

    return config


@router.post("/speed-test-all")
def speed_test_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """启动后台测速任务，立即返回"""
    configs = get_configs(db)

    # 标记所有为测速中
    for config in configs:
        config.testing = True
    db.commit()

    # 添加后台任务
    background_tasks.add_task(speed_test_all_background)

    return {"message": "测速任务已启动", "count": len(configs)}


async def speed_test_all_background():
    """后台执行所有解析服务测速"""
    from database import SessionLocal
    from services.speed_tester import run_speed_test
    import logging

    logger = logging.getLogger("speed_test")
    db = SessionLocal()
    total = len(get_configs(db))
    completed = 0

    try:
        configs = get_configs(db)
        semaphore = asyncio.Semaphore(3)

        async def test_one(config, index):
            nonlocal completed
            logger.info(f"[{index}/{total}] 开始测速: {config.name} ({config.base_url[:50]}...)")

            latency1, latency2 = await run_speed_test(config.base_url)
            config.latency1 = latency1
            config.latency2 = latency2
            config.testing = False
            db.commit()

            completed += 1
            status = f"✓" if latency2 else "✗"
            logger.info(f"[{completed}/{total}] {status} 完成: {config.name} - "
                       f"第一轮: {latency1 or '✗'}s, 第二轮: {latency2 or '✗'}s")

        async def test_with_semaphore(config, index):
            async with semaphore:
                await test_one(config, index)

        tasks = [test_with_semaphore(config, i + 1) for i, config in enumerate(configs)]
        await asyncio.gather(*tasks)

        logger.info(f"[SpeedTest] 全部测速完成 ({completed}/{total})")
    except Exception as e:
        logger.error(f"[SpeedTest] 测速出错: {e}")
    finally:
        db.close()