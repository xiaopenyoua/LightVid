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

    async def search_browser(self, keyword: str, year: int = None) -> Optional[str]:
        """
        浏览器模式搜索 - 使用 Playwright 渲染页面后提取结果
        从搜索结果页找到视频的 v_show 格式 URL（直接返回第1集，规避验证码）
        """
        from services.browser_pool import get_browser_page

        search_url = self.get_search_url(keyword)

        async with get_browser_page() as page:
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # 从 DOM 中提取视频链接 - 优先找集数链接中的 vid
                result = await page.evaluate("""
                    (searchKeyword) => {
                        // 查找集数列表中的 vid
                        // 优酷集数链接格式: //v.youku.com/video?vid=XNjQ3Nzc2ODgwOA==
                        const links = document.querySelectorAll('a[href*="/video?vid="]');
                        let matched = null;

                        for (const link of links) {
                            const href = link.getAttribute('href') || '';
                            const text = link.innerText || '';

                            // 匹配集数链接（通常文本是纯数字，如 "1", "2", "VIP 3" 等）
                            const episodeMatch = text.match(/^(\\d+|VIP\\s*\\d+)$/);
                            if (episodeMatch) {
                                const vidMatch = href.match(/vid=([^&]+)/);
                                if (vidMatch) {
                                    const vid = vidMatch[1];
                                    matched = `https://v.youku.com/v_show/id_${vid}.html`;
                                    break;
                                }
                            }
                        }

                        // 如果没找到集数链接，尝试查找其他包含 vid 的链接
                        if (!matched) {
                            for (const link of links) {
                                const href = link.getAttribute('href') || '';
                                const vidMatch = href.match(/vid=([^&]+)/);
                                if (vidMatch) {
                                    const vid = vidMatch[1];
                                    matched = `https://v.youku.com/v_show/id_${vid}.html`;
                                    break;
                                }
                            }
                        }

                        return matched;
                    }
                """, keyword)

                if result:
                    return result

            except Exception as e:
                print(f"[youku] 浏览器搜索失败: {e}")

        return None

    async def get_episode_url(self, cover_url: str, season: int, episode: int) -> Optional[str]:
        """
        从 cover 页面提取指定剧集的播放 URL
        cover_url: 如 https://v.youku.com/v_show/id_XNjQ3Nzc2ODgwOA==.html
        返回: 如 https://v.youku.com/v_show/id_XNjQ3Nzc2ODgwOA==.html
        """
        from services.browser_pool import get_browser_page

        # 如果请求的是第1集，且 cover_url 已经是 v_show 格式，直接返回
        if episode == 1:
            return cover_url

        async with get_browser_page() as page:
            try:
                await page.goto(cover_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # 从页面提取集数信息
                result = await page.evaluate("""
                    (params) => {
                        const targetEpisode = params.episode;
                        const links = document.querySelectorAll('a[href*="/video?vid="]');
                        let matched = null;

                        for (const link of links) {
                            const href = link.getAttribute('href') || '';
                            const text = link.innerText || '';

                            // 匹配集数 - 文本格式可能是 "藏海传 第1集" 或 "1" 或 "VIP 3"
                            const episodeMatch = text.match(/第(\\d+)集|^(VIP\\s*)?(\\d+)$/);
                            if (episodeMatch) {
                                let itemEpisode;
                                if (episodeMatch[1]) {
                                    // "第X集" 格式
                                    itemEpisode = parseInt(episodeMatch[1]);
                                } else {
                                    // 纯数字或 VIP 数字
                                    itemEpisode = parseInt(episodeMatch[2] || episodeMatch[3]);
                                }

                                if (itemEpisode === targetEpisode) {
                                    // 提取 vid
                                    const vidMatch = href.match(/vid=([^&]+)/);
                                    if (vidMatch) {
                                        const vid = vidMatch[1];
                                        matched = `https://v.youku.com/v_show/id_${vid}.html`;
                                        break;
                                    }
                                }
                            }
                        }

                        return matched;
                    }
                """, {"episode": episode})

                if result:
                    return result

            except Exception as e:
                print(f"[youku] 获取剧集URL失败: {e}")

        return None