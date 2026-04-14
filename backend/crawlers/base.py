from abc import ABC, abstractmethod
from typing import Optional, List
import httpx
from bs4 import BeautifulSoup


class BasePlatformCrawler(ABC):
    """视频平台爬虫基类"""

    platform_name: str = ""  # 平台标识
    platform_url: str = ""   # 平台根域名

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """获取搜索页 URL，子类实现"""
        raise NotImplementedError

    async def search_http(self, keyword: str, year: int = None) -> Optional[str]:
        """
        HTTP 模式搜索（快速优先）
        子类可覆盖实现特定逻辑
        """
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=15.0),
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            follow_redirects=True
        ) as client:
            search_url = self.get_search_url(keyword)
            try:
                resp = await client.get(search_url)
                resp.raise_for_status()
                return self.extract_play_url(resp.text, keyword, year)
            except Exception as e:
                print(f"[{self.platform_name}] HTTP 搜索失败: {e}")
                return None

    @abstractmethod
    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        """
        从 HTML 中提取播放页面 URL
        子类必须实现
        """
        pass

    def extract_title(self, html: str) -> Optional[str]:
        """从 HTML 中提取标题（可选实现）"""
        soup = BeautifulSoup(html, "lxml")
        title_tag = soup.select_one("title")
        return title_tag.text.strip() if title_tag else None


class BaseBrowserCrawler(ABC):
    """Playwright 浏览器爬虫基类（可选实现，性能较差时启用）"""

    platform_name: str = ""

    async def search_browser(self, keyword: str, year: int = None) -> Optional[str]:
        """浏览器模式搜索（保底）"""
        from services.browser_pool import get_browser

        async with get_browser() as page:
            search_url = self.get_search_url(keyword)
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=20000)
                await self.wait_for_results(page)
                return await self.extract_play_url(page, keyword, year)
            except Exception as e:
                print(f"[{self.platform_name}] 浏览器搜索失败: {e}")
                return None

    @abstractmethod
    def get_search_url(self, keyword: str) -> str:
        """获取搜索页 URL"""
        pass

    @abstractmethod
    async def wait_for_results(self, page):
        """等待搜索结果加载"""
        pass

    @abstractmethod
    async def extract_play_url(self, page, keyword: str, year: int = None) -> Optional[str]:
        """从页面提取播放 URL"""
        pass