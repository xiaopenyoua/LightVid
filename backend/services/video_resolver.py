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
    {"name": "虾米视频解析", "url": "https://jx.xmflv.com/?url="},
    {"name": "七七云解析", "url": "https://jx.77flv.cc/?url="},
    {"name": "Player-JY", "url": "https://jx.playerjy.com/?url="},
    {"name": "789解析", "url": "https://jiexi.789jiexi.icu:4433/?url="},
    {"name": "极速解析", "url": "https://jx.2s0.cn/player/?url="},
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