from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class MgtvCrawler(BasePlatformCrawler):
    """芒果TV爬虫"""

    platform_name = "mgtv"
    platform_url = "https://www.mgtv.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://www.mgtv.com/search?query={quote(keyword)}"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # 查找搜索结果条目 - 使用 hitv_horizontal 类（芒果TV搜索结果的主要容器）
        for item in soup.select(".hitv_horizontal"):
            link = item.select_one("a[href*='/b/']")
            if link:
                href = link.get("href", "")
                title = link.get("title", "") or link.get_text(strip=True)
                # 匹配标题中的关键字
                if keyword in title:
                    # 清理 URL 中的 &amp; 转换为 &
                    href = href.replace("&amp;", "&")
                    # 提取干净的 URL（去掉查询参数）
                    if "?" in href:
                        base_url = href.split("?")[0]
                        return base_url
                    return href

        # 备用方案：直接搜索所有包含 /b/ 的链接并匹配标题
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/b/" in href:
                title = a.get("title", "") or a.get_text(strip=True)
                if keyword in title:
                    href = href.replace("&amp;", "&")
                    if "?" in href:
                        return href.split("?")[0]
                    return href

        return None

    async def get_episode_url(self, cover_url: str, season: int, episode: int) -> Optional[str]:
        """
        从 cover 页面提取指定剧集的播放 URL
        cover_url: 如 https://www.mgtv.com/b/743674/24164490.html
        返回: 指定剧集的播放 URL
        """
        from services.browser_pool import get_browser_page

        async with get_browser_page() as page:
            try:
                await page.goto(cover_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)

                # 从页面提取集数信息
                result = await page.evaluate("""
                    (params) => {
                        const targetSeason = params.season;
                        const targetEpisode = params.episode;

                        // 查找集数列表 - 芒果TV 通常在侧边栏或播放列表中
                        // 寻找包含集数信息的元素
                        const episodeLinks = document.querySelectorAll('.episode-item a, .play-list a, [class*="episode"] a[href*="/b/"]');

                        for (const link of episodeLinks) {
                            const href = link.getAttribute('href') || '';
                            const text = link.innerText || '';

                            // 匹配集数 - 格式可能是 "1", "2", "第1集", "E1" 等
                            // 同时匹配 season 信息
                            const episodeMatch = text.match(/第?(\\d+)集?|E?(\\d+)/i);
                            if (episodeMatch) {
                                const episodeNum = parseInt(episodeMatch[1] || episodeMatch[2]);

                                if (episodeNum === targetEpisode) {
                                    // 找到了目标集数
                                    const cleanUrl = href.split('?')[0];
                                    return cleanUrl;
                                }
                            }
                        }

                        // 如果没找到，返回 null
                        return null;
                    }
                """, {"season": season, "episode": episode})

                if result:
                    return result

            except Exception as e:
                print(f"[mgtv] 获取剧集URL失败: {e}")

        return None