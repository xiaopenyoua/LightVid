"""
解析服务测速模块 - 提供两轮测速功能

第一轮（httpx）：快速 HTTP 请求预筛选
第二轮（Playwright）：浏览器模拟真实解析场景
"""

import httpx
import asyncio
import re
import time
from typing import Tuple, Optional

# 默认测试视频 URL
DEFAULT_TEST_VIDEO_URL = "https://v.qq.com/x/cover/mzc00200x8gfhok/m4100c4yead.html"


async def test_http(url: str, timeout: float = 10.0) -> Tuple[bool, float]:
    """
    第一轮测试：httpx 快速 HTTP 预筛选

    Args:
        url: 解析服务基础 URL
        timeout: 超时时间（秒）

    Returns:
        (是否可用, 响应时间秒)。不可用时响应时间为 0.0
    """
    test_video_urls = [
        "https://v.qq.com/x/cover/mzc00200x8gfhok/m4100c4yead.html",
        "https://v.qq.com/x/cover/3q0jq9kvr9wvk2x/d4100mokka3.html",
        "https://v.qq.com/x/cover/mzc002006dzzunf/x4102wrphge.html",
        "https://v.youku.com/v_show/id_XNjUxMjc2NDgwNA==.html",
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


async def test_browser(full_url: str, timeout: float = 30.0) -> Tuple[bool, float, str]:
    """
    第二轮测试：Playwright 浏览器深度测试

    Args:
        full_url: 完整的解析服务测试 URL
        timeout: 超时时间（秒）

    Returns:
        (是否可用, 响应时间秒, 视频URL)
    """
    from services.browser_pool import get_browser_page

    video_url_found = None
    url_pattern = re.compile(r'\.(m3u8|mp4)(\?|$)', re.IGNORECASE)
    start_time = time.monotonic()

    try:
        async with get_browser_page() as page:
            def handle_request(request):
                nonlocal video_url_found
                request_url = request.url
                if url_pattern.search(request_url) and video_url_found is None:
                    video_url_found = request_url

            page.on("request", handle_request)

            try:
                await page.goto(full_url, wait_until="networkidle", timeout=timeout * 1000)
            except Exception:
                pass

            for _ in range(6):
                if video_url_found:
                    break
                await page.wait_for_timeout(500)

            if not video_url_found:
                video_src = await page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        if (video && video.src && (video.src.includes('.m3u8') || video.src.includes('.mp4'))) {
                            return video.src;
                        }
                        return null;
                    }
                """)
                if video_src and not video_src.startswith('blob:'):
                    video_url_found = video_src

            elapsed = time.monotonic() - start_time

            if video_url_found:
                return True, round(elapsed, 2), video_url_found[:100]
            else:
                return False, round(elapsed, 2), ""

    except Exception as e:
        elapsed = time.monotonic() - start_time
        return False, round(elapsed, 2), ""


def build_parse_url(base_url: str, video_url: str) -> str:
    """构建完整的解析服务 URL"""
    if "?url=http" in base_url or "?url=https" in base_url:
        return base_url.replace("?url=", f"?url={video_url}")
    elif "?jx=" in base_url:
        return base_url.replace("?jx=", f"?jx={video_url}")
    elif "?v=" in base_url:
        return base_url.replace("?v=", f"?v={video_url}")
    else:
        return base_url + video_url


async def run_speed_test(base_url: str, test_video_url: str = DEFAULT_TEST_VIDEO_URL) -> Tuple[Optional[float], Optional[float]]:
    """
    对解析服务执行两轮测速

    Args:
        base_url: 解析服务基础 URL
        test_video_url: 测试用视频 URL

    Returns:
        (latency1, latency2) - (第一轮延迟, 第二轮延迟)，失败时为 None
    """
    # 第一轮：httpx 快速测试
    available1, latency1 = await test_http(base_url)

    # 第二轮：Playwright 浏览器测试
    full_url = build_parse_url(base_url, test_video_url)
    available2, latency2, _ = await test_browser(full_url, timeout=30.0)

    return (
        round(latency1, 3) if available1 else None,
        round(latency2, 2) if available2 else None
    )