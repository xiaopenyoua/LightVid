"""
浏览器池管理 - 使用 Playwright 管理浏览器实例复用

注意：并发控制由调用方负责，这里只管理浏览器实例的生命周期
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
                print("[BrowserPool] 正在创建浏览器实例...")
                try:
                    from playwright.async_api import async_playwright
                    p = await async_playwright().start()
                    print("[BrowserPool] Playwright 已启动")
                    _browser = await p.chromium.launch(
                        headless=True,  # 无头模式
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-dev-shm-usage",
                            "--no-sandbox",
                        ]
                    )
                    print("[BrowserPool] 浏览器实例已创建")
                except Exception as e:
                    print(f"[BrowserPool] 创建浏览器实例失败: {e}")
                    import traceback
                    traceback.print_exc()
                    raise

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
    """获取浏览器页面（上下文管理器）- 每次创建新的隔离上下文

    并发控制由调用方负责，使用统一的信号量限制并发数
    """
    print("[BrowserPool] get_browser_page: 正在获取浏览器...")
    browser = await get_browser()
    print("[BrowserPool] get_browser_page: 浏览器已获取，正在创建上下文...")
    try:
        # 创建独立的浏览器上下文，确保请求之间完全隔离
        context = await browser.new_context(
            # 清除所有 cookie 和缓存
            ignore_https_errors=True,
        )
        print("[BrowserPool] get_browser_page: 上下文已创建")
        page = await context.new_page()
        print("[BrowserPool] get_browser_page: 页面已创建")

        try:
            yield page
        finally:
            print("[BrowserPool] get_browser_page: 正在关闭页面和上下文")
            await page.close()
            await context.close()
            print("[BrowserPool] get_browser_page: 页面和上下文已关闭")
    except Exception as e:
        print(f"[BrowserPool] get_browser_page 错误: {e}")
        import traceback
        traceback.print_exc()
        raise