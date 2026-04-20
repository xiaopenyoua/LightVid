from typing import Optional
from urllib.parse import quote
import httpx
import re
from crawlers.base import BasePlatformCrawler


class BilibiliCrawler(BasePlatformCrawler):
    """哔哩哔哩爬虫 - 专门处理番剧和影视"""

    platform_name = "bilibili"
    platform_url = "https://www.bilibili.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        # 搜索API端点
        return f"https://api.bilibili.com/x/web-interface/search/all?keyword={quote(keyword)}&page={page}&pagesize=10"

    async def search_http(self, keyword: str, year: int = None) -> Optional[str]:
        """
        HTTP 模式搜索番剧/影视
        使用bilibili的API直接获取番剧信息
        """
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=10.0),
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://www.bilibili.com",
            },
            follow_redirects=True
        ) as client:
            search_url = self.get_search_url(keyword)
            try:
                resp = await client.get(search_url)
                resp.raise_for_status()
                return self.extract_play_url(resp.json(), keyword, year)
            except Exception as e:
                print(f"[{self.platform_name}] HTTP 搜索失败: {e}")
                return None

    def extract_play_url(self, data: dict, keyword: str, year: int = None) -> Optional[str]:
        """
        从API响应中提取番剧播放页面URL
        data: bilibili API返回的JSON数据
        返回: 如 https://www.bilibili.com/bangumi/play/ss45969
        """
        try:
            result = data.get('data', {}).get('result', {})
            media_bangumi = result.get('media_bangumi', [])

            if not media_bangumi:
                return None

            for item in media_bangumi:
                title = item.get('title', '')
                # 清理HTML标签
                title = re.sub('<[^<]+?>', '', title)

                # 匹配标题
                if keyword in title:
                    season_id = item.get('season_id')
                    if season_id:
                        return f"https://www.bilibili.com/bangumi/play/ss{season_id}"
        except Exception as e:
            print(f"[{self.platform_name}] 提取播放URL失败: {e}")

        return None

    async def get_episode_url(self, cover_url: str, season: int, episode: int) -> Optional[str]:
        """
        从番剧封面页提取指定剧集的播放URL
        cover_url: 如 https://www.bilibili.com/bangumi/play/ss45969
        返回: 如 https://www.bilibili.com/bangumi/play/ep1524256
        """
        # 从cover_url中提取season_id
        # cover_url格式: https://www.bilibili.com/bangumi/play/ss45969
        match = re.search(r'ss(\d+)', cover_url)
        if not match:
            return None

        season_id = match.group(1)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=10.0),
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://www.bilibili.com",
            },
            follow_redirects=True
        ) as client:
            try:
                # 获取番剧剧集列表
                section_url = f"https://api.bilibili.com/pgc/web/season/section?season_id={season_id}"
                resp = await client.get(section_url)
                resp.raise_for_status()
                data = resp.json()

                if data.get('code') != 0:
                    return None

                result = data.get('result', {})
                main_section = result.get('main_section', {})
                sections = result.get('section', [])

                # 收集所有剧集
                all_episodes = []
                if main_section.get('episodes'):
                    all_episodes.extend(main_section['episodes'])
                for sec in sections:
                    if sec.get('episodes'):
                        all_episodes.extend(sec['episodes'])

                # 查找目标剧集
                for ep in all_episodes:
                    title = str(ep.get('title', ''))
                    if title == str(episode) or title == f'第{episode}集':
                        ep_id = ep.get('id')
                        if ep_id:
                            return f"https://www.bilibili.com/bangumi/play/ep{ep_id}"

                # 如果没找到精确匹配，尝试模糊匹配
                for ep in all_episodes:
                    title = str(ep.get('title', ''))
                    try:
                        if int(title) == episode:
                            ep_id = ep.get('id')
                            if ep_id:
                                return f"https://www.bilibili.com/bangumi/play/ep{ep_id}"
                    except ValueError:
                        continue

            except Exception as e:
                print(f"[{self.platform_name}] 获取剧集URL失败: {e}")

        return None