# 视频详情页重新设计实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将视频详情页重新设计为全屏海报 + 悬浮信息面板风格

**Architecture:** 单页 Vue 组件实现，使用 CSS Grid/Flexbox 布局，背景层叠实现视觉层次，横向滚动区域展示演职人员

**Tech Stack:** Vue 3 (Composition API), Element Plus, 原生 CSS

---

## 文件结构

```
frontend/src/views/VideoDetail.vue    # 主组件（重写）
frontend/src/components/CastScroll.vue  # 演职人员横向滚动组件（新建）
frontend/src/components/Synopsis.vue    # 简介展开收起组件（新建）
frontend/src/components/GenreTags.vue   # 类型标签组件（新建）
```

---

## 任务 1: 创建基础布局和背景层

**文件:**
- Modify: `frontend/src/views/VideoDetail.vue:1-50`

- [ ] **Step 1: 重写模板结构**

```vue
<template>
  <div class="video-detail">
    <!-- 背景层 -->
    <div class="backdrop-container" v-if="video?.backdrop_url || video?.poster_url">
      <img
        :src="video.backdrop_url || video.poster_url"
        class="backdrop-image"
        :class="{ loaded: backdropLoaded }"
        @load="backdropLoaded = true"
      />
      <div class="backdrop-overlay-left"></div>
      <div class="backdrop-overlay-bottom"></div>
    </div>

    <!-- 返回按钮 -->
    <button class="back-button" @click="$router.back()">←</button>

    <!-- 主内容区 -->
    <div class="main-content" v-if="video">
      <!-- 信息面板 -->
      <div class="info-panel">
        <!-- 标题区域 -->
        <h1 class="title">{{ video.title }}</h1>
        <p class="title-en" v-if="video.original_title">{{ video.original_title }}</p>

        <!-- 元数据行 -->
        <div class="meta-row">
          <span class="rating" v-if="video.vote_average">
            <span class="star">★</span> {{ video.vote_average.toFixed(1) }}
          </span>
          <span class="year" v-if="video.release_date">{{ video.release_date.slice(0, 4) }}</span>
          <span class="runtime" v-if="video.runtime">{{ formatRuntime(video.runtime) }}</span>
          <span class="rating-level" v-if="video.adult">R</span>
        </div>

        <!-- 类型标签 -->
        <GenreTags :genres="video.genres" />

        <!-- 简介 -->
        <Synopsis :text="video.overview" />

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <button class="btn-play" @click="goPlay">
            <span class="play-icon">▶</span>
            开始播放
          </button>
          <button class="btn-icon" :class="{ active: isFavorite }" @click="toggleFavorite">
            {{ isFavorite ? '❤' : '♡' }}
          </button>
          <button class="btn-icon" @click="handleShare">
            ↗
          </button>
        </div>

        <!-- 剧集选择器 -->
        <div class="episode-selector" v-if="video.seasons?.length">
          <select v-model="currentSeason" class="season-select" @change="onSeasonChange">
            <option v-for="season in video.seasons" :key="season.season_number" :value="season.season_number">
              {{ season.name }}
            </option>
          </select>
          <div class="episode-grid">
            <button
              v-for="episode in currentEpisodes"
              :key="episode.episode_number"
              class="episode-btn"
              :class="{ active: currentEpisode === episode.episode_number }"
              @click="selectEpisode(episode.episode_number)"
            >
              {{ episode.episode_number }}
            </button>
          </div>
        </div>
      </div>

      <!-- 演职人员滚动区 -->
      <CastScroll :cast="video.cast" />
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="loading-state">
      <LoadingSpinner :size="60" />
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-state">
      <p>加载失败</p>
      <button @click="loadDetail">重试</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 添加响应式样式**

```css
/* 背景层 */
.backdrop-container {
  position: fixed;
  inset: 0;
  z-index: 0;
}
.backdrop-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(20px);
  opacity: 0;
  transition: opacity 0.5s;
}
.backdrop-image.loaded {
  opacity: 0.4;
}
.backdrop-overlay-left {
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, #0d0d1a 0%, transparent 60%);
}
.backdrop-overlay-bottom {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, #0d0d1a 0%, transparent 40%);
}

/* 主内容 */
.main-content {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 80px 5% 60px;
}

/* 信息面板 */
.info-panel {
  max-width: 500px;
}

/* 标题 */
.title {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px;
  line-height: 1.2;
}
.title-en {
  font-size: 16px;
  color: #888;
  margin: 0 0 16px;
}

/* 元数据行 */
.meta-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  font-size: 14px;
  color: #ccc;
}
.rating { color: #f5a623; }
.rating .star { margin-right: 4px; }

/* 响应式 */
@media (max-width: 768px) {
  .main-content {
    padding: 100px 20px 120px;
    justify-content: flex-end;
  }
  .info-panel {
    width: 100%;
  }
  .title { font-size: 28px; }
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/VideoDetail.vue
git commit -m "feat(video-detail): 重写为全屏海报布局
- 添加模糊背景层和渐变遮罩
- 重新设计标题、元数据区域
- 添加响应式样式"
```

---

## 任务 2: 创建 GenreTags 组件

**文件:**
- Create: `frontend/src/components/GenreTags.vue`

- [ ] **Step 1: 创建组件**

```vue
<template>
  <div class="genre-tags">
    <span
      v-for="genre in genres"
      :key="genre.id || genre"
      class="tag"
      @click="handleClick(genre)"
    >
      {{ typeof genre === 'string' ? genre : genre.name }}
    </span>
  </div>
</template>

<script setup>
defineProps({
  genres: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select'])

const handleClick = (genre) => {
  const id = typeof genre === 'string' ? genre : genre.id
  emit('select', id)
}
</script>

<style scoped>
.genre-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.tag {
  padding: 6px 14px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 16px;
  font-size: 13px;
  color: #a5b4fc;
  cursor: pointer;
  transition: all 0.2s;
}
.tag:hover {
  background: rgba(99, 102, 241, 0.25);
  border-color: rgba(99, 102, 241, 0.5);
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/GenreTags.vue
git commit -m "feat(video-detail): 添加 GenreTags 组件"
```

---

## 任务 3: 创建 Synopsis 组件（展开/收起）

**文件:**
- Create: `frontend/src/components/Synopsis.vue`

- [ ] **Step 1: 创建组件**

```vue
<template>
  <div class="synopsis">
    <p class="synopsis-text" :class="{ expanded: isExpanded }">
      {{ text || '暂无简介' }}
    </p>
    <button
      v-if="needsTruncate"
      class="expand-btn"
      @click="isExpanded = !isExpanded"
    >
      {{ isExpanded ? '收起 ▲' : '展开全部 ▼' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  text: {
    type: String,
    default: ''
  },
  maxLines: {
    type: Number,
    default: 3
  }
})

const isExpanded = ref(false)
const needsTruncate = ref(false)

onMounted(() => {
  // 检测文本是否需要截断
  const el = document.querySelector('.synopsis-text')
  if (el) {
    needsTruncate.value = el.scrollHeight > el.clientHeight
  }
})
</script>

<style scoped>
.synopsis {
  margin-bottom: 24px;
}
.synopsis-text {
  font-size: 14px;
  line-height: 1.7;
  color: #ccc;
  margin: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
.synopsis-text.expanded {
  display: block;
  -webkit-line-clamp: unset;
}
.expand-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 13px;
  cursor: pointer;
  padding: 8px 0;
  transition: color 0.2s;
}
.expand-btn:hover {
  color: #fff;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/Synopsis.vue
git commit -m "feat(video-detail): 添加 Synopsis 组件支持展开收起"
```

---

## 任务 4: 创建 CastScroll 组件（演职人员横向滚动）

**文件:**
- Create: `frontend/src/components/CastScroll.vue`

- [ ] **Step 1: 创建组件**

```vue
<template>
  <div class="cast-scroll" v-if="cast?.length">
    <div class="cast-header">
      <h3>导演 & 演员</h3>
      <span class="view-all" v-if="cast.length > 10">查看全部 →</span>
    </div>
    <div class="cast-list" ref="castListRef">
      <div
        v-for="person in displayCast"
        :key="person.id || person.name"
        class="cast-item"
      >
        <div class="cast-avatar">
          <img v-if="person.profile_path" :src="person.profile_path" :alt="person.name" />
          <span v-else class="avatar-placeholder">🎭</span>
        </div>
        <p class="cast-name">{{ person.name }}</p>
        <p class="cast-role">{{ person.character || person.job }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  cast: {
    type: Array,
    default: () => []
  }
})

const displayCast = computed(() => {
  // 显示前12个演员
  return props.cast.slice(0, 12)
})
</script>

<style scoped>
.cast-scroll {
  margin-top: 40px;
  margin-left: 5%;
}
.cast-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.cast-header h3 {
  font-size: 14px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0;
}
.view-all {
  font-size: 13px;
  color: #666;
  cursor: pointer;
}
.view-all:hover {
  color: #fff;
}
.cast-list {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 10px;
  scrollbar-width: none;
}
.cast-list::-webkit-scrollbar {
  display: none;
}
.cast-item {
  flex-shrink: 0;
  width: 80px;
  text-align: center;
}
.cast-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 8px;
  background: #1a1a2e;
}
.cast-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 24px;
}
.cast-name {
  font-size: 13px;
  color: #fff;
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cast-role {
  font-size: 12px;
  color: #666;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/CastScroll.vue
git commit -m "feat(video-detail): 添加 CastScroll 演职人员横向滚动组件"
```

---

## 任务 5: 完善脚本逻辑

**文件:**
- Modify: `frontend/src/views/VideoDetail.vue:45-120`

- [ ] **Step 1: 添加脚本逻辑**

```javascript
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideoDetail, getSeasonDetail, addFavorite, removeFavorite, checkFavorite } from '../api'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import GenreTags from '../components/GenreTags.vue'
import Synopsis from '../components/Synopsis.vue'
import CastScroll from '../components/CastScroll.vue'

const route = useRoute()
const router = useRouter()
const video = ref(null)
const loading = ref(false)
const isFavorite = ref(false)
const currentSeason = ref(1)
const currentEpisode = ref(1)
const backdropLoaded = ref(false)

const mediaType = () => route.params.media_type || 'movie'
const tmdbId = () => parseInt(route.params.id)

const currentEpisodes = computed(() => {
  if (!video.value?.seasonDetails?.episodes) return []
  return video.value.seasonDetails.episodes
})

const formatRuntime = (minutes) => {
  if (!minutes) return ''
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h ? `${h}h ${m}m` : `${m}m`
}

const loadDetail = async () => {
  loading.value = true
  try {
    const { data } = await getVideoDetail(mediaType(), tmdbId())
    video.value = data
    if (video.value?.seasons?.length) {
      currentSeason.value = video.value.seasons[0].season_number
      // 加载第一季详情
      await loadSeasonDetail(currentSeason.value)
    }
    // 检查收藏状态
    try {
      const { data: fav } = await checkFavorite(tmdbId())
      isFavorite.value = fav.is_favorite
    } catch {
      isFavorite.value = false
    }
  } catch {
    ElMessage.error('加载详情失败')
  } finally {
    loading.value = false
  }
}

const loadSeasonDetail = async (season) => {
  try {
    const { data } = await getSeasonDetail(tmdbId(), season)
    video.value.seasonDetails = data
    if (data.episodes?.length) {
      currentEpisode.value = data.episodes[0].episode_number
    }
  } catch {}
}

const onSeasonChange = () => {
  loadSeasonDetail(currentSeason.value)
  router.replace({ query: { ...route.query, season: currentSeason.value } })
}

const selectEpisode = (episode) => {
  currentEpisode.value = episode
  router.replace({ query: { ...route.query, episode } })
}

const toggleFavorite = async () => {
  try {
    if (isFavorite.value) {
      await removeFavorite(tmdbId())
      isFavorite.value = false
      ElMessage.success('已取消收藏')
    } else {
      await addFavorite(tmdbId())
      isFavorite.value = true
      ElMessage.success('已添加收藏')
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

const handleShare = async () => {
  const url = window.location.href
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.info('请手动复制链接')
  }
}

const goPlay = () => {
  const query = { season: currentSeason.value }
  if (mediaType() === 'tv') {
    query.episode = currentEpisode.value
  }
  router.push({ path: `/video/${mediaType()}/${tmdbId()}/play`, query })
}

watch(() => route.params.id, loadDetail)

onMounted(loadDetail)
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/VideoDetail.vue
git commit -m "feat(video-detail): 完成脚本逻辑重构
- 添加剧集季节/集数选择
- 添加分享功能
- 完善收藏状态管理"
```

---

## 任务 6: 添加操作按钮样式

**文件:**
- Modify: `frontend/src/views/VideoDetail.vue` (样式部分)

- [ ] **Step 1: 添加按钮样式**

```css
/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}
.btn-play {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 32px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-play:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4);
}
.play-icon {
  font-size: 14px;
}
.btn-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-icon:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: scale(1.05);
}
.btn-icon.active {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  color: #ef4444;
}
```

- [ ] **Step 2: 添加剧集选择器样式**

```css
/* 剧集选择器 */
.episode-selector {
  margin-top: 20px;
}
.season-select {
  width: 100%;
  max-width: 200px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  margin-bottom: 12px;
  cursor: pointer;
}
.season-select option {
  background: #1a1a2e;
  color: #fff;
}
.episode-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}
.episode-btn {
  padding: 8px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #ccc;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.episode-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}
.episode-btn.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-color: transparent;
  color: #fff;
}
```

- [ ] **Step 3: 添加其他样式**

```css
/* 返回按钮 */
.back-button {
  position: fixed;
  top: 24px;
  left: 24px;
  z-index: 100;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(10px);
}
.back-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 加载/错误状态 */
.loading-state,
.error-state {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #888;
}
.error-state button {
  padding: 10px 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/VideoDetail.vue
git commit -m "feat(video-detail): 完成操作按钮和剧集选择器样式
- 添加播放、收藏、分享按钮
- 添加剧集季度/集数选择器UI"
```

---

## 任务 7: 最终调整和测试

- [ ] **Step 1: 安装依赖并启动开发服务器验证**

```bash
cd frontend && npm run dev
```

- [ ] **Step 2: 测试各页面加载**

访问 http://localhost:5173/video/movie/603（电影示例）
访问 http://localhost:5173/video/tv/1399（剧集示例）

- [ ] **Step 3: 提交最终版本**

```bash
git add -A
git commit -m "feat(video-detail): 完成详情页全新设计
- 全屏海报背景 + 左侧信息面板布局
- 类型标签、简介展开收起
- 操作按钮：播放/收藏/分享
- 剧集选择器（季度+集数）
- 演职人员横向滚动展示
- 响应式设计支持

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-14-video-detail-implementation.md`. Ready to execute?**