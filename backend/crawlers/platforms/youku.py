from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class YoukuCrawler(BasePlatformCrawler):
    """优酷爬虫"""

    platform_name = "youku"
    platform_url = "https://www.youku.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://so.youku.com/search/q_{quote(keyword)}?spm=a2hjn.20147490.J_5254934080.1"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        for item in soup.select(".yk-packager"):
            link = item.select_one("a[href*='/show/']")
            if link:
                href = link.get("href", "")
                if href.startswith("http"):
                    return href

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/show/" in href and href.startswith("http"):
                return href

        return None