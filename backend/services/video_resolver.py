"""
视频解析服务 - 调用第三方解析服务获取 m3u8 链接
"""
import httpx
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models.parse_config import ParseConfig


# 默认解析服务列表（备用）
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


async def resolve_video_url(
    platform_url: str,
    parser_url: Optional[str] = None,
    parser_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    使用解析服务解析视频链接

    Args:
        platform_url: 视频平台播放页面 URL
        parser_url: 解析服务 URL（不含参数）
        parser_name: 解析服务名称

    Returns:
        {"m3u8_url": "...", "parser": "..."} 或 None
    """
    if not parser_url:
        # 使用默认解析服务
        parser = DEFAULT_PARSERS[0]
        parser_url = parser["url"]
        parser_name = parser["name"]

    # 拼接完整 URL
    full_url = parser_url + platform_url

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=15.0),
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }
        ) as client:
            resp = await client.get(full_url)
            resp.raise_for_status()

            # 尝试从响应中提取 m3u8 URL
            m3u8_url = extract_m3u8_url(resp.text)

            if m3u8_url:
                return {
                    "m3u8_url": m3u8_url,
                    "parser": parser_name or "未知解析服务",
                }

    except Exception as e:
        print(f"[VideoResolver] 解析失败: {e}")

    return None


def extract_m3u8_url(html: str) -> Optional[str]:
    """
    从 HTML 响应中提取 m3u8 URL
    常见模式:
    - 直接包含 .m3u8
    - 在 video/src 属性中
    - 在 JSON 响应中
    """
    # 模式1: 直接匹配 .m3u8 URL
    patterns = [
        r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*',
        r'"m3u8"\s*:\s*"([^"]+)"',
        r"'m3u8'\s*:\s*'([^']+)'",
        r'src\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            url = match.group(1) if match.lastindex else match.group(0)
            if url.startswith("//"):
                url = "https:" + url
            return url

    return None


async def resolve_with_fallback(
    platform_url: str,
    parsers: Optional[List[Dict[str, str]]] = None
) -> Optional[Dict[str, Any]]:
    """
    使用多个解析服务尝试解析，自动切换
    """
    if parsers is None:
        parsers = DEFAULT_PARSERS

    for parser in parsers:
        result = await resolve_video_url(
            platform_url,
            parser_url=parser["url"],
            parser_name=parser["name"]
        )
        if result:
            return result

    return None


def get_parser_list(db: Session) -> List[Dict[str, Any]]:
    """从数据库获取解析服务列表"""
    configs = db.query(ParseConfig).filter_by(status="active").order_by(ParseConfig.priority.asc()).all()

    if not configs:
        return DEFAULT_PARSERS

    return [
        {"name": cfg.name, "url": cfg.base_url}
        for cfg in configs
    ]