"""
解析服务爬虫 - 从互联网爬取并测试解析服务，保留可用的
"""
import httpx
import asyncio
import re
import random
import time
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from models.parse_config import ParseConfig
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# GitHub反封禁策略配置
GITHUB_REQUEST_DELAY = (1.0, 3.0)  # 请求之间的随机延时范围（秒）
GITHUB_API_DELAY = (2.0, 5.0)  # GitHub API请求之间的延时（秒，较长因为API限制严格）

# User-Agent列表，模拟不同浏览器
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
]


def get_random_user_agent() -> str:
    """随机获取一个User-Agent"""
    return random.choice(USER_AGENTS)


def get_random_delay(min_delay: float = 1.0, max_delay: float = 3.0) -> float:
    """获取随机延时"""
    return random.uniform(min_delay, max_delay)


async def github_request_with_retry(client, url: str, max_retries: int = 3) -> httpx.Response:
    """
    发送GitHub请求，带有重试机制和反封禁策略

    Args:
        client: httpx AsyncClient
        url: 请求URL
        max_retries: 最大重试次数

    Returns:
        httpx.Response对象
    """
    headers = {"User-Agent": get_random_user_agent()}

    for attempt in range(max_retries):
        try:
            # 随机延时
            delay = get_random_delay(*GITHUB_REQUEST_DELAY)
            await asyncio.sleep(delay)

            resp = await client.get(url, headers=headers)
            return resp
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # 递增等待时间
                print(f"[ParseConfig Crawler] 请求失败，等待 {wait_time}秒后重试: {url}")
                time.sleep(wait_time)
            else:
                raise e

    raise Exception(f"请求失败，已达到最大重试次数: {url}")

# 解析服务来源配置
# 可以添加多个来源，爬虫会从每个来源提取解析服务URL
PARSE_SOURCES = {
    # 导航站/目录站 - 从页面提取解析服务链接
    "navigation_sites": [
        # TODO: 添加导航站URL，例如：
        # "https://www.example.com/parse/",
    ],

    # GreasyFork用户脚本 - 从脚本源码提取URL
    "greasyfork_scripts": [
        "https://greasyfork.org/en/scripts/541885-主流视频网vip视频解析助手/code",
    ],

    # GitHub仓库/文件 - 读取仓库中的解析服务列表
    # 支持两种格式：
    # - 文件URL: https://github.com/user/repo/blob/branch/path/file.txt (直接获取该文件)
    # - 仓库URL: https://github.com/user/repo (获取仓库中所有文本文件)
    "github_sources": [
        # TODO: 添加GitHub源，例如：
        # "https://raw.githubusercontent.com/xxx/jx.txt",
        # "https://github.com/user/repo",  # 仓库URL
        "https://github.com/ZhuJD-China/FreeVideos",
        "https://github.com/hl2341685/tv",
        "https://github.com/RemotePinee/AudioVisual"
    ],

    # GitHub仓库递归爬取（当URL是仓库时，爬取所有文件）
    # 注意：启用后可能会触发GitHub API限流，建议谨慎使用
    "github_recursive": True,

    # GitHub自动搜索（通过GitHub API搜索解析服务列表文件）
    # 注意：需要GitHub Token，否则会触发限流，建议禁用
    "github_search_enabled": True,
}

# 已知的解析服务 URL 模式
KNOWN_PARSE_PATTERNS = [
    r'https?://[^\s"\'<>]+\?url=',
    r'https?://[^\s"\'<>]+\?jx=',
    r'https?://[^\s"\'<>]+/jiexi[^\s"\'<>]*',
    r'https?://[^\s"\'<>]+/player[^\s"\'<>]*',
    r'https?://[^\s"\'<>]+/parse[^\s"\'<>]*',
]

# 默认解析服务列表（启动时初始化用）
DEFAULT_PARSERS = [
    { "url": "https://jx.xmflv.com/?url=", "name": "虾米视频解析" },
    { "url": "https://jx.77flv.cc/?url=", "name": "七七云解析" },
    { "url": "https://jx.playerjy.com/?url=", "name": "Player-JY" },
    { "url": "https://jiexi.789jiexi.icu:4433/?url=", "name": "789解析" },
    { "url": "https://jx.2s0.cn/player/?url=", "name": "极速解析" },
    { "url": "https://bd.jx.cn/?url=", "name": "冰豆解析" },
    { "url": "https://jx.973973.xyz/?url=", "name": "973解析" },
    { "url": "https://www.ckplayer.vip/jiexi/?url=", "name": "CK" },
    { "url": "https://jx.nnxv.cn/tv.php?url=", "name": "七哥解析" },
    { "url": "https://www.yemu.xyz/?url=", "name": "夜幕" },
    { "url": "https://www.pangujiexi.com/jiexi/?url=", "name": "盘古" },
    { "url": "https://www.playm3u8.cn/jiexi.php?url=", "name": "playm3u8" },
    { "url": "https://video.isyour.love/player/getplayer?url=", "name": "芒果TV1" },
    { "url": "https://im1907.top/?jx=", "name": "芒果TV2" },
    { "url": "https://jx.hls.one/?url=", "name": "HLS解析" },
    { "url": "https://jx.jsonplayer.com/player/?url=", "name": "JSON解析" },
    { "url": "https://jx.dj6u.com/?url=", "name": "DJ6U解析" },
    { "url": "https://jx.rdhk.net/?v=", "name": "RDHK解析" },
    { "url": "https://api.okjx.cc:3389/jx.php?url=", "name": "OKJX解析1" },
    { "url": "https://okjx.cc/?url=", "name": "OKJX解析2" },
    { "url": "https://jx.aidouer.net/?url=", "name": "Aidouer解析" },
    { "url": "https://jx.iztyy.com/Bei/?url=", "name": "iztyy解析" },
    { "url": "https://jx.yparse.com/index.php?url=", "name": "yparse解析" },
    { "url": "https://www.mtosz.com/m3u8.php?url=", "name": "mtosz解析" },
    { "url": "https://jx.m3u8.tv/jiexi/?url=", "name": "m3u8tv解析" },
    { "url": "https://parse.123mingren.com/?url=", "name": "123明人解析" },
    { "url": "https://jx.4kdv.com/?url=", "name": "4K解析" },
    { "url": "https://ckmov.ccyjjd.com/ckmov/?url=", "name": "CK解析" },
    { "url": "https://www.8090g.cn/?url=", "name": "8090G解析" },
    { "url": "https://api.qianqi.net/vip/?url=", "name": "千奇解析" },
    { "url": "https://vip.laobandq.com/jiexi.php?url=", "name": "老板解析" },
    { "url": "https://www.administratorw.com/video.php?url=", "name": "管理员解析" },
    { "url": "https://go.yh0523.cn/y.cy?url=", "name": "解析14" },
    { "url": "https://jx.blbo.cc:4433/?url=", "name": "人迷解析" },
    { "url": "http://27.124.4.42:4567/jhjson/ceshi.php?url=", "name": "第一解析" },
    { "url": "https://jx.zui.cm/?url=", "name": "最先解析" },
    { "url": "https://za.kuanjv.com/?url=", "name": "王牌解析" },
    { "url": "http://47.98.234.2:7768/api.php?url=", "name": "293" },
    { "url": "https://play.fuqizhishi.com/maotv/API.php?appkey=xiongdimenbieguaiwodingbuzhulegailekey07201538&url=", "name": "云you秒解" },
]


async def fetch_parse_sources() -> List[Dict[str, str]]:
    """从互联网爬取解析服务 URL（多来源调度器）"""
    discovered = []

    # 并发从所有来源爬取
    tasks = []

    # 导航站
    if PARSE_SOURCES.get("navigation_sites"):
        tasks.append(fetch_from_navigation_sites(PARSE_SOURCES["navigation_sites"]))

    # GreasyFork
    if PARSE_SOURCES.get("greasyfork_scripts"):
        tasks.append(fetch_from_greasyfork(PARSE_SOURCES["greasyfork_scripts"]))

    # GitHub
    if PARSE_SOURCES.get("github_sources"):
        tasks.append(fetch_from_github(PARSE_SOURCES["github_sources"]))

    # GitHub自动搜索（如果启用）
    if PARSE_SOURCES.get("github_search_enabled", False):
        tasks.append(fetch_from_github_search())

    # 并发执行所有任务
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                print(f"[ParseConfig Crawler] 爬取任务异常: {result}")
            else:
                discovered.extend(result)
    else:
        print("[ParseConfig Crawler] 警告: 没有配置任何来源，请添加来源到 PARSE_SOURCES")

    return discovered


def extract_parse_urls(text: str) -> List[str]:
    """从文本中提取解析服务 URL"""
    urls = set()

    for pattern in KNOWN_PARSE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for url in matches:
            url = url.rstrip('",;)\'}\n\r ')
            if is_valid_parse_url(url):
                urls.add(url)

    return list(urls)


async def fetch_from_navigation_sites(navigation_sites: List[str]) -> List[Dict[str, str]]:
    """从导航站/目录站爬取解析服务"""
    discovered = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        for site_url in navigation_sites:
            try:
                resp = await client.get(site_url)
                resp.raise_for_status()
                text = resp.text

                urls = extract_parse_urls(text)
                for parse_url in urls:
                    name = guess_parse_name(parse_url)
                    discovered.append({"name": name, "url": parse_url})
                    print(f"[ParseConfig Crawler] 从导航站发现: {name} - {parse_url}")

            except Exception as e:
                print(f"[ParseConfig Crawler] 导航站爬取失败 {site_url}: {e}")

    return discovered


async def fetch_from_greasyfork(greasyfork_scripts: List[str]) -> List[Dict[str, str]]:
    """从GreasyFork用户脚本爬取解析服务"""
    discovered = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        for script_url in greasyfork_scripts:
            try:
                # GreasyFork的/code路径需要follow_redirects来获取实际内容
                resp = await client.get(script_url, follow_redirects=True)
                resp.raise_for_status()

                text = resp.text
                urls = extract_parse_urls(text)

                for parse_url in urls:
                    name = guess_parse_name(parse_url)
                    discovered.append({"name": f"GreasyFork-{name}", "url": parse_url})
                    print(f"[ParseConfig Crawler] 从GreasyFork发现: {name} - {parse_url}")

            except Exception as e:
                print(f"[ParseConfig Crawler] GreasyFork爬取失败 {script_url}: {e}")

    return discovered


def convert_github_url_to_raw(github_url: str) -> str:
    """
    将GitHub Web URL转换为raw.githubusercontent.com URL

    支持的格式：
    - https://github.com/user/repo/blob/branch/path/to/file -> https://raw.githubusercontent.com/user/repo/branch/path/to/file
    """
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)', github_url)
    if match:
        user, repo, branch, path = match.groups()
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
    return github_url


def is_github_repo_url(url: str) -> bool:
    """检查是否是GitHub仓库URL（没有具体文件路径）"""
    # 如果URL不包含 /blob/ 并且是正则匹配到 github.com/user/repo 格式
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/?$', url)
    return match is not None


async def fetch_readme_from_repo(client, repo_url: str) -> str:
    """
    从GitHub仓库获取README内容
    尝试 main 和 master 分支

    使用反封禁策略：随机延时 + User-Agent轮换
    """
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/?$', repo_url)
    if not match:
        return ""

    user, repo = match.groups()

    # 尝试 main 分支
    for branch in ['main', 'master']:
        # 随机延时
        await asyncio.sleep(get_random_delay(*GITHUB_REQUEST_DELAY))

        readme_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/README.md"
        try:
            headers = {"User-Agent": get_random_user_agent()}
            resp = await client.get(readme_url, headers=headers)
            if resp.status_code == 200:
                print(f"[ParseConfig Crawler] 成功获取README: {readme_url}")
                return resp.text
        except Exception:
            continue

    return ""


async def get_repo_default_branch(client, user: str, repo: str) -> str:
    """
    通过GitHub API获取仓库的默认分支名
    使用反封禁策略：User-Agent轮换 + 随机延时
    """
    try:
        # 随机延时（GitHub API限制更严格）
        delay = get_random_delay(*GITHUB_API_DELAY)
        await asyncio.sleep(delay)

        api_url = f"https://api.github.com/repos/{user}/{repo}"
        headers = {"User-Agent": get_random_user_agent()}
        resp = await client.get(api_url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("default_branch", "main")
        elif resp.status_code == 403:
            print(f"[ParseConfig Crawler] GitHub API限流，等待更长时间...")
            await asyncio.sleep(30)  # 遇到限流等待30秒
    except Exception as e:
        print(f"[ParseConfig Crawler] 获取仓库默认分支失败: {e}")
    return "main"


async def fetch_repo_recursive(client, user: str, repo: str, branch: str, path: str = "", discovered: list = None) -> List[Dict[str, str]]:
    """
    递归爬取GitHub仓库中的所有文本文件

    使用反封禁策略：
    - 随机User-Agent轮换
    - 请求之间随机延时
    - GitHub API请求更长的延时

    Args:
        client: httpx AsyncClient
        user: GitHub用户名
        repo: 仓库名
        branch: 分支名
        path: 当前路径
        discovered: 已发现的解析服务列表

    Returns:
        发现的解析服务URL列表
    """
    if discovered is None:
        discovered = []

    # 避免无限递归，限制深度
    max_depth = 5
    current_depth = path.count('/')
    if current_depth >= max_depth:
        return discovered

    try:
        # 随机延时（GitHub API限制更严格）
        delay = get_random_delay(*GITHUB_API_DELAY)
        await asyncio.sleep(delay)

        # 使用GitHub API获取目录内容
        api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}?ref={branch}"
        headers = {"User-Agent": get_random_user_agent()}
        resp = await client.get(api_url, headers=headers)

        if resp.status_code == 403:
            print(f"[ParseConfig Crawler] GitHub API限流，停止递归爬取...")
            return discovered

        resp.raise_for_status()
        contents = resp.json()

        if not isinstance(contents, list):
            # 如果是文件而不是目录，直接返回
            return discovered

        for item in contents:
            if item.get("type") == "file":
                # 检查文件类型，只处理文本文件
                filename = item.get("name", "")
                file_ext = filename.split('.')[-1].lower() if '.' in filename else ''

                # 只处理文本格式的文件
                text_extensions = ['txt', 'md', 'json', 'yml', 'yaml', 'xml', 'html', 'htm', 'py', 'js', 'ts']
                if file_ext in text_extensions:
                    # 获取文件内容
                    file_path = item.get("path", "")
                    raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}"
                    try:
                        # 随机延时后再请求文件
                        await asyncio.sleep(get_random_delay(*GITHUB_REQUEST_DELAY))
                        file_resp = await client.get(raw_url, headers={"User-Agent": get_random_user_agent()})
                        if file_resp.status_code == 200:
                            text = file_resp.text
                            # 从文件内容中提取解析服务URL
                            urls = extract_parse_urls(text)
                            for parse_url in urls:
                                name = guess_parse_name(parse_url)
                                discovered.append({"name": f"GitHub-{name}", "url": parse_url})
                                print(f"[ParseConfig Crawler] 从GitHub仓库发现: {name} - {parse_url}")
                    except Exception:
                        pass

            elif item.get("type") == "dir":
                # 递归处理子目录
                sub_path = item.get("path", "")
                await fetch_repo_recursive(client, user, repo, branch, sub_path, discovered)

    except Exception as e:
        print(f"[ParseConfig Crawler] 爬取仓库目录失败 {path}: {e}")

    return discovered


async def fetch_from_github(github_sources: List[str]) -> List[Dict[str, str]]:
    """
    从GitHub源爬取解析服务

    使用反封禁策略：
    - 随机User-Agent轮换
    - 请求之间随机延时
    """
    discovered = []
    recursive = PARSE_SOURCES.get("github_recursive", False)

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        for source_url in github_sources:
            try:
                text = ""

                # 随机延时
                await asyncio.sleep(get_random_delay(*GITHUB_REQUEST_DELAY))

                # 判断URL类型
                if '/blob/' in source_url:
                    # 文件URL：转换为raw URL并获取内容
                    raw_url = convert_github_url_to_raw(source_url)
                    print(f"[ParseConfig Crawler] 转换GitHub URL: {source_url} -> {raw_url}")
                    headers = {"User-Agent": get_random_user_agent()}
                    resp = await client.get(raw_url, headers=headers)
                    resp.raise_for_status()
                    text = resp.text

                    # 从内容中提取解析服务URL
                    urls = extract_parse_urls(text)
                    for parse_url in urls:
                        name = guess_parse_name(parse_url)
                        discovered.append({"name": f"GitHub-{name}", "url": parse_url})
                        print(f"[ParseConfig Crawler] 从GitHub发现: {name} - {parse_url}")

                elif is_github_repo_url(source_url):
                    # 仓库URL
                    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/?$', source_url)
                    if not match:
                        continue

                    user, repo = match.groups()

                    if recursive:
                        # 递归爬取所有文件
                        print(f"[ParseConfig Crawler] 递归爬取仓库: {source_url}")
                        branch = await get_repo_default_branch(client, user, repo)
                        print(f"[ParseConfig Crawler] 仓库默认分支: {branch}")
                        await fetch_repo_recursive(client, user, repo, branch, "", discovered)
                    else:
                        # 只获取README内容
                        print(f"[ParseConfig Crawler] 获取仓库README: {source_url}")
                        text = await fetch_readme_from_repo(client, source_url)
                        if text:
                            urls = extract_parse_urls(text)
                            for parse_url in urls:
                                name = guess_parse_name(parse_url)
                                discovered.append({"name": f"GitHub-{name}", "url": parse_url})
                                print(f"[ParseConfig Crawler] 从GitHub发现: {name} - {parse_url}")
                        else:
                            print(f"[ParseConfig Crawler] 无法获取仓库README: {source_url}")

                else:
                    # 已经是raw URL或其他URL，直接获取
                    headers = {"User-Agent": get_random_user_agent()}
                    resp = await client.get(source_url, headers=headers)
                    resp.raise_for_status()
                    text = resp.text

                    urls = extract_parse_urls(text)
                    for parse_url in urls:
                        name = guess_parse_name(parse_url)
                        discovered.append({"name": f"GitHub-{name}", "url": parse_url})
                        print(f"[ParseConfig Crawler] 从GitHub发现: {name} - {parse_url}")

            except Exception as e:
                print(f"[ParseConfig Crawler] GitHub源爬取失败 {source_url}: {e}")

    return discovered


async def fetch_from_github_search() -> List[Dict[str, str]]:
    """
    通过GitHub API搜索解析服务列表文件

    使用反封禁策略：
    - 随机User-Agent轮换
    - 请求之间随机延时
    - GitHub API请求更长的延时

    搜索关键词包括 jx.txt, parse.json, video parser等
    返回找到的raw文件URL列表
    """
    discovered = []

    # GitHub搜索关键词
    search_queries = [
        "jx.txt",
        "parse.json",
        "video+parser+list",
        "m3u8+parser+list",
    ]

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        for query in search_queries:
            try:
                # 随机延时（GitHub API限制更严格）
                delay = get_random_delay(*GITHUB_API_DELAY)
                await asyncio.sleep(delay)

                # 使用GitHub API搜索代码
                api_url = f"https://api.github.com/search/code?q={query}+in:path&per_page=10"
                headers = {"User-Agent": get_random_user_agent()}
                resp = await client.get(api_url, headers=headers)

                if resp.status_code == 403:
                    print(f"[ParseConfig Crawler] GitHub API限流，停止搜索...")
                    break

                resp.raise_for_status()
                data = resp.json()

                for item in data.get("items", []):
                    # 获取文件信息并构建raw URL
                    html_url = item.get("html_url", "")
                    repo_url = item.get("repository", {}).get("html_url", "")
                    path = item.get("path", "")

                    # 转换blob URL为raw URL
                    raw_url = convert_github_url_to_raw(html_url) if "/blob/" in html_url else None
                    if not raw_url:
                        # 手动构建raw URL
                        match = re.match(r'https://github\.com/([^/]+)/([^/]+)', repo_url)
                        if match:
                            user, repo = match.groups()
                            raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/main/{path}"
                        else:
                            continue

                    # 避免重复
                    if raw_url not in [d["url"] for d in discovered]:
                        name = guess_parse_name(raw_url)
                        discovered.append({"name": f"GitHub搜索-{name}", "url": raw_url})
                        print(f"[ParseConfig Crawler] 从GitHub搜索发现: {name} - {raw_url}")

            except Exception as e:
                print(f"[ParseConfig Crawler] GitHub搜索失败 (query={query}): {e}")

    return discovered


def is_valid_parse_url(url: str) -> bool:
    """验证是否为有效的解析服务 URL"""
    if not url.startswith(("http://", "https://")):
        return False
    exclude_keywords = [
        "github.com", "raw.githubusercontent.com", "gitee.com",
        "baidu.com", "qq.com", "taobao.com", "alipay.com",
        "bilibili.com", "youku.com", "iqiyi.com", "mgtv.com",
        "v.qq.com", "video.sina.com", "letv.com",
    ]
    for keyword in exclude_keywords:
        if keyword in url.lower():
            return False
    return True


def guess_parse_name(url: str) -> str:
    """从 URL 猜测解析服务名称"""
    patterns = [
        (r'://([^/]+)', None),
        (r'jx\.(\w+)\.', 'jx.{}.解析'),
        (r'parse\.(\w+)\.', 'parse.{}.解析'),
    ]

    for pattern, template in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            if template:
                return template.format(match.group(1))
            return match.group(1)

    parsed = re.sub(r'https?://', '', url)
    parsed = re.sub(r'[/?].*', '', parsed)
    return parsed[:30] if len(parsed) > 30 else parsed


async def test_parse_config(url: str, timeout: float = 10.0) -> Tuple[bool, float]:
    """
    测试解析服务是否可用，并记录响应时间

    使用多个测试视频 URL 测试，只检查响应状态和速度，
    不验证返回内容是否包含 m3u8/mp4（因为解析服务多为 SPA，HTTP 请求无法验证）

    Returns:
        (是否可用, 响应时间秒)。不可用时响应时间为 0.0
    """
    import time

    test_video_urls = [
        "https://v.qq.com/x/cover/mzc00200x8gfhok/m4100c4yead.html",
        "https://v.qq.com/x/cover/3q0jq9kvr9wvk2x/d4100mokka3.html",
        "https://v.qq.com/x/cover/mzc002006dzzunf/x4102wrphge.html",
    ]

    def build_url(base: str, video: str) -> str:
        if "?url=http" in base or "?url=https" in base:
            return base.replace("?url=", f"?url={video}")
        elif "?jx=" in base:
            return base.replace("?jx=", f"?jx={video}")
        elif "?v=" in base:
            return base.replace("?v=", f"?v={video}")
        else:
            return base + video

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5.0), follow_redirects=True) as client:
        for video_url in test_video_urls:
            full_url = build_url(url, video_url)
            try:
                start = time.monotonic()
                resp = await client.get(full_url)
                elapsed = time.monotonic() - start

                if resp.status_code == 200 and len(resp.text) >= 500:
                    return True, round(elapsed, 3)
            except Exception:
                continue

    return False, 0.0


def init_default_parse_configs(db: Session) -> int:
    """初始化默认解析服务到数据库（全覆盖）"""
    # 清空现有解析服务
    db.query(ParseConfig).delete()
    db.commit()

    added = 0
    for parser in DEFAULT_PARSERS:
        config = ParseConfig(
            name=parser["name"],
            base_url=parser["url"],
            priority=50,  # 默认优先级
            status="active"
        )
        db.add(config)
        added += 1

    db.commit()
    print(f"[ParseConfig Crawler] 已初始化 {added} 个默认解析服务")
    return added


async def crawl_and_test_parse_configs(db: Session) -> Tuple[int, int]:
    """
    统一的解析服务更新任务：
    1. 从互联网爬取新的解析服务
    2. 与 DEFAULT_PARSERS 合并去重（url 相同算相同）
    3. 测试所有解析服务
    4. 只保留测试通过的解析服务（全覆盖）

    Returns:
        (爬取数量, 保留数量)
    """
    print("[ParseConfig Crawler] 开始爬取和测试解析服务...")

    # 1. 从互联网爬取解析服务
    discovered = await fetch_parse_sources()
    print(f"[ParseConfig Crawler] 从互联网发现 {len(discovered)} 个解析服务")

    # 2. 合并 DEFAULT_PARSERS 和爬取的解析服务，按 url 去重
    all_parsers = {}
    for parser in DEFAULT_PARSERS:
        all_parsers[parser["url"]] = parser["name"]
    for item in discovered:
        url = item["url"]
        if url not in all_parsers:
            all_parsers[url] = item["name"]

    print(f"[ParseConfig Crawler] 去重后共 {len(all_parsers)} 个解析服务待测试")

    # 3. 测试所有解析服务（并发提升速度）
    async def test_one(url: str, name: str):
        available, elapsed = await test_parse_config(url)
        return name, url, available, elapsed

    tasks = [test_one(url, name) for url, name in all_parsers.items()]
    results = await asyncio.gather(*tasks)

    valid_parsers = []
    for name, url, available, elapsed in results:
        if available:
            valid_parsers.append({"name": name, "url": url, "elapsed": elapsed})
            print(f"[ParseConfig Crawler] ✓ {name} 可用 ({elapsed}s)")
        else:
            print(f"[ParseConfig Crawler] ✗ {name} 不可用")

    # 4. 清空数据库并保存测试通过的解析服务（全覆盖），按响应时间排序
    db.query(ParseConfig).delete()
    # 按响应时间升序排列（快的在前）
    valid_parsers.sort(key=lambda x: x["elapsed"])
    for parser in valid_parsers:
        config = ParseConfig(
            name=parser["name"],
            base_url=parser["url"],
            priority=int(parser["elapsed"] * 1000),  # 毫秒作为优先级，快的优先
            status="active"
        )
        db.add(config)

    db.commit()
    print(f"[ParseConfig Crawler] 测试完成，保留 {len(valid_parsers)}/{len(all_parsers)} 个可用解析服务")

    return len(discovered), len(valid_parsers)