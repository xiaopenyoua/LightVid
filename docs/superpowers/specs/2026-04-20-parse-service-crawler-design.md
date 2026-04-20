# 视频解析服务爬虫设计

**日期**: 2026-04-20
**状态**: 已确认

## 目标

将现有的"解析服务爬虫"从固定URL读取器改造成真正的多来源浅度爬虫，自动发现并测试解析服务。

## 设计决策

| 决策点 | 选择 | 原因 |
|--------|------|------|
| 爬取深度 | 浅度（1-2层） | 避免爬虫陷阱，解析服务变化快，深层爬取收益不大 |
| 数据处理 | 与DEFAULT_PARSERS合并去重后测速 | 现有40+解析服务作为保底，动态发现作为补充 |
| 来源类型 | 导航站 + GreasyFork + GitHub | 多来源组合提高稳定性 |
| 扩展性 | 配置化，所有来源可配置 | 方便后续添加新来源 |

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    ParseConfigCrawler                    │
│                     (统一调度器)                          │
├─────────────────────────────────────────────────────────┤
│  1. 从配置读取来源列表                                     │
│  2. 对每个来源执行浅度爬取                                  │
│  3. 提取解析服务URLs                                       │
│  4. 与DEFAULT_PARSERS合并去重                            │
│  5. 测速验证可用性                                        │
│  6. 保存到数据库                                          │
└─────────────────────────────────────────────────────────┘
```

## 来源配置

```python
PARSE_SOURCES = {
    # 导航站/目录站 - 从页面提取解析服务链接
    "navigation_sites": [
        # TODO: 添加导航站URL
    ],

    # GreasyFork用户脚本 - 从脚本源码提取URL
    "greasyfork_scripts": [
        "https://greasyfork.org/en/scripts/541885-主流视频网vip视频解析助手/code",
    ],

    # GitHub仓库/文件 - 读取仓库中的解析服务列表
    "github_sources": [
        # TODO: 添加GitHub源
    ],
}
```

## 爬取策略

| 来源类型 | 爬取方式 | 深度 |
|---------|---------|------|
| 导航站 | 请求页面 → BeautifulSoup提取`<a href>` | 1层（只爬入口页） |
| GreasyFork | 请求JS源码 → 正则匹配URL | 1层 |
| GitHub | 直接请求文件内容 → 正则匹配 | 1层 |

## URL 匹配模式

沿用现有的 `KNOWN_PARSE_PATTERNS`:

```python
KNOWN_PARSE_PATTERNS = [
    r'https?://[^\s"\'<>]+\?url=',
    r'https?://[^\s"\'<>]+\?jx=',
    r'https?://[^\s"\'<>]+/jiexi[^\s"\'<>]*',
    r'https?://[^\s"\'<>]+/player[^\s"\'<>]*',
    r'https?://[^\s"\'<>]+/parse[^\s"\'<>]*',
]
```

## 数据流程

1. **多来源爬取**: 并发从配置的所有来源提取解析服务URLs
2. **合并去重**: 与DEFAULT_PARSERS合并，按URL去重
3. **测速验证**: 并发测试每个解析服务，测量响应时间
4. **保存数据库**: 按响应时间升序排列，保存到parse_configs表

## 文件变更

- `backend/crawlers/parse_config_crawler.py`: 重构核心逻辑
  - 新增 `PARSE_SOURCES` 配置结构
  - 新增 `fetch_from_navigation_sites()` - 爬取导航站
  - 新增 `fetch_from_greasyfork()` - 爬取GreasyFork脚本
  - 新增 `fetch_from_github()` - 爬取GitHub源
  - 重构 `fetch_parse_sources()` 为调度器
  - 保留现有的 `test_parse_config()`, `crawl_and_test_parse_configs()` 等函数

## 待补充

- [ ] 导航站具体URL列表（需调研可靠的导航站）
- [ ] GitHub来源具体URL列表（需调研相关仓库）