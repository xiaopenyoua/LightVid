# 首页重构实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan.

**Goal:** 将首页改造为「全屏轮播 + 左侧分类导航 + 右侧影片网格」布局

**Architecture:**
- 后端：修改 3 个 schema 文件暴露已有字段，新增 1 个 home 接口字段
- 前端：新建 3 个组件，重写 Home.vue
- 数据流：轮播用 `trending/all/day`（实时），分类用现有 `TmdbGenre`，影片网格用现有 `getMovies`/`getTvShows` API

**Tech Stack:** FastAPI + Vue 3 + Element Plus

---

## 现有状态确认（无需改动）

- `TmdbGenre` 模型已有 `media_type` 字段 ✓
- `TmdbCachedList` 模型已有 `backdrop_url` 字段 ✓
- `sync_genres()` 已保存 `media_type` ✓
- `sync_trending()` 已保存 `backdrop_url` ✓
- `tmdb_service.format_tmdb_item()` 已返回 `backdrop_url` ✓

---

## 文件结构

```
backend/
├── schemas/
│   ├── tmdb_genre.py          # 修改: 新增 media_type 字段
│   └── tmdb_cached_list.py    # 修改: 新增 backdrop_url 字段
└── api/
    └── videos.py              # 修改: /home 新增 trending_all

frontend/src/
├── views/
│   └── Home.vue               # 重写: 三区布局
└── components/
    ├── HeroCarousel.vue       # 新建: 全屏轮播组件
    ├── GenreSidebar.vue       # 新建: 左侧分类导航
    └── FilmGrid.vue           # 新建: 影片网格
```

---

## Task 1: 后端 Schema 改动

**Files:**
- Modify: `backend/schemas/tmdb_genre.py`
- Modify: `backend/schemas/tmdb_cached_list.py`

- [ ] **Step 1: 修改 `TmdbGenreResponse` 新增 media_type 字段**

文件 `backend/schemas/tmdb_genre.py`，找到 `TmdbGenreResponse` 类，在 `name` 字段后新增：

```python
class TmdbGenreResponse(BaseModel):
    id: int
    tmdb_id: int
    name: str
    media_type: str  # 新增: "movie" 或 "tv"
```

- [ ] **Step 2: 修改 `TmdbCachedItemResponse` 新增 backdrop_url 字段**

文件 `backend/schemas/tmdb_cached_list.py`，在现有字段列表中新增：

```python
class TmdbCachedItemResponse(BaseModel):
    tmdb_id: int
    title: str
    media_type: str
    poster_url: Optional[str]
    backdrop_url: Optional[str]  # 新增
    vote_average: Optional[float]
    vote_count: Optional[int]
    popularity: Optional[float]
    overview: Optional[str]
    release_date: Optional[str]
    genre_ids: Optional[str]
    season_number: Optional[int]
```

- [ ] **Step 3: 提交**

```bash
git add backend/schemas/
git commit -m "feat(backend): expose media_type and backdrop_url in schemas"
```

---

## Task 2: 后端 /home 接口新增 trending_all

**Files:**
- Modify: `backend/api/videos.py:22-45`

- [ ] **Step 1: 修改 `get_home` 函数，新增 trending_all**

在 `backend/api/videos.py` 的 `get_home` 函数中，在返回字典的 `lists` 后面新增 `trending_all` 字段。

在函数开头（获取 genres 之后）添加：

```python
# 获取 trending/all/day 用于首页轮播（实时，不走缓存保证新鲜度）
trending_all_raw = await tmdb_service.get_trending(media_type="all", time_window="day")
trending_all = [tmdb_service.format_tmdb_item(r) for r in trending_all_raw[:10]]
```

在返回字典中新增：

```python
return {
    "genres": [TmdbGenreResponse.model_validate(g) for g in genres],
    "lists": {k: [TmdbCachedItemResponse.model_validate(i) for i in v] for k, v in lists.items()},
    "trending_all": [TmdbCachedItemResponse.model_validate(t) for t in trending_all],
}
```

- [ ] **Step 2: 提交**

```bash
git add backend/api/videos.py
git commit -m "feat(backend): add trending_all to /api/videos/home for hero carousel"
```

---

## Task 3: 前端 HeroCarousel 组件

**Files:**
- Create: `frontend/src/components/HeroCarousel.vue`

- [ ] **Step 1: 创建 HeroCarousel.vue**

完整组件，参考 `design-a-revised.html` 中的 hero section 样式：

```vue
<template>
  <section class="hero-section">
    <div class="hero-slides">
      <div
        v-for="(item, index) in items"
        :key="item.tmdb_id"
        class="hero-slide"
        :class="{ active: currentIndex === index }"
        @click="handleClick(item)"
      >
        <img :src="item.backdrop_url" class="hero-bg" :alt="item.title" />
        <div class="hero-gradient"></div>
        <div class="hero-gradient-lr"></div>
      </div>
    </div>

    <!-- Hero Content -->
    <div class="hero-content" v-if="currentItem">
      <span class="hero-badge">🔥 热门推荐</span>
      <h1 class="hero-title">{{ currentItem.title }}</h1>
      <div class="hero-meta">
        <span class="rating">⭐ {{ currentItem.vote_average?.toFixed(1) }}</span>
        <span>{{ currentItem.release_date?.slice(0, 4) }}</span>
        <span>{{ currentItem.media_type === 'movie' ? '电影' : '剧集' }}</span>
      </div>
      <p class="hero-desc">{{ currentItem.overview }}</p>
      <div class="hero-actions">
        <button class="btn-primary" @click.stop="handlePlay(currentItem)">
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          立即播放
        </button>
        <button class="btn-secondary" @click.stop="handleFavorite(currentItem)">
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          收藏
        </button>
      </div>
    </div>

    <!-- Carousel Dots -->
    <div class="carousel-dots">
      <div
        v-for="(item, index) in items"
        :key="item.tmdb_id"
        class="carousel-dot"
        :class="{ active: currentIndex === index }"
        @click="currentIndex = index"
      >
        <div class="dot-line"></div>
        <span class="dot-title">{{ item.title }}</span>
      </div>
    </div>

    <!-- Scroll Indicator -->
    <div class="scroll-indicator">
      <div class="mouse"><div class="wheel"></div></div>
      <span>滚动探索分类</span>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select', 'play', 'favorite'])

const currentIndex = ref(0)
let timer = null

const currentItem = computed(() => props.items[currentIndex.value])

const handleClick = (item) => emit('select', item)
const handlePlay = (item) => emit('play', item)
const handleFavorite = (item) => emit('favorite', item)

const startAutoPlay = () => {
  timer = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % props.items.length
  }, 5000)
}

const stopAutoPlay = () => {
  if (timer) clearInterval(timer)
}

onMounted(() => {
  if (props.items.length > 1) startAutoPlay()
})

onUnmounted(() => stopAutoPlay())
</script>

<style scoped>
.hero-section {
  position: relative;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background: #000;
}
.hero-slides { position: absolute; inset: 0; }
.hero-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 1.2s ease;
  cursor: pointer;
}
.hero-slide.active { opacity: 1; }
.hero-bg {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.55);
}
.hero-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(10,10,15,0.2) 0%, rgba(10,10,15,0.05) 30%, rgba(10,10,15,0.5) 70%, rgba(10,10,15,1) 100%);
}
.hero-gradient-lr {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(10,10,15,0.9) 0%, rgba(10,10,15,0.3) 50%, rgba(10,10,15,0.1) 100%);
}
.hero-content {
  position: absolute;
  bottom: 18%;
  left: 80px;
  max-width: 520px;
  z-index: 10;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 8px 18px;
  border-radius: 24px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 20px;
}
.hero-title {
  font-size: 52px;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: 16px;
  text-shadow: 0 4px 30px rgba(0,0,0,0.5);
}
.hero-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 14px;
  color: rgba(255,255,255,0.7);
}
.hero-meta .rating { color: #fbbf24; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.hero-desc {
  font-size: 15px;
  line-height: 1.7;
  color: rgba(255,255,255,0.8);
  margin-bottom: 28px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.hero-actions { display: flex; gap: 12px; }
.btn-primary {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  padding: 14px 30px;
  border-radius: 30px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.btn-primary:hover {
  transform: scale(1.04);
  box-shadow: 0 15px 40px rgba(99, 102, 241, 0.45);
}
.btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255,255,255,0.2);
  padding: 14px 24px;
  border-radius: 30px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-secondary:hover { background: rgba(255,255,255,0.25); }

/* Carousel Dots */
.carousel-dots {
  position: absolute;
  bottom: 50px;
  left: 80px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}
.carousel-dot {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 0;
}
.carousel-dot .dot-line {
  width: 24px;
  height: 2px;
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
  transition: all 0.3s;
}
.carousel-dot .dot-title {
  font-size: 13px;
  color: rgba(255,255,255,0.5);
  transition: all 0.3s;
  opacity: 0;
  transform: translateX(-10px);
}
.carousel-dot:hover .dot-title,
.carousel-dot.active .dot-title {
  opacity: 1;
  transform: translateX(0);
}
.carousel-dot.active .dot-line {
  width: 48px;
  background: #fff;
}
.carousel-dot:hover .dot-line { background: rgba(255,255,255,0.6); }

/* Scroll Indicator */
.scroll-indicator {
  position: absolute;
  bottom: 40px;
  right: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  z-index: 10;
  color: rgba(255,255,255,0.5);
  font-size: 12px;
  animation: scrollBounce 2s infinite;
}
@keyframes scrollBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(10px); }
}
.scroll-indicator .mouse {
  width: 26px;
  height: 40px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 13px;
  position: relative;
}
.scroll-indicator .wheel {
  width: 4px;
  height: 8px;
  background: rgba(255,255,255,0.5);
  border-radius: 2px;
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/HeroCarousel.vue
git commit -m "feat(frontend): add HeroCarousel component for full-screen backdrop carousel"
```

---

## Task 4: 前端 GenreSidebar 组件

**Files:**
- Create: `frontend/src/components/GenreSidebar.vue`

- [ ] **Step 1: 创建 GenreSidebar.vue**

参考 `design-a-revised.html` 中 `.genre-sidebar` 样式：

```vue
<template>
  <aside class="genre-sidebar">
    <div class="sidebar-header">
      <h2>分类浏览</h2>
    </div>
    <div class="genre-list">
      <!-- 固定导航入口 -->
      <div
        v-for="nav in fixedNav"
        :key="nav.key"
        class="genre-item"
        :class="{ active: activeKey === nav.key }"
        @click="handleNavClick(nav)"
      >
        <div class="genre-icon">{{ nav.icon }}</div>
        <div class="genre-info">
          <div class="genre-name">{{ nav.name }}</div>
        </div>
      </div>

      <!-- 真实类型列表 -->
      <div
        v-for="genre in genres"
        :key="genre.tmdb_id"
        class="genre-item"
        :class="{ active: activeKey === genre.key }"
        @click="handleGenreClick(genre)"
      >
        <div class="genre-icon">{{ getGenreIcon(genre.name) }}</div>
        <div class="genre-info">
          <div class="genre-name">{{ genre.name }}</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  genres: {
    type: Array,
    default: () => []  // [{ tmdb_id, name, media_type }]
  }
})

const emit = defineEmits(['select'])  // select(genre { tmdb_id, name, media_type })

const FIXED_NAV = [
  { key: 'hot', name: '热门推荐', icon: '🔥', media_type: null },
  { key: 'movie', name: '电影', icon: '🎬', media_type: 'movie' },
  { key: 'tv', name: '剧集', icon: '📺', media_type: 'tv' },
]

const activeKey = ref('hot')

const handleNavClick = (nav) => {
  activeKey.value = nav.key
  emit('select', { key: nav.key, name: nav.name, media_type: nav.media_type, tmdb_id: null })
}

const handleGenreClick = (genre) => {
  activeKey.value = `genre-${genre.tmdb_id}`
  emit('select', { key: `genre-${genre.tmdb_id}`, name: genre.name, media_type: genre.media_type, tmdb_id: genre.tmdb_id })
}

const ICON_MAP = {
  '科幻': '🚀', '爱情': '💕', '动作': '🔫', '奇幻': '🗡️',
  '恐怖': '👻', '喜剧': '😂', '剧情': '📜', '悬疑': '🔎',
  '冒险': '🌍', '动画': '🎨', '纪录片': '📽️', '音乐': '🎵',
  '战争': '⚔️', '犯罪': '🚔', '历史': '🏛️', '家庭': '👨‍👩‍👧',
}

const getGenreIcon = (name) => ICON_MAP[name] || '🎬'
</script>

<style scoped>
.genre-sidebar {
  width: 280px;
  height: 100vh;
  position: sticky;
  top: 0;
  background: linear-gradient(180deg, #12121f 0%, #0d0d18 100%);
  border-right: 1px solid rgba(255,255,255,0.06);
  padding: 100px 0 40px;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 0 32px;
  margin-bottom: 24px;
}
.sidebar-header h2 {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 1px;
}
.genre-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}
.genre-list::-webkit-scrollbar { width: 4px; }
.genre-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
.genre-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  margin-bottom: 4px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}
.genre-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 60%;
  background: linear-gradient(180deg, #6366f1, #a855f7);
  border-radius: 2px;
  transition: transform 0.25s;
}
.genre-item:hover {
  background: rgba(255,255,255,0.06);
  transform: scale(1.03);
}
.genre-item.active {
  background: rgba(99, 102, 241, 0.15);
}
.genre-item.active::before {
  transform: translateY(-50%) scaleY(1);
}
.genre-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: transform 0.25s;
}
.genre-item:hover .genre-icon { transform: scale(1.15); }
.genre-item.active .genre-icon {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}
.genre-info { flex: 1; }
.genre-name {
  font-size: 15px;
  font-weight: 500;
  color: rgba(255,255,255,0.85);
  transition: color 0.2s;
}
.genre-item:hover .genre-name,
.genre-item.active .genre-name { color: #fff; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/GenreSidebar.vue
git commit -m "feat(frontend): add GenreSidebar component with fixed nav and genre list"
```

---

## Task 5: 前端 FilmGrid 组件

**Files:**
- Create: `frontend/src/components/FilmGrid.vue`

- [ ] **Step 1: 创建 FilmGrid.vue**

参考 `design-a-revised.html` 中 `.film-grid` 和 `.film-card` 样式：

```vue
<template>
  <div class="film-grid">
    <div
      v-for="item in items"
      :key="item.tmdb_id"
      class="film-card"
      @click="handleClick(item)"
    >
      <div class="poster-wrap">
        <img :src="item.poster_url || 'https://via.placeholder.com/300x450?text=No+Image'" :alt="item.title" />
        <div class="hover-overlay">
          <div class="play-btn" @click.stop="handlePlay(item)">
            <svg width="20" height="20" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </div>
          <div class="film-info">
            <div class="rating">⭐ {{ item.vote_average?.toFixed(1) }}</div>
            <div class="tags" v-if="item.genre_ids">
              <span class="tag" v-for="gid in (item.genre_ids.split(',').slice(0, 2))" :key="gid">
                {{ genreName(gid) }}
              </span>
            </div>
          </div>
        </div>
        <div class="score-badge">⭐ {{ item.vote_average?.toFixed(1) }}</div>
      </div>
      <div class="film-title">{{ item.title }}</div>
      <div class="film-meta">{{ item.release_date?.slice(0, 4) }} · {{ item.media_type === 'movie' ? '电影' : '剧集' }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  genres: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select', 'play'])

const handleClick = (item) => emit('select', item)
const handlePlay = (item) => emit('play', item)

const genreName = (gid) => {
  const g = props.genres.find(g => g.tmdb_id === Number(gid))
  return g ? g.name : ''
}
</script>

<style scoped>
.film-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 24px;
}
.film-card { cursor: pointer; }
.poster-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 12px;
  background: linear-gradient(145deg, #1e1e30, #252540);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s;
}
.film-card:hover .poster-wrap {
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 24px 48px rgba(0,0,0,0.5);
}
.poster-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.hover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 30%, rgba(0,0,0,0.92) 100%);
  opacity: 0;
  transition: opacity 0.3s;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 16px;
}
.film-card:hover .hover-overlay { opacity: 1; }
.play-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  align-self: center;
  transform: scale(0.7);
  opacity: 0;
  transition: all 0.3s 0.1s;
  cursor: pointer;
}
.film-card:hover .play-btn {
  transform: scale(1);
  opacity: 1;
}
.play-btn svg { fill: #1a1a2e; margin-left: 3px; }
.film-info {
  transform: translateY(10px);
  opacity: 0;
  transition: all 0.3s 0.15s;
}
.film-card:hover .film-info {
  transform: translateY(0);
  opacity: 1;
}
.rating {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #fbbf24;
  margin-bottom: 6px;
}
.tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag {
  font-size: 11px;
  color: rgba(255,255,255,0.75);
  background: rgba(255,255,255,0.15);
  padding: 3px 8px;
  border-radius: 8px;
}
.score-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(10px);
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #fbbf24;
}
.film-title {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}
.film-meta {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/FilmGrid.vue
git commit -m "feat(frontend): add FilmGrid component with hover overlay and rating badge"
```

---

## Task 6: 重写 Home.vue

**Files:**
- Rewrite: `frontend/src/views/Home.vue`

- [ ] **Step 1: 重写 Home.vue**

实现设计中的两区布局（Hero + 分类内容区）：

```vue
<template>
  <div class="home">
    <!-- Navigation -->
    <nav class="nav">
      <div class="nav-logo">轻影</div>
      <ul class="nav-links">
        <li><a href="#" class="active">首页</a></li>
        <li><a href="#">电影</a></li>
        <li><a href="#">剧集</a></li>
        <li><a href="#">综艺</a></li>
        <li><a href="#">动漫</a></li>
      </ul>
      <div class="nav-actions">
        <input type="text" class="nav-search" placeholder="搜索电影、剧集..." @keyup.enter="handleSearch" v-model="keyword" />
        <button class="nav-btn">👤</button>
      </div>
    </nav>

    <!-- Hero Section: Full-Screen Carousel -->
    <HeroCarousel
      v-if="homeData?.trending_all?.length"
      :items="homeData.trending_all"
      @select="handleSelect"
      @play="handlePlay"
      @favorite="handleFavorite"
    />

    <!-- Content Section: Genre Sidebar + Film Grid -->
    <section class="content-section">
      <GenreSidebar
        :genres="filteredGenres"
        @select="handleGenreSelect"
      />

      <main class="content-area">
        <div class="content-header">
          <div class="content-title">
            <h2>{{ currentGenre.name }}</h2>
            <span class="genre-tag" v-if="currentGenre.name !== '热门推荐'">按分类浏览</span>
          </div>
        </div>

        <div v-if="loading" v-loading="true" style="min-height: 400px;"></div>
        <FilmGrid
          v-else-if="currentItems.length"
          :items="currentItems"
          :genres="allGenres"
          @select="handleSelect"
          @play="handlePlay"
        />
        <el-empty v-else description="暂无数据" />
      </main>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHome, getMovies, getTvShows, addFavorite } from '../api'
import HeroCarousel from '../components/HeroCarousel.vue'
import GenreSidebar from '../components/GenreSidebar.vue'
import FilmGrid from '../components/FilmGrid.vue'

const router = useRouter()
const loading = ref(false)
const homeData = ref(null)
const currentItems = ref([])
const currentGenre = ref({ key: 'hot', name: '热门推荐', media_type: null, tmdb_id: null })

// 合并电影类型和剧集类型
const filteredGenres = computed(() => homeData.value?.genres || [])
const allGenres = computed(() => homeData.value?.genres || [])

// 热门推荐 = trending_all
const trendingAll = computed(() => homeData.value?.trending_all || [])

const loadHome = async () => {
  try {
    const { data } = await getHome()
    homeData.value = data
    // 默认显示热门推荐
    currentItems.value = trendingAll.value
  } catch {
    ElMessage.error('加载首页数据失败')
  }
}

const loadGenreContent = async (genre) => {
  loading.value = true
  currentItems.value = []
  try {
    if (genre.media_type === 'movie') {
      const { data } = await getMovies({ genre: genre.tmdb_id, page: 1 })
      currentItems.value = data.slice(0, 20)
    } else if (genre.media_type === 'tv') {
      const { data } = await getTvShows({ genre: genre.tmdb_id, page: 1 })
      currentItems.value = data.slice(0, 20)
    } else if (genre.key === 'hot') {
      currentItems.value = trendingAll.value
    } else {
      // 综艺/动漫等未知类型，显示 trending_all 作为兜底
      currentItems.value = trendingAll.value
    }
  } catch {
    currentItems.value = []
  } finally {
    loading.value = false
  }
}

const handleGenreSelect = (genre) => {
  currentGenre.value = genre
  loadGenreContent(genre)
}

const handleSelect = (item) => {
  router.push(`/video/${item.media_type}/${item.tmdb_id}`)
}

const handlePlay = (item) => {
  router.push(`/video/${item.media_type}/${item.tmdb_id}/play`)
}

const handleFavorite = async (item) => {
  try {
    await addFavorite(item.tmdb_id)
    ElMessage.success('收藏成功')
  } catch {
    ElMessage.error('收藏失败')
  }
}

const handleSearch = () => {
  if (keyword.value.trim()) {
    router.push({ path: '/search', query: { q: keyword.value.trim() } })
  }
}

const keyword = ref('')

onMounted(async () => {
  await loadHome()
})
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: #0d0d15;
}

/* Navigation */
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
  padding: 24px 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(180deg, rgba(10,10,15,0.8) 0%, transparent 100%);
}
.nav-logo {
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.nav-links {
  display: flex;
  gap: 8px;
  list-style: none;
}
.nav-links a {
  color: rgba(255,255,255,0.65);
  text-decoration: none;
  padding: 10px 20px;
  border-radius: 24px;
  font-size: 14px;
  transition: all 0.2s;
}
.nav-links a:hover { color: #fff; background: rgba(255,255,255,0.08); }
.nav-links a.active {
  color: #fff;
  background: rgba(255,255,255,0.12);
}
.nav-actions { display: flex; gap: 12px; align-items: center; }
.nav-search {
  width: 200px;
  height: 40px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 20px;
  padding: 0 20px;
  color: #fff;
  font-size: 14px;
}
.nav-search::placeholder { color: rgba(255,255,255,0.4); }
.nav-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 16px;
}

/* Content Section */
.content-section {
  background: #0d0d15;
  display: flex;
  min-height: 100vh;
}
.content-area {
  flex: 1;
  padding: 100px 48px 60px;
  overflow-y: auto;
}
.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}
.content-title {
  display: flex;
  align-items: center;
  gap: 16px;
}
.content-title h2 {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}
.genre-tag {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Home.vue
git commit -m "refactor(frontend): rewrite Home.vue with new three-section layout"
```

---

## Task 7: 联调测试

- [ ] **Step 1: 启动后端验证 API**

```bash
cd /Volumes/ssd/projects-github/LightVid/backend
python -c "
import asyncio
from services.tmdb_service import tmdb_service
async def test():
    r = await tmdb_service.get_trending('all', 'day')
    print(f'trending_all count: {len(r)}')
    print(f'first item keys: {list(r[0].keys()) if r else []}')
asyncio.run(test())
"
```
预期：返回 10+ 条数据，每条包含 backdrop_url

- [ ] **Step 2: 验证 home 接口返回**

启动后端后访问 `GET /api/videos/home`，确认响应包含：
- `genres` 每项有 `media_type`
- `trending_all` 每项有 `backdrop_url`

- [ ] **Step 3: 启动前端验证页面**

```bash
cd /Volumes/ssd/projects-github/LightVid/frontend
npm run dev
```

访问首页验证：
- Hero 轮播正常显示 backdrop 图片
- 左侧分类导航正常渲染
- 点击分类右侧影片网格加载正确数据
