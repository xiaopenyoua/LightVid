from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class TencentCrawler(BasePlatformCrawler):
    """腾讯视频爬虫"""

    platform_name = "tencent"
    platform_url = "https://v.qq.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://v.qq.com/x/search/?q={quote(keyword)}&page={page}"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        """
        从腾讯视频搜索页 HTML 中提取播放页面 URL
        搜索结果格式: https://v.qq.com/x/cover/{cover_id}.html

        注意：腾讯视频搜索页是 SPA，HTTP 模式会返回空壳 HTML，
        需要使用浏览器模式（search_browser）来获取真实搜索结果
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

        # 方式4: 查找 JavaScript 渲染后的数据（JSON 格式）
        import re
        # 查找 window.__INITIAL_STATE__ 或类似的数据
        script_tags = soup.find_all("script")
        for script in script_tags:
            if script.string:
                # 查找 cover 相关的数据
                cover_matches = re.findall(r'"coverId"\s*:\s*"([^"]+)"', script.string)
                for cover_id in cover_matches:
                    return f"https://v.qq.com/x/cover/{cover_id}.html"

                # 查找 _coverid 或其他格式
                cover_id_matches = re.findall(r'(?:coverid|_coverid|cover_id)\s*[=:]\s*["\']([^"\']+)["\']', script.string, re.I)
                for cover_id in cover_id_matches:
                    return f"https://v.qq.com/x/cover/{cover_id}.html"

        return None

    async def search_browser(self, keyword: str, year: int = None) -> Optional[str]:
        """
        浏览器模式搜索 - 使用 Playwright 渲染页面后提取结果
        通过分析 DOM 中的图片 URL 获取 cover_id，构建播放页 URL
        """
        from services.browser_pool import get_browser_page
        import re

        search_url = self.get_search_url(keyword)
        search_keyword = keyword.split('第')[0].strip() if '第' in keyword else keyword

        async with get_browser_page() as page:
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(5000)

                # 滚动页面触发懒加载
                await page.evaluate('window.scrollTo(0, 300)')
                await page.wait_for_timeout(1000)

                # 直接从 DOM 中查找所有图片的 cover_id，并匹配关键词
                result = await page.evaluate("""
                    (searchKeyword) => {
                        const imgs = document.querySelectorAll('img[src*="vcover"], img[src*="puui"]');
                        let matched = null;

                        for (const img of imgs) {
                            const src = img.src || img.getAttribute('data-src') || '';
                            const match = src.match(/\\/vcover_vt_pic\\/0\\/([^\\/]+)\\//);
                            if (!match) continue;

                            const rawCoverId = match[1];
                            // cover_id 取前15位（腾讯视频 cover_id 格式：mzc002006dzzunf 是14位，substring(0,15)取前14个字符）
                            const coverId = rawCoverId.length > 15 ? rawCoverId.substring(0, 15) : rawCoverId;

                            // 检查图片父元素是否包含搜索关键词
                            const parent = img.closest('[class*="item"], [class*="card"], [class*="result"]');
                            if (parent) {
                                const text = parent.innerText || '';
                                // 宽松匹配：标题包含搜索词
                                if (text.includes(searchKeyword)) {
                                    matched = coverId;
                                    break;
                                }
                            }

                            // 如果还没匹配，且这是第一个图片，记录它作为备选
                            if (!matched) {
                                matched = coverId;
                            }
                        }

                        return matched;
                    }
                """, search_keyword)

                if result:
                    return f"https://v.qq.com/x/cover/{result}.html"

            except Exception as e:
                print(f"[tencent] 浏览器搜索失败: {e}")

        return None

    async def get_episode_url(self, cover_url: str, season: int, episode: int) -> Optional[str]:
        """
        从 cover 页面提取指定剧集的播放 URL
        cover_url: 如 https://v.qq.com/x/cover/mzc002006dzzunf.html
        返回: 如 https://v.qq.com/x/cover/mzc002006dzzunf/h4102lz1osw.html
        """
        from services.browser_pool import get_browser_page

        async with get_browser_page() as page:
            try:
                await page.goto(cover_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # 滚动到顶部以显示剧集列表
                await page.evaluate('window.scrollTo(0, 0)')
                await page.wait_for_timeout(1000)

                # 从页面提取集数信息 - 从 dt-params 属性中获取 vid 和 cover_id
                result = await page.evaluate("""
                    (params) => {
                        const targetSeason = params.season;
                        const targetEpisode = params.episode;

                        // 收集所有匹配的剧集
                        const matches = [];

                        // 查找所有剧集项 .episode-item
                        const items = document.querySelectorAll('.episode-item');
                        for (const item of items) {
                            const text = item.innerText || '';
                            // 匹配集数：可能是 "1"、"2"、"3预告"、"4VIP" 等
                            const episodeMatch = text.match(/^(\\d+)/);
                            if (!episodeMatch) continue;

                            const itemEpisode = parseInt(episodeMatch[1]);
                            // 检查是否是预告版本（有"预告"标签表示还未正式播出）
                            const isTrailer = text.includes('预告');
                            // 检查是否是VIP版本（正式播出的VIP内容）
                            const isVip = text.includes('VIP');

                            // 从 dt-params 中提取 vid 和 cover_id
                            const dtParams = item.getAttribute('dt-params') || '';
                            const vidMatch = dtParams.match(/vid=([^&]+)/);
                            const cidMatch = dtParams.match(/cid=([^&]+)/);
                            if (!vidMatch || !cidMatch) continue;

                            const vid = vidMatch[1];
                            const coverId = cidMatch[1];

                            // 精确匹配剧集（season 暂时只支持1）
                            if (targetSeason === 1 && itemEpisode === targetEpisode) {
                                // 优先级：VIP > 非预告 > 预告
                                // 评分：预告=-1, VIP=2, 非预告非VIP=1
                                let priority = isTrailer ? -1 : (isVip ? 2 : 1);
                                matches.push({ vid, coverId, priority, isTrailer, isVip });
                            }
                        }

                        if (matches.length === 0) return null;

                        // 按优先级排序，选择最高优先级的
                        matches.sort((a, b) => b.priority - a.priority);
                        const best = matches[0];
                        return `https://v.qq.com/x/cover/${best.coverId}/${best.vid}.html`;
                    }
                """, {"season": season, "episode": episode})

                if result:
                    return result

            except Exception as e:
                print(f"[tencent] 获取剧集URL失败: {e}")

        return None