# 首页重构设计文档

## 概述

将首页从现有的「横向滚动分区」布局改造为设计文件 `design-a-revised.html` 中的「全屏轮播 + 左侧分类导航 + 右侧影片网格」布局。

## 设计来源

参考文件：`/Volumes/ssd/projects-github/LightVid/.superpowers/brainstorm/home-design/design-a-revised.html`

## 布局结构

```
┌─────────────────────────────────────────────────────────┐
│  Navigation Bar (logo + nav links + search + avatar)    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  HERO SECTION (100vh)                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Backdrop Image (full screen, dimmed)             │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  Hero Content (left side):                  │ │  │
│  │  │  - Badge: 热门推荐                          │ │  │
│  │  │  - Title: 星际穿越                          │ │  │
│  │  │  - Meta: ⭐9.4 | 2014 | 科幻/冒险 | 3h 9m   │ │  │
│  │  │  - Description (max 3 lines)                │ │  │
│  │  │  - Buttons: 立即播放 / 收藏                  │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  │                                                  │  │
│  │  Carousel Dots (left bottom, vertical)           │  │
│  │  Scroll Indicator (right bottom)                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
├───────────────┬─────────────────────────────────────────┤
│               │                                         │
│  GENRE        │  CONTENT AREA                           │
│  SIDEBAR      │  ┌─────────────────────────────────┐   │
│  (280px)      │  │ Header: 分类名称 + 查看全部 →   │   │
│               │  └─────────────────────────────────┘   │
│  🔥 热门推荐   │  ┌────┐ ┌────┐ ┌────┐ ┌────┐        │
│  🎬 电影      │  │Film│ │Film│ │Film│ │Film│        │
│  📺 剧集      │  │Card│ │Card│ │Card│ │Card│        │
│  🎭 综艺      │  └────┘ └────┘ └────┘ └────┘        │
│  🦸 动漫      │  ┌────┐ ┌────┐ ┌────┐ ┌────┐        │
│  🚀 科幻      │  │Film│ │Film│ │Film│ │Film│        │
│  💕 爱情      │  │Card│ │Card│ │Card│ │Card│        │
│  ...         │  └────┘ └────┘ └────┘ └────┘        │
│               │                                         │
└───────────────┴─────────────────────────────────────────┘
```

## 数据来源

| 模块 | 数据来源 | 接口/方法 |
|---|---|---|
| Hero 轮播 | TMDB `trending/all/day` | 实时调用 TMDB API，后端新增 `trending_all` 字段 |
| 左侧分类导航 | 现有 `TmdbGenre` 表 | 需新增 `media_type` 字段区分 movie/tv |
| 右侧影片网格 | 现有 `getMovies(genre=X)` / `getTvShows(genre=X)` | 前端按 media_type 调对应接口 |

## 后端改动

### 1. Schema 改动

**`TmdbGenreResponse`** - 新增 `media_type` 字段：
```python
class TmdbGenreResponse(BaseModel):
    tmdb_id: int
    name: str
    media_type: str  # 新增: "movie" / "tv"
```

**`TmdbCachedItemResponse`** - 新增 `backdrop_url` 字段：
```python
class TmdbCachedItemResponse(BaseModel):
    # ... 现有字段 ...
    backdrop_url: Optional[str]  # 新增：轮播大图
```

### 2. API 改动

**`GET /api/videos/home`** - 新增 `trending_all` 列表：

返回结构变更：
```json
{
  "genres": [...],                    // 现有，含新增 media_type
  "lists": {                           // 现有
    "trending_movie": [...],
    "popular_movie": [...],
    ...
  },
  "trending_all": [                    // 新增：trending/all/day
    {
      "tmdb_id": 603,
      "title": "The Matrix",
      "media_type": "movie",
      "backdrop_url": "https://image.tmdb.org/...",
      "vote_average": 8.7,
      ...
    }
  ]
}
```

### 3. 前置分类入口

左侧导航顶部需要「热门推荐」「电影」「剧集」「综艺」「动漫」五个固定入口，这些不是真正的 genre，而是媒体类型筛选入口。

方案：前端硬编码这五个固定入口，data 如下：

```javascript
const FIXED_NAV = [
  { key: 'hot', name: '热门推荐', icon: '🔥', media_type: null },
  { key: 'movie', name: '电影', icon: '🎬', media_type: 'movie' },
  { key: 'tv', name: '剧集', icon: '📺', media_type: 'tv' },
  { key: 'variety', name: '综艺', icon: '🎭', media_type: null },
  { key: 'anime', name: '动漫', icon: '🦸', media_type: null },
]
```

真正的类型（科幻、爱情、动作等）来自 `TmdbGenre` 表，前端接在其下方。

## 前端改动

### 1. Home.vue 重构

- 三区布局：Hero（100vh）+ 分类区（100vh，flex 横排）
- Hero 区：轮播组件改为展示 backdrop 大图，叠加渐变遮罩
- 分类区：左侧 280px sticky sidebar + 右侧自适应 content-area

### 2. Carousel.vue 改动

现有 Carousel.vue 是横向滑动行（poster 展示），需要改造或新建 `HeroCarousel.vue`：
- 全屏 backdrop 背景
- 自动轮播 + 手动切换
- 底部竖排 carousel dots（显示影片标题）
- 右侧 scroll indicator

### 3. Film Grid 组件

设计中的 film-card 包含：
- 海报封面（aspect-ratio 2/3）
- Hover 时：播放按钮 + 评分 + 标签浮现
- 左上角评分角标

可新建 `FilmGrid.vue` 或直接内嵌在 Home.vue 中。

## 实现顺序

1. 后端：Schema 改动（TmdbGenreResponse + TmdbCachedItemResponse）
2. 后端：/api/videos/home 新增 trending_all 字段
3. 前端：FilmGrid 组件
4. 前端：HeroCarousel 组件
5. 前端：Home.vue 重构（固定导航 + 左侧分类栏 + 内容区）
6. 测试联调

## 兼容性

此改动仅影响首页 `Home.vue`，其他页面（Search、VideoDetail、Play 等）不受影响。

## 关键文件清单

| 文件 | 操作 |
|---|---|
| `backend/schemas/tmdb_genre.py` | 修改：新增 media_type |
| `backend/schemas/tmdb_cached_list.py` | 修改：新增 backdrop_url |
| `backend/api/videos.py` | 修改：/home 接口新增 trending_all |
| `frontend/src/views/Home.vue` | 重构：新的三区布局 |
| `frontend/src/components/HeroCarousel.vue` | 新建：Hero 轮播组件 |
| `frontend/src/components/FilmGrid.vue` | 新建：影片网格组件 |
| `frontend/src/components/GenreSidebar.vue` | 新建：左侧分类导航组件 |
