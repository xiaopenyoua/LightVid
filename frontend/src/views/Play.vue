<template>
  <div class="play-page">
    <!-- 左侧播放器 -->
    <div class="player-section">
      <!-- 背景 -->
      <div class="player-bg">
        <img v-if="video?.backdrop_url" :src="video.backdrop_url" class="bg-image" />
        <div class="bg-overlay"></div>
      </div>

      <!-- 返回按钮 -->
      <button class="back-btn" @click="$router.back()">←</button>
      <span class="header-title">{{ video?.title || '加载中...' }}</span>

      <!-- 播放器主体 -->
      <div class="player-main">
        <!-- HLS/m3u8 视频播放 -->
        <video
          v-if="m3u8Url"
          class="player-video"
          controls
          autoplay
        ></video>

        <!-- 加载状态 -->
        <div v-else-if="loading" class="player-loading">
          <LoadingSpinner :size="60" />
          <p>{{ loadingText }}</p>
        </div>

        <!-- 默认占位 -->
        <div v-else class="player-placeholder">
          <div class="placeholder-content">
            <span class="placeholder-icon">▶</span>
            <p>正在准备播放...</p>
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
      </div>

      <!-- 播放源选择 -->
      <div class="sources-section">
        <h3 class="section-title">视频源</h3>
        <div class="source-grid">
          <button
            v-for="source in videoSources"
            :key="source.value"
            class="source-btn"
            :class="{ active: selectedSource === source.value }"
            @click="selectedSource = source.value"
          >
            {{ source.label }}
          </button>
        </div>
      </div>

      <!-- 视频解析服务 -->
      <div class="parser-section">
        <h3 class="section-title">视频解析服务</h3>
        <select v-model="selectedParser" class="parser-select">
          <option v-for="parser in parserServices" :key="parser.value" :value="parser.value">
            {{ parser.label }}
          </option>
        </select>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideoDetail, getSeasonDetail } from '../api'
import { searchVideoLink, resolveVideo, getParsers } from '../api/search'
import Hls from 'hls.js'
import LoadingSpinner from '../components/LoadingSpinner.vue'

// 视频源列表
const videoSources = [
  { value: 'tencent', label: '腾讯视频' },
  { value: 'iqiyi', label: '爱奇艺' },
  { value: 'youku', label: '优酷' },
  { value: 'bilibili', label: '哔哩哔哩' },
  { value: 'mgtv', label: '芒果TV' }
]

const route = useRoute()
const video = ref(null)
const loading = ref(false)
const loadingText = ref('加载中...')

// 播放状态
const m3u8Url = ref('')
const hlsInstance = ref(null)

// 选择的配置
const selectedSource = ref('tencent')
const selectedParser = ref('')
const parserServices = ref([])

// 剧集
const currentSeason = ref(1)
const currentEpisode = ref(1)

const mediaType = () => route.params.media_type || 'movie'
const tmdbId = () => parseInt(route.params.id)

const currentEpisodes = computed(() => {
  return video.value?.seasonDetails?.episodes || []
})

const formatRuntime = (minutes) => {
  if (!minutes) return ''
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h ? `${h}h ${m}m` : `${m}m`
}

const loadData = async () => {
  loading.value = true
  loadingText.value = '加载视频信息...'
  try {
    // 并行加载视频详情和解析服务列表
    const [detailRes, parsersRes] = await Promise.all([
      getVideoDetail(mediaType(), tmdbId()),
      getParsers()
    ])

    video.value = detailRes.data

    // 处理解析服务列表
    if (parsersRes.data && parsersRes.data.length > 0) {
      parserServices.value = parsersRes.data.map(p => ({
        value: p.url,
        label: p.name
      }))
      // 默认选择第一个解析服务
      selectedParser.value = parserServices.value[0].value
    }

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
      // 保持当前选中的集数，如果不存在则选择第一集
      const exists = data.episodes.some(e => e.episode_number === currentEpisode.value)
      if (!exists) {
        currentEpisode.value = data.episodes[0].episode_number
      }
    }
  } catch {}
}

const selectSeason = (season) => {
  currentSeason.value = season
  loadSeasonDetail(season)
  // 切换季时重置到第一集
  if (video.value?.seasonDetails?.episodes?.length) {
    currentEpisode.value = video.value.seasonDetails.episodes[0].episode_number
  }
}

const selectEpisode = (episode) => {
  currentEpisode.value = episode
}

// 核心播放逻辑
const handlePlay = async () => {
  if (!video.value) {
    ElMessage.warning('请先选择要播放的影片')
    return
  }

  loading.value = true
  loadingText.value = '正在搜索播放链接...'

  try {
    // 1. 搜索视频播放链接
    const isTv = mediaType() === 'tv'
    const searchRes = await searchVideoLink({
      tmdb_id: video.value.tmdb_id || parseInt(route.params.id),
      media_type: mediaType(),
      platform: selectedSource.value,
      title: video.value.title,
      year: video.value.release_date ? parseInt(video.value.release_date.slice(0, 4)) : null,
      season: isTv ? currentSeason.value : null,
      episode: isTv ? currentEpisode.value : null
    })

    const platformUrl = searchRes.data.platform_url
    loadingText.value = '正在解析视频...'

    // 2. 解析为 m3u8 或直接播放 URL
    const resolveRes = await resolveVideo({
      platform_url: platformUrl,
      parser_url: selectedParser.value
    })

    const url = resolveRes.data.m3u8_url
    const parser = resolveRes.data.parser
    console.log('[播放] 返回的 URL:', url, '解析服务:', parser)

    // 3. 根据 URL 类型选择播放方式
    if (url.includes('.m3u8')) {
      // m3u8 URL 使用 HLS.js 播放
      m3u8Url.value = url
      await nextTick()
      playM3u8(url)
      ElMessage.success(`使用 ${parser} 播放`)
    } else if (url.includes('.mp4')) {
      // mp4 URL 直接用 video 标签播放
      m3u8Url.value = url
      await nextTick()
      playMp4(url)
      ElMessage.success(`使用 ${parser} 播放`)
    } else {
      ElMessage.error('无法解析视频地址，请尝试其他解析服务')
      m3u8Url.value = ''
    }
  } catch (err) {
    const msg = err.response?.data?.detail || '播放失败，请尝试其他解析服务'
    ElMessage.error(msg)
    m3u8Url.value = ''
  } finally {
    loading.value = false
  }
}

const playM3u8 = (url) => {
  const videoEl = document.querySelector('.player-video')
  if (!videoEl) return

  // 清理旧实例
  if (hlsInstance.value) {
    hlsInstance.value.destroy()
    hlsInstance.value = null
  }

  if (Hls.isSupported()) {
    const hls = new Hls({
      enableWorker: true,
      lowLatencyMode: false,
    })
    hls.loadSource(url)
    hls.attachMedia(videoEl)
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      videoEl.play().catch(e => console.warn('自动播放失败:', e))
    })
    hls.on(Hls.Events.ERROR, (event, data) => {
      if (data.fatal) {
        console.error('HLS 错误:', data)
        ElMessage.error('视频播放出错')
      }
    })
    hlsInstance.value = hls
  } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
    // Safari 原生支持 HLS
    videoEl.src = url
    videoEl.play().catch(e => console.warn('自动播放失败:', e))
  } else {
    ElMessage.error('您的浏览器不支持 HLS 播放')
  }
}

const playMp4 = (url) => {
  const videoEl = document.querySelector('.player-video')
  if (!videoEl) return

  videoEl.src = url
  videoEl.play().catch(e => console.warn('自动播放失败:', e))
}

const cleanup = () => {
  if (hlsInstance.value) {
    hlsInstance.value.destroy()
    hlsInstance.value = null
  }
}

// 用于检测是否首次加载
const isInitialized = ref(false)

// 监听视频源变化 - 自动播放
watch(selectedSource, (newSource, oldSource) => {
  if (isInitialized.value && oldSource !== undefined) {
    handlePlay()
  }
})

// 监听解析服务变化 - 自动播放
watch(selectedParser, (newParser, oldParser) => {
  if (isInitialized.value && oldParser !== undefined) {
    handlePlay()
  }
})

// 监听剧集变化 - 自动播放
watch(currentEpisode, (newEpisode, oldEpisode) => {
  if (isInitialized.value && oldEpisode !== undefined) {
    handlePlay()
  }
})

onUnmounted(cleanup)

watch(() => route.params.id, (newId, oldId) => {
  if (newId !== oldId) {
    cleanup()
    loadData()
  }
})

onMounted(async () => {
  await loadData()
  // 数据加载完成后，标记为已初始化并触发首次播放
  isInitialized.value = true
  // 延迟一点触发首次播放，确保 UI 已渲染
  setTimeout(() => {
    handlePlay()
  }, 500)
})
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

/* 返回按钮 */
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

.header-title {
  position: fixed;
  top: 24px;
  left: 80px;
  z-index: 100;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}

.player-main {
  flex: 1;
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.player-video {
  width: 100%;
  height: 100%;
  background: #000;
}
.player-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #888;
}
.player-loading p {
  font-size: 14px;
}
.player-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #0d0d1a 100%);
}
.placeholder-content {
  text-align: center;
  color: #666;
}
.placeholder-icon {
  font-size: 80px;
  opacity: 0.2;
  display: block;
  margin-bottom: 16px;
}
.placeholder-content p {
  font-size: 14px;
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
}
.info-meta .rating {
  color: #f5a623;
}

.sources-section,
.parser-section,
.episodes-section {
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

/* 视频源网格 */
.source-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}
.source-btn {
  padding: 12px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  color: #ccc;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.source-btn:hover {
  background: rgba(255,255,255,0.1);
}
.source-btn.active {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.4);
  color: #fff;
}

/* 解析服务选择 */
.parser-select {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}
.parser-select option {
  background: #1a1a2e;
  color: #fff;
}

/* 播放状态 */
.play-status {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 12px 24px;
}
.status-tag {
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 20px;
  font-size: 12px;
  color: #a5b4fc;
}

/* 剧集选择 */
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