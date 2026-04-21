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
      <div class="player-main" @mousemove="resetControlsTimeout" @mouseleave="startControlsHideTimer">
        <!-- HLS/m3u8 视频播放 -->
        <video
          v-if="m3u8Url"
          ref="videoRef"
          class="player-video"
          autoplay
          @timeupdate="handleTimeUpdate"
          @durationchange="handleDurationChange"
          @progress="handleProgress"
          @play="videoPaused = false"
          @pause="videoPaused = true"
          @ended="handleVideoEnded"
          @click="togglePlay"
        ></video>

        <!-- 自定义控制栏 -->
        <div v-if="m3u8Url" class="custom-controls" :class="{ 'controls-hidden': !showControls }" @mousemove="resetControlsTimeout" @mouseleave="startControlsHideTimer" @click="resetControlsTimeout">
          <!-- 进度条 -->
          <div class="progress-container" @click.stop="handleProgressClick">
            <div class="progress-bar">
              <div class="progress-buffered" :style="{ width: bufferedPercent + '%' }"></div>
              <div class="progress-played" :style="{ width: playedPercent + '%' }"></div>
            </div>
          </div>

          <!-- 控制按钮行 -->
          <div class="controls-row">
            <!-- 播放/暂停 -->
            <button class="control-btn" @click.stop="togglePlay" :title="videoPaused ? '播放 (K)' : '暂停 (K)'">
              <svg v-if="videoPaused" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
              <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
            </button>

            <!-- 时间显示 -->
            <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>

            <div class="controls-spacer"></div>

            <!-- 音量控制 -->
            <div class="volume-control">
              <button class="control-btn" @click.stop="toggleMute" title="静音 (M)">
                <svg v-if="volume > 0" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>
              </button>
              <input type="range" class="volume-slider" min="0" max="1" step="0.05" :value="volume" @input="handleVolumeChange" />
            </div>

            <!-- 播放速度 -->
            <div class="speed-control">
              <button class="control-btn speed-btn" @click.stop="showSpeedMenu = !showSpeedMenu" title="播放速度">{{ playbackSpeed }}x</button>
              <div v-if="showSpeedMenu" class="speed-menu" @click.stop>
                <button v-for="speed in [0.75, 1, 1.25, 1.5, 2]" :key="speed" :class="{ active: playbackSpeed === speed }" @click="setPlaybackSpeed(speed)">{{ speed }}x</button>
              </div>
            </div>

            <!-- 清晰度 -->
            <div class="quality-control" v-if="availableLevels.length > 1">
              <button class="control-btn quality-btn" @click.stop="showQualityMenu = !showQualityMenu" title="清晰度">
                {{ currentLevel === -1 ? '自动' : (availableLevels.find(l => l.index === currentLevel)?.label || '自动') }}
              </button>
              <div v-if="showQualityMenu" class="quality-menu" @click.stop>
                <button :class="{ active: currentLevel === -1 }" @click="setQuality(-1)">自动</button>
                <button v-for="level in availableLevels" :key="level.index" :class="{ active: currentLevel === level.index }" @click="setQuality(level.index)">{{ level.label }}</button>
              </div>
            </div>

            <!-- 设置 -->
            <div class="settings-control">
              <button class="control-btn" @click.stop="showSettingsMenu = !showSettingsMenu" title="设置">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
              </button>
              <div v-if="showSettingsMenu" class="settings-menu" @click.stop>
                <label class="settings-item">
                  <span>自动连播</span>
                  <input type="checkbox" :checked="autoPlayNext" @change="toggleAutoPlayNext" />
                </label>
                <label class="settings-item">
                  <span>单集循环</span>
                  <input type="checkbox" :checked="loopSingle" @change="toggleLoopSingle" />
                </label>
              </div>
            </div>

            <!-- 画中画 -->
            <button class="control-btn" @click.stop="togglePiP" title="画中画 (P)">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 7h-8v6h8V7zm2-4H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H3V5h18v14z"/></svg>
            </button>

            <!-- 全屏 -->
            <button class="control-btn" @click.stop="toggleFullscreen" title="全屏 (F)">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
            </button>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-else-if="loading" class="player-loading">
          <div class="loading-animation">
            <div class="loading-bar">
              <div class="loading-bar-fill"></div>
            </div>
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
          <p class="loading-text">{{ loadingText }}</p>
        </div>

        <!-- 默认占位 -->
        <div v-else class="player-placeholder">
          <div class="placeholder-content">
            <div class="placeholder-icon">
              <div class="play-btn">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
            </div>
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
import { searchVideoLink, resolveVideo, getParsers, continuePrecache } from '../api/search'
import { getProgress, saveProgress } from '../api/progress'
import Hls from 'hls.js'

// 视频源列表
// 用于取消正在进行的请求
let searchController = null
let resolveController = null
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

// 剧集 - 从 URL query 参数初始化，支持直接通过链接进入指定剧集
const currentSeason = ref(route.query.season ? parseInt(route.query.season) : 1)
const currentEpisode = ref(route.query.episode ? parseInt(route.query.episode) : 1)

// 播放进度相关
const savedProgress = ref(null)  // 从数据库加载的进度
const playbackSpeed = ref(parseFloat(localStorage.getItem('playback_speed')) || 1)

// 自定义控制栏相关
const showControls = ref(true)
const controlsTimeout = ref(null)
const isBuffering = ref(false)

// 播放状态
const videoPaused = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const bufferedPercent = ref(0)
const volume = ref(1)

// 速度菜单
const showSpeedMenu = ref(false)

// 清晰度相关
const availableLevels = ref([]) // 可用清晰度列表
const currentLevel = ref(-1) // -1 表示自动
const showQualityMenu = ref(false)

// 设置菜单
const showSettingsMenu = ref(false)
const autoPlayNext = ref(localStorage.getItem('auto_play_next') === 'true') // 自动连播
const loopSingle = ref(localStorage.getItem('loop_single') === 'true') // 单集循环

// 进度保存定时器
let progressSaveTimer = null

// 视频元素引用
const videoRef = ref(null)

// 播放进度百分比
const playedPercent = computed(() => {
  return duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
})

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

// ==================== 自定义控制栏函数 ====================

// 播放/暂停
const togglePlay = () => {
  const videoEl = videoRef.value
  if (!videoEl) return
  if (videoEl.paused) {
    videoEl.play()
  } else {
    videoEl.pause()
  }
}

// 视频事件处理
const handleTimeUpdate = () => {
  const videoEl = videoRef.value
  if (!videoEl) return
  currentTime.value = videoEl.currentTime
}

const handleDurationChange = () => {
  const videoEl = videoRef.value
  if (!videoEl) return
  duration.value = videoEl.duration
}

const handleProgress = () => {
  const videoEl = videoRef.value
  if (!videoEl || !videoEl.buffered.length) return
  bufferedPercent.value = (videoEl.buffered.end(videoEl.buffered.length - 1) / videoEl.duration) * 100
}

// 音量控制
const toggleMute = () => {
  const videoEl = videoRef.value
  if (!videoEl) return
  if (videoEl.volume > 0) {
    videoEl._previousVolume = videoEl.volume
    videoEl.volume = 0
    volume.value = 0
  } else {
    videoEl.volume = videoEl._previousVolume || 1
    volume.value = videoEl.volume
  }
}

const handleVolumeChange = (e) => {
  const videoEl = videoRef.value
  if (!videoEl) return
  videoEl.volume = parseFloat(e.target.value)
  volume.value = videoEl.volume
}

// 播放速度
const setPlaybackSpeed = (speed) => {
  const videoEl = videoRef.value
  if (!videoEl) return
  videoEl.playbackRate = speed
  playbackSpeed.value = speed
  localStorage.setItem('playback_speed', speed)
  showSpeedMenu.value = false
}

// 清晰度切换
const getQualityLabel = (level, height, bitrate) => {
  if (level === -1) return '自动'
  // 优先使用 height
  if (height && height > 0) return `${height}p`
  // 没有 height 时用 bitrate 估算（假设 1Mbps ≈ 720p）
  if (bitrate && bitrate > 0) {
    const estimatedHeight = Math.round(Math.sqrt(bitrate / 1000) * 720)
    if (estimatedHeight > 0) return `${estimatedHeight}p`
    return `${Math.round(bitrate / 1000)}k`
  }
  return `${level}`
}

const setQuality = (level) => {
  if (hlsInstance.value) {
    hlsInstance.value.currentLevel = level
    currentLevel.value = level
  }
  showQualityMenu.value = false
}

const updateAvailableLevels = () => {
  if (hlsInstance.value && hlsInstance.value.levels) {
    availableLevels.value = hlsInstance.value.levels.map((l, i) => ({
      index: i,
      height: l.height,
      bitrate: l.bitrate,
      label: getQualityLabel(i, l.height, l.bitrate)
    }))
    currentLevel.value = hlsInstance.value.currentLevel
  }
}

// 设置：自动连播
const toggleAutoPlayNext = () => {
  autoPlayNext.value = !autoPlayNext.value
  localStorage.setItem('auto_play_next', autoPlayNext.value)
}

// 设置：单集循环
const toggleLoopSingle = () => {
  loopSingle.value = !loopSingle.value
  localStorage.setItem('loop_single', loopSingle.value)
}

// 进度条点击
const handleProgressClick = (e) => {
  const videoEl = videoRef.value
  if (!videoEl) return
  const rect = e.currentTarget.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  videoEl.currentTime = percent * videoEl.duration
}

// 格式化时间
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 画中画
const togglePiP = async () => {
  const videoEl = videoRef.value
  if (!videoEl) return
  try {
    if (document.pictureInPictureElement) {
      await document.exitPictureInPicture()
    } else {
      await videoEl.requestPictureInPicture()
    }
  } catch (err) {
    console.warn('PiP error:', err)
  }
}

// 全屏
const toggleFullscreen = async () => {
  const playerEl = document.querySelector('.player-section')
  if (!playerEl) return
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else {
      await playerEl.requestFullscreen()
    }
  } catch (err) {
    console.warn('Fullscreen error:', err)
  }
}

// 控制栏显示/隐藏
const resetControlsTimeout = () => {
  showControls.value = true
  if (controlsTimeout.value) {
    clearTimeout(controlsTimeout.value)
  }
  startControlsHideTimer()
}

const startControlsHideTimer = () => {
  if (controlsTimeout.value) {
    clearTimeout(controlsTimeout.value)
  }
  controlsTimeout.value = setTimeout(() => {
    if (!videoPaused.value) {
      showControls.value = false
    }
  }, 350)
}

// ==================== 加载数据 ====================

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
      // 只有当 URL 没有指定 season 参数时才使用默认的第一季
      const seasonFromQuery = route.query.season ? parseInt(route.query.season) : null
      if (seasonFromQuery && video.value.seasons.some(s => s.season_number === seasonFromQuery)) {
        currentSeason.value = seasonFromQuery
      } else {
        currentSeason.value = video.value.seasons[0].season_number
      }
      await loadSeasonDetail(currentSeason.value)

      // 构建每季集数字典
      const seasonsEpisodesData = {}
      for (const s of video.value.seasons) {
        if (s.season_number && s.episode_count) {
          seasonsEpisodesData[s.season_number] = s.episode_count
        }
      }

      // 继续预缓存未完成的集数（如果之前有中断）
      continuePrecache({
        tmdb_id: tmdbId(),
        platform: selectedSource.value,
        title: video.value.title,
        year: video.value.release_date ? parseInt(video.value.release_date.slice(0, 4)) : null,
        current_season: currentSeason.value,
        current_episode: currentEpisode.value,
        seasons_episodes: seasonsEpisodesData
      }).catch(e => console.warn('[预缓存] 继续预缓存失败:', e))
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

  // 1. 取消之前的请求
  if (searchController) {
    searchController.abort()
    searchController = null
  }
  if (resolveController) {
    resolveController.abort()
    resolveController = null
  }

  // 2. 显示 loading（但不停止当前播放，保持画面）
  loading.value = true
  loadingText.value = '正在搜索播放链接...'

  // 保存当前选中的集数，用于判断请求返回时是否已切换
  const playingEpisode = currentEpisode.value
  const playingSeason = currentSeason.value

  try {
    // 创建新的 AbortController
    searchController = new AbortController()

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
    }, searchController.signal)

    // 检查是否已切换到其他集数
    if (playingEpisode !== currentEpisode.value || playingSeason !== currentSeason.value) {
      console.log('[播放] 集数已切换，忽略此次响应')
      return
    }

    const platformUrl = searchRes.data.platform_url

    // 2. 使用用户选择的解析服务
    loadingText.value = `正在解析视频...`
    resolveController = new AbortController()

    const resolveRes = await resolveVideo({
      platform_url: platformUrl,
      parser_url: selectedParser.value
    }, resolveController.signal)

    // 再次检查集数是否已切换
    if (playingEpisode !== currentEpisode.value || playingSeason !== currentSeason.value) {
      console.log('[播放] 集数已切换，忽略')
      return
    }

    const url = resolveRes.data.m3u8_url
    if (url.includes('.m3u8')) {
      m3u8Url.value = url
      await nextTick()
      playM3u8(url)
    } else if (url.includes('.mp4')) {
      m3u8Url.value = url
      await nextTick()
      playMp4(url)
    } else {
      throw new Error('无法解析视频地址')
    }

  } catch (err) {
    // 如果是取消的请求，不显示错误
    if (err.name === 'AbortError' || err.name === 'CanceledError') {
      console.log('[播放] 请求已取消')
      return
    }
    const msg = err.response?.data?.detail || '播放失败，请尝试其他解析服务'
    ElMessage.error(msg)
    stopCurrentPlayback()
  } finally {
    loading.value = false
  }
}

// 停止当前播放
const stopCurrentPlayback = () => {
  // 清理 HLS 实例
  if (hlsInstance.value) {
    hlsInstance.value.destroy()
    hlsInstance.value = null
  }
  // 清除视频 URL（也会停止播放）
  m3u8Url.value = ''
}

const playM3u8 = (url) => {
  const videoEl = videoRef.value
  if (!videoEl) return

  // 清理旧实例
  if (hlsInstance.value) {
    hlsInstance.value.destroy()
    hlsInstance.value = null
  }

  // 设置播放速度
  videoEl.playbackRate = playbackSpeed.value

  if (Hls.isSupported()) {
    const hls = new Hls({
      enableWorker: true,
      lowLatencyMode: false,
    })
    hls.loadSource(url)
    hls.attachMedia(videoEl)
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      // 更新可用清晰度列表
      updateAvailableLevels()
      // 恢复播放进度
      if (savedProgress.value && savedProgress.value.current_time > 0) {
        const restoreProgress = () => {
          if (videoEl.duration > savedProgress.value.current_time) {
            videoEl.currentTime = savedProgress.value.current_time
          }
        }
        if (videoEl.readyState >= 2) {
          restoreProgress()
        } else {
          videoEl.addEventListener('loadedmetadata', restoreProgress, { once: true })
        }
      }
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
    // 恢复播放进度
    if (savedProgress.value && savedProgress.value.current_time > 0) {
      const restoreProgress = () => {
        if (videoEl.duration > savedProgress.value.current_time) {
          videoEl.currentTime = savedProgress.value.current_time
        }
      }
      if (videoEl.readyState >= 2) {
        restoreProgress()
      } else {
        videoEl.addEventListener('loadedmetadata', restoreProgress, { once: true })
      }
    }
    videoEl.play().catch(e => console.warn('自动播放失败:', e))
  } else {
    ElMessage.error('您的浏览器不支持 HLS 播放')
  }
}

const playMp4 = (url) => {
  const videoEl = videoRef.value
  if (!videoEl) return

  // 设置播放速度
  videoEl.playbackRate = playbackSpeed.value

  videoEl.src = url

  // 恢复播放进度
  if (savedProgress.value && savedProgress.value.current_time > 0) {
    const restoreProgress = () => {
      if (videoEl.duration > savedProgress.value.current_time) {
        videoEl.currentTime = savedProgress.value.current_time
      }
    }
    if (videoEl.readyState >= 2) {
      restoreProgress()
    } else {
      videoEl.addEventListener('loadedmetadata', restoreProgress, { once: true })
    }
  }

  videoEl.play().catch(e => console.warn('自动播放失败:', e))
}

const cleanup = () => {
  // 取消所有正在进行的请求
  if (searchController) {
    searchController.abort()
    searchController = null
  }
  if (resolveController) {
    resolveController.abort()
    resolveController = null
  }
  // 停止播放
  stopCurrentPlayback()
}

// 用于检测是否首次加载
const isInitialized = ref(false)

// 进度保存函数
const saveCurrentProgress = () => {
  const isTv = mediaType() === 'tv'
  if (currentTime.value > 0 && duration.value > 0) {
    saveProgress(
      tmdbId(),
      isTv ? currentSeason.value : null,
      isTv ? currentEpisode.value : null,
      currentTime.value,
      duration.value
    ).catch(e => console.warn('[进度] 保存失败:', e))
  }
}

// 键盘快捷键
const handleKeydown = (e) => {
  // 如果用户在输入框中，不触发快捷键
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

  const videoEl = videoRef.value
  if (!videoEl) return

  switch (e.key) {
    case ' ':
    case 'k':
      e.preventDefault()
      togglePlay()
      break
    case 'ArrowLeft':
      e.preventDefault()
      videoEl.currentTime = Math.max(0, videoEl.currentTime - 10)
      break
    case 'ArrowRight':
      e.preventDefault()
      videoEl.currentTime = Math.min(videoEl.duration, videoEl.currentTime + 10)
      break
    case 'ArrowUp':
      e.preventDefault()
      videoEl.volume = Math.min(1, videoEl.volume + 0.1)
      volume.value = videoEl.volume
      break
    case 'ArrowDown':
      e.preventDefault()
      videoEl.volume = Math.max(0, videoEl.volume - 0.1)
      volume.value = videoEl.volume
      break
    case 'm':
      toggleMute()
      break
    case 'f':
      toggleFullscreen()
      break
    case 'p':
      togglePiP()
      break
  }
}

// 页面关闭前保存进度
const handleBeforeUnload = () => {
  saveCurrentProgress()
}

// 视频播放结束处理
const handleVideoEnded = () => {
  const videoEl = videoRef.value
  if (!videoEl) return

  // 单集循环
  if (loopSingle.value) {
    videoEl.currentTime = 0
    videoEl.play()
    return
  }

  // 自动连播下一集（仅剧集）
  if (autoPlayNext.value && mediaType() === 'tv') {
    const episodes = currentEpisodes.value
    if (episodes.length > 0) {
      const currentEp = episodes.findIndex(e => e.episode_number === currentEpisode.value)
      if (currentEp >= 0 && currentEp < episodes.length - 1) {
        // 播放下一集
        selectEpisode(episodes[currentEp + 1].episode_number)
      }
    }
  }
}

// 监听视频源变化 - 自动播放

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

onUnmounted(() => {
  // 保存进度
  saveCurrentProgress()
  // 停止定时器
  if (progressSaveTimer) {
    clearInterval(progressSaveTimer)
    progressSaveTimer = null
  }
  // 移除事件监听
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  // 执行清理
  cleanup()
})

watch(() => route.params.id, (newId, oldId) => {
  if (newId !== oldId) {
    cleanup()
    loadData()
  }
})

onMounted(async () => {
  // 先加载播放进度
  try {
    const isTv = mediaType() === 'tv'
    const res = await getProgress(
      tmdbId(),
      isTv ? currentSeason.value : null,
      isTv ? currentEpisode.value : null
    )
    if (res.data) {
      savedProgress.value = res.data
    }
  } catch (e) {
    console.warn('[进度] 加载失败:', e)
  }

  await loadData()

  // 数据加载完成后，标记为已初始化并触发首次播放
  isInitialized.value = true

  // 启动进度保存定时器
  if (progressSaveTimer) clearInterval(progressSaveTimer)
  progressSaveTimer = setInterval(saveCurrentProgress, 15000) // 每 15 秒保存一次

  // 添加键盘监听
  window.addEventListener('keydown', handleKeydown)
  // 添加页面关闭事件
  window.addEventListener('beforeunload', handleBeforeUnload)

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
  min-height: 0;
}
.player-video {
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
  aspect-ratio: 16 / 9;
  object-fit: contain;
  background: #000;
}

/* 自定义控制栏 */
.custom-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  padding: 20px 16px 12px;
  transition: opacity 0.3s;
  z-index: 10;
}

.custom-controls.controls-hidden {
  opacity: 0;
}

.progress-container {
  cursor: pointer;
  padding: 16px 0;
  margin-top: -8px;
}

.progress-bar {
  height: 6px;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
  position: relative;
  overflow: hidden;
}

.progress-buffered {
  position: absolute;
  height: 100%;
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
  transition: width 0.3s;
}

.progress-played {
  position: absolute;
  height: 100%;
  background: #6366f1;
  border-radius: 2px;
  transition: width 0.1s;
}

.controls-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
}

.control-btn {
  background: none;
  border: none;
  color: #fff;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn:hover {
  background: rgba(255,255,255,0.1);
}

.control-btn svg {
  width: 22px;
  height: 22px;
}

.time-display {
  font-size: 12px;
  color: #ccc;
  min-width: 90px;
  margin-left: 4px;
}

.controls-spacer {
  flex: 1;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 4px;
}

.volume-slider {
  width: 70px;
  height: 4px;
  -webkit-appearance: none;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: #fff;
  border-radius: 50%;
  cursor: pointer;
}

.speed-control {
  position: relative;
}

.speed-btn {
  font-size: 12px;
  min-width: 40px;
}

.speed-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  background: rgba(20, 20, 30, 0.95);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 8px 0;
  margin-bottom: 8px;
  min-width: 80px;
}

.speed-menu button {
  display: block;
  width: 100%;
  padding: 8px 16px;
  text-align: center;
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  font-size: 13px;
}

.speed-menu button:hover,
.speed-menu button.active {
  background: rgba(99, 102, 241, 0.2);
  color: #fff;
}

/* 清晰度菜单 */
.quality-control,
.settings-control {
  position: relative;
}

.quality-btn {
  font-size: 12px;
  min-width: 40px;
}

.quality-menu,
.settings-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  background: rgba(20, 20, 30, 0.95);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 8px 0;
  margin-bottom: 8px;
  min-width: 100px;
}

.quality-menu button,
.settings-menu button {
  display: block;
  width: 100%;
  padding: 8px 16px;
  text-align: center;
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  font-size: 13px;
}

.quality-menu button:hover,
.quality-menu button.active,
.settings-menu button:hover,
.settings-menu button.active {
  background: rgba(99, 102, 241, 0.2);
  color: #fff;
}

/* 设置菜单 */
.settings-menu {
  min-width: 140px;
}

.settings-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
  color: #ccc;
}

.settings-item:hover {
  background: rgba(99, 102, 241, 0.2);
  color: #fff;
}

.settings-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #6366f1;
}

.player-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  color: #888;
}

/* 加载动画 - 进度条 + 跳动圆点 */
.loading-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.loading-bar {
  width: 200px;
  height: 3px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
  overflow: hidden;
}

.loading-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
  background-size: 200% 100%;
  border-radius: 2px;
  animation: loading-gradient 1.5s ease-in-out infinite;
}

.loading-dots {
  display: flex;
  gap: 8px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #6366f1;
  border-radius: 50%;
  animation: loading-dot 1.4s ease-in-out infinite;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
  background: #8b5cf6;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
  background: #a855f7;
}

.loading-text {
  font-size: 14px;
  color: #666;
  animation: text-pulse 2s ease-in-out infinite;
}

@keyframes loading-gradient {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@keyframes loading-dot {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes text-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
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
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}

.play-btn {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(168, 85, 247, 0.3));
  border: 2px solid rgba(99, 102, 241, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: play-pulse 2s ease-in-out infinite;
}

.play-btn svg {
  width: 36px;
  height: 36px;
  color: rgba(255, 255, 255, 0.9);
  margin-left: 4px;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes play-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4),
                0 0 20px rgba(99, 102, 241, 0.2);
  }
  50% {
    box-shadow: 0 0 0 15px rgba(99, 102, 241, 0),
                0 0 30px rgba(99, 102, 241, 0.3);
  }
}

.placeholder-content p {
  font-size: 14px;
  color: #555;
  animation: text-fade 2s ease-in-out infinite;
}

@keyframes text-fade {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.8; }
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