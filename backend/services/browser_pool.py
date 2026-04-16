"""
浏览器池管理 - 使用 Playwright 管理浏览器实例复用
"""
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

# 全局浏览器实例
_browser = None
_browser_lock = asyncio.Lock()


async def get_browser():
    """获取全局浏览器实例（线程安全）"""
    global _browser

    if _browser is None or not _browser.is_connected():
        async with _browser_lock:
            if _browser is None or not _browser.is_connected():
                from playwright.async_api import async_playwright
                p = await async_playwright().start()
                _browser = await p.chromium.launch(
                    headless=True,  # 无头模式
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ]
                )
                print("[BrowserPool] 浏览器实例已创建")

    return _browser


async def close_browser():
    """关闭全局浏览器实例"""
    global _browser

    if _browser and _browser.is_connected():
        await _browser.close()
        _browser = None
        print("[BrowserPool] 浏览器实例已关闭")


@asynccontextmanager
async def get_browser_page():
    """获取浏览器页面（上下文管理器）- 每次创建新的隔离上下文"""
    browser = await get_browser()
    # 创建独立的浏览器上下文，确保请求之间完全隔离
    context = await browser.new_context(
        # 清除所有 cookie 和缓存
        ignore_https_errors=True,
    )
    page = await context.new_page()

    try:
        yield page
    finally:
        await page.close()
        await context.close()