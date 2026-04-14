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
          <div class="episode-grid" v-if="currentEpisodes.length">
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

<script setup>
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
      await loadSeasonDetail(currentSeason.value)
    }
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
</script>

<style scoped>
.video-detail {
  position: relative;
  min-height: 100vh;
  background: #0d0d1a;
}

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
  filter: blur(1px);
  opacity: 0;
  transition: opacity 0.5s;
}
.backdrop-image.loaded {
  opacity: 0.95;
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

/* 返回按钮 */
.back-button {
  position: fixed;
  top: 80px;
  left: 48px;
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
.rating {
  color: #f5a623;
}
.rating .star {
  margin-right: 4px;
}

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
  z-index: 10;
}
.error-state button {
  padding: 10px 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
}

/* 响应式 */
@media (max-width: 768px) {
  .main-content {
    padding: 100px 20px 120px;
    justify-content: flex-end;
  }
  .info-panel {
    width: 100%;
  }
  .title {
    font-size: 28px;
  }
}
</style>