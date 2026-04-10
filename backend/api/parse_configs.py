from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.parse_config import ParseConfig
from schemas.parse_config import ParseConfigCreate, ParseConfigUpdate, ParseConfigResponse

router = APIRouter(prefix="/api/parse-configs", tags=["parse-configs"])

@router.get("", response_model=list[ParseConfigResponse])
def get_configs(db: Session = Depends(get_db)):
    return db.query(ParseConfig).filter_by(status="active").order_by(ParseConfig.priority.desc()).all()

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
