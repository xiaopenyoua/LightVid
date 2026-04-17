from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class IqiyiCrawler(BasePlatformCrawler):
    """爱奇艺爬虫"""

    platform_name = "iqiyi"
    platform_url = "https://www.iqiyi.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://so.iqiyi.com/so/q_{quote(keyword)}?source=input&sr=1&page={page}"

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

    async def search_browser(self, keyword: str, year: int = None) -> Optional[str]:
        """
        浏览器模式搜索 - 使用 Playwright 渲染页面后提取结果
        爱奇艺搜索页是 SPA，内容通过 JS 渲染
        """
        from services.browser_pool import get_browser_page

        search_url = self.get_search_url(keyword)
        search_keyword = keyword.split('第')[0].strip() if '第' in keyword else keyword

        async with get_browser_page() as page:
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # 等待搜索结果出现
                try:
                    await page.wait_for_selector('a[href*="/v_"]', timeout=10000)
                except:
                    pass

                # 从 DOM 中提取视频链接
                result = await page.evaluate("""
                    (searchKeyword) => {
                        const links = document.querySelectorAll('a[href*="/v_"]');
                        let matched = null;
                        let firstValid = null;

                        for (const link of links) {
                            const href = link.href || link.getAttribute('href');
                            if (!href || !href.includes('iqiyi.com') || !href.includes('/v_')) continue;

                            // 获取链接的父元素或邻近文本，检查是否匹配关键词
                            const parent = link.closest('[class*="item"], [class*="result"], [class*="card"]');
                            let linkText = '';
                            if (parent) {
                                linkText = parent.innerText || '';
                            } else {
                                linkText = link.innerText || '';
                            }

                            // 宽松匹配：标题包含搜索词
                            if (linkText.includes(searchKeyword)) {
                                matched = href.split('?')[0]; // 去除查询参数
                                break;
                            }

                            // 记录第一个有效链接作为备选
                            if (!firstValid) {
                                firstValid = href.split('?')[0];
                            }
                        }

                        return matched || firstValid;
                    }
                """, search_keyword)

                if result:
                    return result

            except Exception as e:
                print(f"[iqiyi] 浏览器搜索失败: {e}")

        return None

    async def get_episode_url(self, video_url: str, season: int, episode: int) -> Optional[str]:
        """
        从视频页面提取指定剧集的播放 URL
        video_url: 如 https://www.iqiyi.com/v_pz64qf5dtk.html
        返回: 同上（爱奇艺的视频页面 URL 格式已经包含集数信息）
        """
        # 爱奇艺的 /v_ 链接已经可以直接播放对应剧集
        # 如果传入的是封面页，需要提取具体剧集
        # 目前返回原始 URL，因为爱奇艺的 URL 格式不支持直接替换集数
        return video_url