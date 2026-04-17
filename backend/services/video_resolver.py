"""
视频解析服务 - 调用第三方解析服务获取 m3u8 链接
"""
import httpx
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models.parse_config import ParseConfig
from crawlers.parse_config_crawler import DEFAULT_PARSERS

async def resolve_video_url(
    platform_url: str,
    parser_url: Optional[str] = None,
    parser_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    使用解析服务解析视频链接（使用浏览器模式获取动态渲染的 m3u8 URL）

    Args:
        platform_url: 视频平台播放页面 URL
        parser_url: 解析服务 URL（不含参数，如 https://jx.xmflv.com/?url=）
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
    # 如果 parser_url 已经包含 ?url= 和 http（完整 URL），直接使用
    # 否则拼接 platform_url
    if "?url=http" in parser_url or "?url=https" in parser_url:
        full_url = parser_url
    else:
        full_url = parser_url + platform_url

    try:
        # 使用 Playwright 浏览器获取动态渲染的 m3u8 URL
        m3u8_url = await _resolve_with_browser(full_url)
        if m3u8_url:
            return {
                "m3u8_url": m3u8_url,
                "parser": parser_name or "未知解析服务",
            }
    except Exception as e:
        print(f"[VideoResolver] 浏览器解析失败: {e}")

    return None


async def _resolve_with_browser(parse_url: str) -> Optional[str]:
    """
    使用 Playwright 浏览器访问解析服务，获取动态渲染的 m3u8 URL

    解析服务的页面是 SPA（单页应用），需要 JavaScript 渲染后才能获取 m3u8 URL
    通过拦截网络请求来捕获 m3u8/mp4 地址
    """
    from services.browser_pool import get_browser_page
    import re

    video_url_found = None
    # 匹配 URL 中包含 .m3u8 或 .mp4 的请求
    url_pattern = re.compile(r'\.(m3u8|mp4)', re.IGNORECASE)

    async with get_browser_page() as page:
        try:
            # 设置网络请求拦截
            def handle_request(request):
                """拦截视频请求，记录 URL"""
                nonlocal video_url_found
                url = request.url
                if url_pattern.search(url) and video_url_found is None:
                    print(f"[_resolve_with_browser] 拦截到视频请求: {url[:100]}...")
                    video_url_found = url

            page.on("request", handle_request)

            # 使用 networkidle 等待所有请求完成（包括 iframe 加载）
            try:
                await page.goto(parse_url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                # networkidle 超时，继续检查已有的请求
                print(f"[_resolve_with_browser] networkidle 超时: {e}")

            # 如果已经找到视频URL，直接返回
            if video_url_found:
                return video_url_found

            # 额外等待 3 秒确保最后的请求也被捕获
            for _ in range(6):
                if video_url_found:
                    break
                await page.wait_for_timeout(500)

            if video_url_found:
                return video_url_found

            # 备用: 检查 video 标签 (可能直接返回 m3u8/mp4)
            video_src = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    return video ? video.src : null;
                }
            """)
            if video_src and ('.m3u8' in video_src or '.mp4' in video_src) and not video_src.startswith('blob:'):
                print(f"[_resolve_with_browser] 从 video 标签获取: {video_src[:100]}...")
                return video_src

            # 备用: 检查 iframe
            iframe_src = await page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe');
                    return iframe ? iframe.src : null;
                }
            """)
            if iframe_src and ('.m3u8' in iframe_src or iframe_src.startswith('http')):
                return iframe_src

            # 备用: 从页面源码中提取
            content = await page.content()
            m3u8_url = extract_m3u8_url(content)
            if m3u8_url:
                return m3u8_url

        except Exception as e:
            print(f"[_resolve_with_browser] 错误: {e}")

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


async def resolve_with_browser_fallback(
    platform_url: str,
    parsers: Optional[List[Dict[str, str]]] = None
) -> Optional[Dict[str, Any]]:
    """
    使用浏览器模式尝试多个解析服务，直到成功
    每次尝试都有超时控制，避免单个解析服务卡住导致整体 pending
    """
    import asyncio

    if parsers is None:
        parsers = DEFAULT_PARSERS

    for parser in parsers:
        parser_base = parser["url"]
        # 如果 parser URL 已经包含完整 URL（包含 ?url= 和一个 http），直接使用，否则拼接
        if "?url=http" in parser_base or "?url=https" in parser_base:
            parser_url = parser_base
        else:
            parser_url = parser_base + platform_url
        parser_name = parser.get("name", "未知解析服务")
        try:
            # 给每个解析服务 25 秒超时
            m3u8_url = await asyncio.wait_for(
                _resolve_with_browser(parser_url),
                timeout=25.0
            )
            if m3u8_url:
                print(f"[resolve_with_browser_fallback] {parser_name} 成功获取 m3u8")
                return {
                    "m3u8_url": m3u8_url,
                    "parser": parser_name,
                }
            else:
                print(f"[resolve_with_browser_fallback] {parser_name} 未获取到 m3u8，继续尝试下一个")
        except asyncio.TimeoutError:
            print(f"[resolve_with_browser_fallback] {parser_name} 超时，跳过")
        except Exception as e:
            print(f"[resolve_with_browser_fallback] {parser_name} 失败: {e}")
            continue

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