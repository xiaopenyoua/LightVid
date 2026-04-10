# LightVid 主页与后端 API 重新设计

> **设计日期：** 2026/04/10
> **核心变化：** 基于 TMDB 深度整合，重构主页布局和后端 API，彻底移除 TMDB 痕迹

---

## 一、设计目标

1. **主页全面升级** — 混合型设计（顶部轮播 + 分区横向滚动），Netflix 式沉浸感 + 豆瓣式信息密度
2. **TMDB 深度整合** — 利用 TMDB 全部相关内容 API，本地只缓存 Genre 列表
3. **业务化 API 命名** — 所有 API 以业务语义命名，前端完全无感知 TMDB
4. **分层缓存策略** — 热门列表本地缓存，详情实时获取，平衡性能和数据新鲜度

---

## 二、数据库设计

### 2.1 新增表：tmdb_genres（类型列表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| tmdb_id | INTEGER | TMDB genre ID |
| name | TEXT | 中文名称，如"动作" |
| media_type | TEXT | "movie" 或 "tv" |

**数据量：** 约 20-40 条，极小。

### 2.2 新增表：tmdb_cached_list（缓存的列表数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| list_type | TEXT | trending / popular / top_rated / upcoming |
| media_type | TEXT | movie / tv |
| tmdb_id | INTEGER | TMDB 电影/剧集 ID |
| title | TEXT | 标题 |
| poster_url | TEXT | 海报 URL |
| backdrop_url | TEXT | 背景图 URL |
| vote_average | REAL | 评分 |
| vote_count | INTEGER | 投票数 |
| popularity | REAL | 热度值 |
| overview | TEXT | 简介 |
| release_date | TEXT | 上映/首播日期 |
| genre_ids | TEXT | 逗号分隔的 genre IDs |
| season_number | INTEGER | 剧集季节号（仅剧集），电影为 NULL |
| cached_at | DATETIME | 缓存时间 |

**数据量：** 每类列表 20 条 × 7 类 ≈ 140 条，极小。

### 2.3 已有表（保持不变）

- `video_sources` — TV Box 播放源
- `parse_configs` — 解析接口配置
- `watch_history` — 观看历史（关联 tmdb_id + media_type）
- `favorites` — 收藏（关联 tmdb_id + media_type）

---

## 三、API 设计

### 3.1 核心业务 API（/api/videos/*）

所有接口以**业务语义**命名，前端完全无感知 TMDB。

| 接口 | 方法 | 说明 | 数据来源 |
|------|------|------|----------|
| `/api/videos/home` | GET | 首页全量数据 | 本地缓存 |
| `/api/videos/genres` | GET | 类型列表（电影+剧集） | 本地库 |
| `/api/videos/movies` | GET | 电影列表，支持 genre 过滤、分页、排序 | 实时 TMDB |
| `/api/videos/tv` | GET | 剧集列表，支持 genre 过滤、分页、排序 | 实时 TMDB |
| `/api/videos/{media_type}/{id}` | GET | 电影/剧集详情 | 实时 TMDB |
| `/api/videos/{media_type}/{id}/seasons/{season}` | GET | 剧集某季详情 | 实时 TMDB |
| `/api/videos/search` | GET | 搜索电影+剧集 | 实时 TMDB |

### 3.2 其他业务 API（保持不变）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/sources` | GET/POST/DELETE | TV Box 播放源管理 |
| `/api/play` | GET | 播放相关 |
| `/api/parse-configs` | GET/POST/PUT/DELETE | 解析接口管理 |
| `/api/history` | GET/POST/DELETE | 观看历史 |
| `/api/favorites` | GET/POST/DELETE | 收藏 |

### 3.3 `/api/videos/home` 响应结构

```json
{
  "genres": [
    { "id": 1, "tmdb_id": 28, "name": "动作", "media_type": "movie" },
    { "id": 2, "tmdb_id": 35, "name": "喜剧", "media_type": "movie" },
    { "id": 3, "tmdb_id": 10765, "name": "科幻", "media_type": "tv" },
    ...
  ],
  "lists": {
    "trending_movie": [ /* 20条 */ ],
    "trending_tv": [ /* 20条 */ ],
    "popular_movie": [ /* 20条 */ ],
    "popular_tv": [ /* 20条 */ ],
    "top_rated_movie": [ /* 20条 */ ],
    "top_rated_tv": [ /* 20条 */ ],
    "upcoming_movie": [ /* 20条 */ ]
  }
}
```

**每个列表项的完整字段（来自 TMDB discover）：**
```json
{
  "tmdb_id": 123,
  "title": "肖申克的救赎",
  "media_type": "movie",
  "poster_url": "https://image.tmdb.org/t/p/w500/xxx.jpg",
  "backdrop_url": "https://image.tmdb.org/t/p/w780/xxx.jpg",
  "vote_average": 9.7,
  "vote_count": 28000,
  "popularity": 500.0,
  "overview": "一场囚犯与狱警之间...",
  "release_date": "1994-09-10",
  "genre_ids": "18,80",
  "season_number": null
}
```

### 3.4 `/api/videos/movies` 和 `/api/videos/tv` 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| genre | integer | - | TMDB genre ID |
| page | integer | 1 | 页码 |
| sort_by | string | popularity.desc | 排序：popularity.desc / vote_average.desc / release_date.desc |

### 3.5 `/api/videos/search` 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| q | string | - | 搜索关键词 |
| page | integer | 1 | 页码 |

---

## 四、前端主页布局

### 4.1 页面结构

```
顶部：轮播（Trending 电影 20张海报自动轮播，5秒切换）
  ↓
分区 1：热门电影（Popular Movies，横向滚动）
分区 2：热门剧集（Popular TV，横向滚动）
分区 3：本周热门（Trending This Week，混合电影+剧集）
分区 4：高分电影（Top Rated Movies）
分区 5：高分剧集（Top Rated TV）
分区 6：即将上映（Upcoming Movies）
分区 7+：按 Genre 分类（动作、喜剧、科幻、恐怖、爱情、动画...）
```

### 4.2 分区交互

- 每个分区横向滚动，支持鼠标拖动
- 点击海报 → 跳转详情页 `/video/{media_type}/{tmdb_id}`
- 剧集海报显示"第X季"标识

### 4.3 视频详情页

- 顶部大背景图 + 海报
- 视频信息（标题、年份、评分、类型、简介）
- 剧集支持切换季节
- 播放按钮 → 跳转播放页

---

## 五、定时任务设计

| 任务 | 频率 | 说明 |
|------|------|------|
| 刷新 Genre 列表 | 每日凌晨 | 同步电影+剧集所有 Genre 到本地库 |
| 刷新 Trending | 每 30 分钟 | `/trending/all/week` |
| 刷新 Popular | 每 1 小时 | `/movie/popular` + `/tv/popular` |
| 刷新 Top Rated | 每 2 小时 | `/movie/top_rated` + `/tv/top_rated` |
| 刷新 Upcoming | 每 6 小时 | `/movie/upcoming` |
| 清理过期缓存 | 每日凌晨 | 删除超过 24 小时的缓存数据 |

---

## 六、技术约束

1. **前端完全无感知 TMDB** — 所有 API 都是 `/api/videos/*`，响应数据中无任何 TMDB 字样
2. **中文优先** — 所有 TMDB 请求带 `language=zh-CN`，简介没有中文则 fallback 到空
3. **剧集多季独立展示** — 每个季节作为独立条目，每季数据单独获取
4. **数据新鲜度** — 热门列表最长 1 小时时滞，详情页实时获取确保完整新鲜

---

## 七、TMDB API 端点映射

| 功能 | TMDB 端点 |
|------|-----------|
| 获取 Genre 列表 | `/genre/movie/list` + `/genre/tv/list` |
| Trending | `/trending/{media_type}/{time_window}` |
| Popular | `/movie/popular` + `/tv/popular` |
| Top Rated | `/movie/top_rated` + `/tv/top_rated` |
| Upcoming | `/movie/upcoming` |
| 电影列表（按 Genre） | `/discover/movie?with_genres=xx` |
| 剧集列表（按 Genre） | `/discover/tv?with_genres=xx` |
| 电影详情 | `/movie/{id}` |
| 剧集详情 | `/tv/{id}` |
| 剧集季详情 | `/tv/{id}/season/{season}` |
| 搜索 | `/search/multi` |

---

## 八、后端模块变更

### 8.1 新增文件

```
backend/
├── models/
│   ├── tmdb_genre.py       # Genre 模型
│   └── tmdb_cached_list.py # 缓存列表模型
├── schemas/
│   ├── tmdb_genre.py       # Genre Pydantic schema
│   └── tmdb_cached_list.py # 缓存列表 Pydantic schema
├── services/
│   ├── sync_service.py     # TMDB 定时同步服务
│   └── tmdb_service.py      # TMDB API 调用（扩展）
├── api/
│   └── videos.py           # 新 API 路由（替代原来的 /douban）
└── schedulers/
    └── sync_scheduler.py   # 定时任务配置
```

### 8.2 删除/废弃

- `api/douban.py` → 替换为 `api/videos.py`
- 手动爬取 API（`/api/douban/crawl/{tmdb_id}`）→ 移除，改为定时任务

---

## 九、实施优先级

1. **Phase 1：** 数据库模型 + TMDB Service 扩展
2. **Phase 2：** 定时同步任务（Genre + 缓存列表）
3. **Phase 3：** 新 API 路由（/api/videos/*）
4. **Phase 4：** 前端主页重构（轮播 + 分区）
5. **Phase 5：** 视频详情页 + 剧集季切换
6. **Phase 6：** 清理旧 API，测试上线
