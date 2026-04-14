from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class BilibiliCrawler(BasePlatformCrawler):
    """哔哩哔哩爬虫"""

    platform_name = "bilibili"
    platform_url = "https://www.bilibili.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://search.bilibili.com/all?keyword={quote(keyword)}&order=totalrank&duration=0&t=1&page={page}"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # 查找视频结果
        for item in soup.select(".bili-video-card"):
            link = item.select_one("a[href*='/video/']")
            if link:
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = "https:" + href
                return href

        # 备用方式
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/video/BV" in href:
                if not href.startswith("http"):
                    href = "https://www.bilibili.com" + href
                return href

        return None