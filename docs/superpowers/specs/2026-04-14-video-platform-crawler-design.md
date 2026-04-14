# 视频平台爬虫 + 解析播放设计

## 1. 背景与目标

当前问题：用户在前端手动输入视频链接，体验差且需要用户自己找链接。

目标：用户从 TMDB 选择影片 → 选择视频平台（腾讯/爱奇艺等）→ 后端自动在视频平台搜索并获取播放链接 → 解析成 m3u8 → 前端播放。

## 2. 整体流程

```
用户选择 TMDB 影片
    ↓
用户选择视频平台（腾讯/爱奇艺/优酷/哔哩哔哩/芒果TV）
    ↓
后端用浏览器自动化（Playwright）在该视频平台搜索影片
    ↓
获取播放页面 URL
    ↓
调用视频解析服务获取 m3u8 链接
    ↓
返回 m3u8 给前端播放
```

## 3. 技术架构

### 3.1 技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| 浏览器自动化 | Playwright | 模拟浏览器，支持腾讯/爱奇艺/优酷/哔哩哔哩/芒果TV |
| 视频解析 | 复用现有解析服务 | 40+ 解析服务可选 |
| 视频播放 | HLS.js | 前端播放 m3u8，不依赖 iframe |
| 爬虫存储 | SQLite | 缓存播放页面 URL，减少重复爬取 |

### 3.2 目录结构

```
backend/
├── services/
│   ├── video_searcher.py      # 视频平台搜索服务
│   ├── video_resolver.py     # 视频解析服务
│   └── browser_pool.py       # 浏览器池管理
├── crawlers/
│   ├── platforms/            # 各平台爬虫
│   │   ├── tencent.py        # 腾讯视频
│   │   ├── iqiyi.py          # 爱奇艺
│   │   ├── youku.py          # 优酷
│   │   ├── bilibili.py       # 哔哩哔哩
│   │   └── mgtv.py           # 芒果TV
│   └── base.py               # 爬虫基类
└── api/
    ├── play.py               # 播放相关 API（已有，扩展）
    └── search.py             # 新增：搜索 API
```

## 4. 数据库模型

### 4.1 新增表：VideoPlatformLink（视频平台链接缓存）

```python
class VideoPlatformLink(Base):
    __tablename__ = "video_platform_links"

    id = Column(Integer, primary_key=True)
    tmdb_id = Column(Integer, nullable=False, index=True)        # TMDB 影片 ID
    media_type = Column(String)                                  # movie / tv
    platform = Column(String, nullable=False)                    # tencent / iqiyi / youku / bilibili / mgtv
    platform_url = Column(String, nullable=False)                # 播放页面 URL
    title = Column(String)                                       # 平台返回的标题（用于匹配）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)                # 过期时间（缓存）
```

## 5. API 设计

### 5.1 搜索视频链接

**POST** `/api/search/video-link`

Request:
```json
{
    "tmdb_id": 12345,
    "media_type": "movie",
    "platform": "tencent"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "platform": "tencent",
        "platform_url": "https://v.qq.com/x/cover/xxx.html",
        "title": "流浪地球2"
    }
}
```

逻辑：
1. 查缓存，有且未过期 → 直接返回
2. 无缓存 → 启动 Playwright 爬虫
3. 搜索影片 → 获取播放页面 URL → 存入缓存 → 返回

### 5.2 解析视频链接

**POST** `/api/play/resolve`

Request:
```json
{
    "platform_url": "https://v.qq.com/x/cover/xxx.html",
    "parser_id": 0  // 使用默认解析服务
}
```

Response:
```json
{
    "success": true,
    "data": {
        "m3u8_url": "https://xxx.com/xxx.m3u8",
        "parser": "虾米视频解析"
    }
}
```

### 5.3 获取可用的解析服务

**GET** `/api/play/parsers`

Response:
```json
{
    "success": true,
    "data": [
        {"id": 0, "name": "虾米视频解析", "url": "https://jx.xmflv.com/?url="},
        {"id": 1, "name": "七七云解析", "url": "https://jx.77flv.cc/?url="}
    ]
}
```

## 6. 各平台爬虫实现

### 6.1 通用流程

每个平台的爬虫遵循统一接口：

```python
class BasePlatformCrawler(ABC):
    @abstractmethod
    async def search(self, keyword: str, year: int = None) -> Optional[str]:
        """搜索影片，返回播放页面 URL"""
        pass

    @abstractmethod
    def get_search_url(self, keyword: str) -> str:
        """获取搜索页 URL"""
        pass
```

### 6.2 腾讯视频爬虫示例

```python
class TencentCrawler(BasePlatformCrawler):
    SEARCH_URL = "https://v.qq.com/search.html?page=1&search失常"
    PLAYER_URL_PATTERN = "https://v.qq.com/x/cover/{cover_id}.html"

    async def search(self, keyword: str, year: int = None) -> Optional[str]:
        async with get_browser() as page:
            # 1. 访问搜索页
            search_url = self.get_search_url(keyword)
            await page.goto(search_url, wait_until="networkidle")

            # 2. 等待搜索结果加载
            await page.wait_for_selector(".result_item", timeout=10000)

            # 3. 提取第一个结果的链接
            first_result = await page.query_selector(".result_item a")
            if first_result:
                return await first_result.get_attribute("href")

        return None
```

### 6.3 各平台注意事项

| 平台 | 搜索 URL | 反爬策略 |
|------|----------|----------|
| 腾讯视频 | v.qq.com/search.html | 需要等待 networkidle，跳过验证码 |
| 爱奇艺 | so.iqiyi.com/so/search | 延迟加载，需要滚动页面 |
| 优酷 | so.youku.com/search | 可能有验证码 |
| 哔哩哔哩 | search.bilibili.com | 需要处理分页，API 较友好 |
| 芒果TV | search.mgtv.com | 相对简单 |

## 7. 解析服务集成

### 7.1 解析流程

1. 接收播放页面 URL
2. 选择一个可用的解析服务
3. 拼接 URL：`解析服务URL + encodeURIComponent(播放页面URL)`
4. 发送请求，获取响应中的 m3u8 链接
5. 验证 m3u8 是否可访问

### 7.2 解析服务管理

- 解析服务列表从配置文件或数据库加载
- 支持按优先级排序
- 自动测速，优先使用响应快的服务
- 解析失败时自动切换下一个服务

## 8. 前端修改

### 8.1 Play.vue 改造

**移除**：用户手动输入视频链接的功能
**新增**：
1. TMDB 影片信息展示区
2. 视频平台选择器
3. 搜索按钮
4. m3u8 播放（使用 HLS.js）

### 8.2 播放流程

```
用户选择影片 → 选择平台 → 点击播放
    → 调用 /api/search/video-link 获取播放 URL
    → 调用 /api/play/resolve 获取 m3u8
    → HLS.js 播放 m3u8
```

## 9. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 搜索无结果 | 返回提示"该平台暂无资源" |
| 解析服务全部失败 | 返回提示"解析失败，请稍后重试" |
| 浏览器启动失败 | 降级到无头模式，或返回错误 |
| m3u8 链接无效 | 切换解析服务重试 |
| 缓存过期 | 自动重新爬取 |

## 10. 实施计划

### Phase 1: 基础架构
- [ ] 安装 Playwright
- [ ] 实现浏览器池管理
- [ ] 实现数据库模型

### Phase 2: 爬虫实现
- [ ] 实现 BasePlatformCrawler 基类
- [ ] 实现腾讯视频爬虫
- [ ] 实现爱奇艺爬虫
- [ ] 实现优酷爬虫
- [ ] 实现哔哩哔哩爬虫
- [ ] 实现芒果TV爬虫

### Phase 3: API 开发
- [ ] 实现搜索 API
- [ ] 实现解析 API
- [ ] 实现解析服务管理

### Phase 4: 前端改造
- [ ] 改造 Play.vue
- [ ] 集成 HLS.js
- [ ] 测试完整流程

## 11. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 视频平台反爬 | 使用 Playwright 模拟真人行为，设置随机延迟 |
| 解析服务不稳定 | 维护多个解析服务，自动切换 |
| 浏览器资源占用 | 使用浏览器池复用，控制并发数 |
| IP 被封 | 考虑使用代理池（可选） |