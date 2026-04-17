"""
解析服务爬虫 - 从互联网爬取并测试解析服务，保留可用的
"""
import httpx
import asyncio
import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from models.parse_config import ParseConfig
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 解析服务来源列表
PARSE_SOURCE_URLS = [
    "https://raw.githubusercontent.com/wncx/Parse/master/jx.txt",
]

# 已知的解析服务 URL 模式
KNOWN_PARSE_PATTERNS = [
    r'https?://[^\s"\'<>]+\?url=',
    r'https?://[^\s"\'<>]+\?jx=',
    r'https?://[^\s"\'<>]+/jiexi[^\s"\'<>]*',
    r'https?://[^\s"\'<>]+/player[^\s"\'<>]*',
    r'https?://[^\s"\'<>]+/parse[^\s"\'<>]*',
]

# 默认解析服务列表（启动时初始化用）
DEFAULT_PARSERS = [
    { "url": "https://jx.xmflv.com/?url=", "name": "虾米视频解析" },
    { "url": "https://jx.77flv.cc/?url=", "name": "七七云解析" },
    { "url": "https://jx.playerjy.com/?url=", "name": "Player-JY" },
    { "url": "https://jiexi.789jiexi.icu:4433/?url=", "name": "789解析" },
    { "url": "https://jx.2s0.cn/player/?url=", "name": "极速解析" },
    { "url": "https://bd.jx.cn/?url=", "name": "冰豆解析" },
    { "url": "https://jx.973973.xyz/?url=", "name": "973解析" },
    { "url": "https://www.ckplayer.vip/jiexi/?url=", "name": "CK" },
    { "url": "https://jx.nnxv.cn/tv.php?url=", "name": "七哥解析" },
    { "url": "https://www.yemu.xyz/?url=", "name": "夜幕" },
    { "url": "https://www.pangujiexi.com/jiexi/?url=", "name": "盘古" },
    { "url": "https://www.playm3u8.cn/jiexi.php?url=", "name": "playm3u8" },
    { "url": "https://video.isyour.love/player/getplayer?url=", "name": "芒果TV1" },
    { "url": "https://im1907.top/?jx=", "name": "芒果TV2" },
    { "url": "https://jx.hls.one/?url=", "name": "HLS解析" },
    { "url": "https://jx.jsonplayer.com/player/?url=", "name": "JSON解析" },
    { "url": "https://jx.dj6u.com/?url=", "name": "DJ6U解析" },
    { "url": "https://jx.rdhk.net/?v=", "name": "RDHK解析" },
    { "url": "https://api.okjx.cc:3389/jx.php?url=", "name": "OKJX解析1" },
    { "url": "https://okjx.cc/?url=", "name": "OKJX解析2" },
    { "url": "https://jx.aidouer.net/?url=", "name": "Aidouer解析" },
    { "url": "https://jx.iztyy.com/Bei/?url=", "name": "iztyy解析" },
    { "url": "https://jx.yparse.com/index.php?url=", "name": "yparse解析" },
    { "url": "https://www.mtosz.com/m3u8.php?url=", "name": "mtosz解析" },
    { "url": "https://jx.m3u8.tv/jiexi/?url=", "name": "m3u8tv解析" },
    { "url": "https://parse.123mingren.com/?url=", "name": "123明人解析" },
    { "url": "https://jx.4kdv.com/?url=", "name": "4K解析" },
    { "url": "https://ckmov.ccyjjd.com/ckmov/?url=", "name": "CK解析" },
    { "url": "https://www.8090g.cn/?url=", "name": "8090G解析" },
    { "url": "https://api.qianqi.net/vip/?url=", "name": "千奇解析" },
    { "url": "https://vip.laobandq.com/jiexi.php?url=", "name": "老板解析" },
    { "url": "https://www.administratorw.com/video.php?url=", "name": "管理员解析" },
    { "url": "https://go.yh0523.cn/y.cy?url=", "name": "解析14" },
    { "url": "https://jx.blbo.cc:4433/?url=", "name": "人迷解析" },
    { "url": "http://27.124.4.42:4567/jhjson/ceshi.php?url=", "name": "第一解析" },
    { "url": "https://jx.zui.cm/?url=", "name": "最先解析" },
    { "url": "https://za.kuanjv.com/?url=", "name": "王牌解析" },
    { "url": "http://47.98.234.2:7768/api.php?url=", "name": "293" },
    { "url": "https://play.fuqizhishi.com/maotv/API.php?appkey=xiongdimenbieguaiwodingbuzhulegailekey07201538&url=", "name": "云you秒解" },
]


async def fetch_parse_sources() -> List[Dict[str, str]]:
    """从互联网爬取解析服务 URL"""
    discovered = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        for url in PARSE_SOURCE_URLS:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                text = resp.text

                urls = extract_parse_urls(text)
                for parse_url in urls:
                    name = guess_parse_name(parse_url)
                    discovered.append({"name": name, "url": parse_url})

            except Exception as e:
                print(f"[ParseConfig Crawler] 爬取失败 {url}: {e}")

    return discovered


def extract_parse_urls(text: str) -> List[str]:
    """从文本中提取解析服务 URL"""
    urls = set()

    for pattern in KNOWN_PARSE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for url in matches:
            url = url.rstrip('",;)\'}\n\r ')
            if is_valid_parse_url(url):
                urls.add(url)

    return list(urls)


def is_valid_parse_url(url: str) -> bool:
    """验证是否为有效的解析服务 URL"""
    if not url.startswith(("http://", "https://")):
        return False
    exclude_keywords = [
        "github.com", "raw.githubusercontent.com", "gitee.com",
        "baidu.com", "qq.com", "taobao.com", "alipay.com",
        "bilibili.com", "youku.com", "iqiyi.com", "mgtv.com",
        "v.qq.com", "video.sina.com", "letv.com",
    ]
    for keyword in exclude_keywords:
        if keyword in url.lower():
            return False
    return True


def guess_parse_name(url: str) -> str:
    """从 URL 猜测解析服务名称"""
    patterns = [
        (r'://([^/]+)', None),
        (r'jx\.(\w+)\.', 'jx.{}.解析'),
        (r'parse\.(\w+)\.', 'parse.{}.解析'),
    ]

    for pattern, template in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            if template:
                return template.format(match.group(1))
            return match.group(1)

    parsed = re.sub(r'https?://', '', url)
    parsed = re.sub(r'[/?].*', '', parsed)
    return parsed[:30] if len(parsed) > 30 else parsed


async def test_parse_config(url: str, timeout: float = 10.0) -> Tuple[bool, float]:
    """
    测试解析服务是否可用，并记录响应时间

    使用多个测试视频 URL 测试，只检查响应状态和速度，
    不验证返回内容是否包含 m3u8/mp4（因为解析服务多为 SPA，HTTP 请求无法验证）

    Returns:
        (是否可用, 响应时间秒)。不可用时响应时间为 0.0
    """
    import time

    test_video_urls = [
        "https://v.qq.com/x/cover/mzc00200x8gfhok/m4100c4yead.html",
        "https://v.qq.com/x/cover/3q0jq9kvr9wvk2x/d4100mokka3.html",
        "https://v.qq.com/x/cover/mzc002006dzzunf/x4102wrphge.html",
    ]

    def build_url(base: str, video: str) -> str:
        if "?url=http" in base or "?url=https" in base:
            return base.replace("?url=", f"?url={video}")
        elif "?jx=" in base:
            return base.replace("?jx=", f"?jx={video}")
        elif "?v=" in base:
            return base.replace("?v=", f"?v={video}")
        else:
            return base + video

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5.0), follow_redirects=True) as client:
        for video_url in test_video_urls:
            full_url = build_url(url, video_url)
            try:
                start = time.monotonic()
                resp = await client.get(full_url)
                elapsed = time.monotonic() - start

                if resp.status_code == 200 and len(resp.text) >= 500:
                    return True, round(elapsed, 3)
            except Exception:
                continue

    return False, 0.0


def init_default_parse_configs(db: Session) -> int:
    """初始化默认解析服务到数据库（全覆盖）"""
    # 清空现有解析服务
    db.query(ParseConfig).delete()
    db.commit()

    added = 0
    for parser in DEFAULT_PARSERS:
        config = ParseConfig(
            name=parser["name"],
            base_url=parser["url"],
            priority=50,  # 默认优先级
            status="active"
        )
        db.add(config)
        added += 1

    db.commit()
    print(f"[ParseConfig Crawler] 已初始化 {added} 个默认解析服务")
    return added


async def crawl_and_test_parse_configs(db: Session) -> Tuple[int, int]:
    """
    统一的解析服务更新任务：
    1. 从互联网爬取新的解析服务
    2. 与 DEFAULT_PARSERS 合并去重（url 相同算相同）
    3. 测试所有解析服务
    4. 只保留测试通过的解析服务（全覆盖）

    Returns:
        (爬取数量, 保留数量)
    """
    print("[ParseConfig Crawler] 开始爬取和测试解析服务...")

    # 1. 从互联网爬取解析服务
    discovered = await fetch_parse_sources()
    print(f"[ParseConfig Crawler] 从互联网发现 {len(discovered)} 个解析服务")

    # 2. 合并 DEFAULT_PARSERS 和爬取的解析服务，按 url 去重
    all_parsers = {}
    for parser in DEFAULT_PARSERS:
        all_parsers[parser["url"]] = parser["name"]
    for item in discovered:
        url = item["url"]
        if url not in all_parsers:
            all_parsers[url] = item["name"]

    print(f"[ParseConfig Crawler] 去重后共 {len(all_parsers)} 个解析服务待测试")

    # 3. 测试所有解析服务（并发提升速度）
    async def test_one(url: str, name: str):
        available, elapsed = await test_parse_config(url)
        return name, url, available, elapsed

    tasks = [test_one(url, name) for url, name in all_parsers.items()]
    results = await asyncio.gather(*tasks)

    valid_parsers = []
    for name, url, available, elapsed in results:
        if available:
            valid_parsers.append({"name": name, "url": url, "elapsed": elapsed})
            print(f"[ParseConfig Crawler] ✓ {name} 可用 ({elapsed}s)")
        else:
            print(f"[ParseConfig Crawler] ✗ {name} 不可用")

    # 4. 清空数据库并保存测试通过的解析服务（全覆盖），按响应时间排序
    db.query(ParseConfig).delete()
    # 按响应时间升序排列（快的在前）
    valid_parsers.sort(key=lambda x: x["elapsed"])
    for parser in valid_parsers:
        config = ParseConfig(
            name=parser["name"],
            base_url=parser["url"],
            priority=int(parser["elapsed"] * 1000),  # 毫秒作为优先级，快的优先
            status="active"
        )
        db.add(config)

    db.commit()
    print(f"[ParseConfig Crawler] 测试完成，保留 {len(valid_parsers)}/{len(all_parsers)} 个可用解析服务")

    return len(discovered), len(valid_parsers)