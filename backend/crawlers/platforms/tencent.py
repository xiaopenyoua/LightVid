from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class TencentCrawler(BasePlatformCrawler):
    """腾讯视频爬虫"""

    platform_name = "tencent"
    platform_url = "https://v.qq.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://v.qq.com/search.html?page={page}&q={quote(keyword)}&filter=sort=0&source=mix&cbk=1"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        """
        从腾讯视频搜索页 HTML 中提取播放页面 URL
        搜索结果格式: https://v.qq.com/x/cover/{cover_id}.html
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # 方式1: 查找 .result_item 结构
        for item in soup.select(".result_item"):
            title_elem = item.select_one(".title a, .figure_title a")
            if title_elem:
                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")

                # 简单匹配：标题包含关键词
                if keyword.lower() in title.lower() or title.lower() in keyword.lower():
                    if "/cover/" in href:
                        return href

        # 方式2: 直接查找包含 /cover/ 的链接
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/cover/" in href and href.startswith("http"):
                return href

        # 方式3: 查找 _main_card 里的链接
        for item in soup.select("a[href*='/cover/']"):
            href = item.get("href", "")
            if href.startswith("http"):
                return href

        return None