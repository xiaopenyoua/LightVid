from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class MgtvCrawler(BasePlatformCrawler):
    """芒果TV爬虫"""

    platform_name = "mgtv"
    platform_url = "https://www.mgtv.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://search.mgtv.com/search?q={quote(keyword)}"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        for item in soup.select(".result-item, .video-item"):
            link = item.select_one("a[href*='/boke/']")
            if link:
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = "https://www.mgtv.com" + href
                return href

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/boke/" in href and href.startswith("http"):
                return href

        return None