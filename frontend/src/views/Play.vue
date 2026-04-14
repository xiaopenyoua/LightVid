<template>
  <div class="play-page">
    <!-- 左侧播放器 -->
    <div class="player-section">
      <!-- 背景 -->
      <div class="player-bg">
        <img v-if="video?.backdrop_url" :src="video.backdrop_url" class="bg-image" />
        <div class="bg-overlay"></div>
      </div>

      <!-- 播放器头部 -->
      <div class="player-header">
        <button class="back-btn" @click="$router.back()">←</button>
        <span class="video-title">{{ video?.title || '加载中...' }}</span>
      </div>

      <!-- 播放器主体 -->
      <div class="player-main" @mousemove="showControls" @mouseleave="hideControls">
        <iframe
          v-if="currentUrl"
          :src="currentUrl"
          class="player-iframe"
          frameborder="0"
          allowfullscreen
        ></iframe>
        <div v-else class="player-placeholder">
          <span class="placeholder-icon">▶</span>
        </div>

        <!-- 底部控制栏 -->
        <div class="player-controls" :class="{ visible: controlsVisible }">
          <div class="progress-bar" @click.stop="seekVideo">
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
          </div>
          <div class="controls-row">
            <div class="controls-left">
              <button class="ctrl-btn">◀◀</button>
              <button class="ctrl-btn play-btn">{{ isPlaying ? '⏸' : '▶' }}</button>
              <button class="ctrl-btn">▶▶</button>
              <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
            </div>
            <div class="controls-right">
              <button class="ctrl-btn">🔊</button>
              <button class="ctrl-btn">⛶</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧面板 -->
    <div class="right-panel">
      <!-- 视频信息 -->
      <div class="video-info" v-if="video">
        <h2 class="info-title">{{ video.title }}</h2>
        <div class="info-meta">
          <span class="rating" v-if="video.vote_average">⭐ {{ video.vote_average.toFixed(1) }}</span>
          <span v-if="video.release_date">{{ video.release_date.slice(0, 4) }}</span>
          <span v-if="video.runtime">{{ formatRuntime(video.runtime) }}</span>
        </div>
        <p class="info-overview" v-if="video.overview">{{ video.overview }}</p>
      </div>

      <!-- 播放源 -->
      <div class="sources-section">
        <h3 class="section-title">播放源</h3>
        <div class="source-list">
          <div
            v-for="source in sources"
            :key="source.id"
            class="source-item"
            :class="{ active: currentSource?.id === source.id }"
            @click="playSource(source)"
          >
            <div class="source-info">
              <span class="source-name">{{ source.name }}</span>
              <span class="source-speed" v-if="source.speed">{{ source.speed }}s</span>
              <span class="source-speed untested" v-else>未测速</span>
            </div>
            <span v-if="currentSource?.id === source.id" class="active-indicator">●</span>
          </div>
        </div>
      </div>

      <!-- 剧集选择 -->
      <div class="episodes-section" v-if="video?.seasons?.length">
        <h3 class="section-title">选集</h3>
        <div class="season-tabs">
          <button
            v-for="season in video.seasons"
            :key="season.season_number"
            class="season-tab"
            :class="{ active: currentSeason === season.season_number }"
            @click="selectSeason(season.season_number)"
          >
            {{ season.name }}
          </button>
        </div>
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

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <LoadingSpinner :size="50" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideoDetail, getSeasonDetail, getPlaySources, getParseConfigs, updateHistory } from '../api'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const route = useRoute()
const video = ref(null)
const sources = ref([])
const parseConfigs = ref([])
const currentSource = ref(null)
const currentUrl = ref('')
const loading = ref(false)
const controlsVisible = ref(true)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const progress = ref(0)
const currentSeason = ref(1)
const currentEpisode = ref(1)

let hideControlsTimer = null

const mediaType = () => route.params.media_type || 'movie'
const tmdbId = () => parseInt(route.params.id)

const currentEpisodes = computed(() => {
  return video.value?.seasonDetails?.episodes || []
})

const formatTime = (seconds) => {
  if (!seconds) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatRuntime = (minutes) => {
  if (!minutes) return ''
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h ? `${h}h ${m}m` : `${m}m`
}

const loadData = async () => {
  loading.value = true
  try {
    const [detailRes, sourcesRes, configsRes] = await Promise.all([
      getVideoDetail(mediaType(), tmdbId()),
      getPlaySources(),
      getParseConfigs()
    ])
    video.value = detailRes.data
    sources.value = sourcesRes.data
    parseConfigs.value = configsRes.data

    if (video.value?.seasons?.length) {
      currentSeason.value = video.value.seasons[0].season_number
      await loadSeasonDetail(currentSeason.value)
    }
  } catch {
    ElMessage.error('加载失败')
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

const playSource = (source) => {
  currentSource.value = source
  if (source.type === 'parse') {
    const config = parseConfigs.value.find(c => c.id === source.parse_config_id) || parseConfigs.value[0]
    if (config) {
      currentUrl.value = config.base_url + encodeURIComponent(source.url)
    }
  } else {
    currentUrl.value = source.url
  }
}

const selectSeason = (season) => {
  currentSeason.value = season
  loadSeasonDetail(season)
}

const selectEpisode = (episode) => {
  currentEpisode.value = episode
}

const showControls = () => {
  controlsVisible.value = true
  clearTimeout(hideControlsTimer)
  hideControlsTimer = setTimeout(() => {
    controlsVisible.value = false
  }, 3000)
}

const hideControls = () => {
  hideControlsTimer = setTimeout(() => {
    controlsVisible.value = false
  }, 1000)
}

const seekVideo = (e) => {
  const rect = e.currentTarget.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  progress.value = percent * 100
  currentTime.value = (percent * duration.value)
}

const saveProgress = async () => {
  if (video.value) {
    try {
      await updateHistory(video.value.tmdb_id, {
        progress: currentTime.value,
        duration: duration.value,
        source_id: currentSource.value?.id
      })
    } catch {}
  }
}

watch(() => route.params.id, loadData)

onMounted(loadData)
onUnmounted(saveProgress)
</script>

<style scoped>
.play-page {
  display: flex;
  height: 100vh;
  background: #0d0d1a;
  overflow: hidden;
}

/* 左侧播放器 */
.player-section {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  background: #000;
}

.player-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}
.bg-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(30px);
  opacity: 0.25;
}
.bg-overlay {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, transparent 30%, #000 100%);
}

.back-btn {
  position: fixed;
  top: 24px;
  left: 24px;
  z-index: 100;
  background: rgba(0,0,0,0.5);
  border: 1px solid rgba(255,255,255,0.2);
  color: #fff;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(10px);
}
.back-btn:hover {
  background: rgba(255,255,255,0.2);
}
.video-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.player-main {
  flex: 1;
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.player-iframe {
  width: 100%;
  height: 100%;
}
.player-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #0d0d1a 100%);
}
.placeholder-icon {
  font-size: 80px;
  opacity: 0.2;
}

.player-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s;
}
.player-controls.visible {
  opacity: 1;
}
.progress-bar {
  height: 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 12px;
}
.progress-track {
  width: 100%;
  height: 4px;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
}
.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ctrl-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  opacity: 0.8;
  transition: opacity 0.2s;
}
.ctrl-btn:hover {
  opacity: 1;
}
.play-btn {
  font-size: 24px;
}
.time-display {
  font-size: 12px;
  color: #ccc;
  margin-left: 8px;
}

/* 右侧面板 */
.right-panel {
  width: 360px;
  background: rgba(20, 20, 30, 0.95);
  border-left: 1px solid rgba(255,255,255,0.06);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.video-info {
  padding: 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.info-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
}
.info-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #888;
  margin-bottom: 12px;
}
.info-meta .rating {
  color: #f5a623;
}
.info-overview {
  font-size: 13px;
  line-height: 1.6;
  color: #999;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sources-section {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.section-title {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 16px;
}
.source-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.source-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.source-item:hover {
  background: rgba(255,255,255,0.1);
}
.source-item.active {
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.4);
}
.source-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.source-name {
  font-size: 14px;
  color: #fff;
}
.source-speed {
  font-size: 12px;
  color: #666;
}
.source-speed.untested {
  color: #888;
}
.active-indicator {
  color: #6366f1;
  font-size: 12px;
}

.episodes-section {
  padding: 20px 24px;
  flex: 1;
}
.season-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.season-tab {
  padding: 6px 12px;
  background: rgba(255,255,255,0.08);
  border: none;
  border-radius: 6px;
  color: #ccc;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.season-tab:hover {
  background: rgba(255,255,255,0.12);
}
.season-tab.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}
.episode-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.episode-btn {
  padding: 10px;
  background: rgba(255,255,255,0.06);
  border: none;
  border-radius: 6px;
  color: #ccc;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.episode-btn:hover {
  background: rgba(255,255,255,0.1);
}
.episode-btn.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.8);
}

/* 响应式 */
@media (max-width: 900px) {
  .play-page {
    flex-direction: column;
  }
  .player-section {
    height: 50vh;
  }
  .right-panel {
    width: 100%;
    height: 50vh;
  }
}
</style>