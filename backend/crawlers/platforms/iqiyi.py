from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class IqiyiCrawler(BasePlatformCrawler):
    """爱奇艺爬虫"""

    platform_name = "iqiyi"
    platform_url = "https://www.iqiyi.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://so.iqiyi.com/so/q_{quote(keyword)}?source=input&sr=1&page=1"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # 查找搜索结果中的播放链接
        for item in soup.select(".qy-search-item, .result-item"):
            link = item.select_one("a[href*='/v_']")
            if link:
                href = link.get("href", "")
                if href.startswith("http"):
                    return href

        # 直接查找包含 /v_ 的链接
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/v_" in href and href.startswith("http"):
                return href

        return None