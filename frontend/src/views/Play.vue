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
        <video
          v-if="m3u8Url"
          class="player-video"
          controls
          autoplay
        ></video>
        <iframe
          v-else-if="currentUrl"
          :src="currentUrl"
          class="player-iframe"
          frameborder="0"
          allowfullscreen
        ></iframe>
        <div v-else class="player-placeholder">
          <div class="placeholder-content">
            <span class="placeholder-icon">▶</span>
            <p>请在右侧选择视频源并点击播放按钮</p>
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

      <!-- 播放按钮 -->
      <div class="play-section">
        <button class="play-btn-large" @click="handlePlay" :disabled="loading">
          {{ loading ? '解析中...' : '播放' }}
        </button>
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
import { getVideoDetail, getSeasonDetail } from '../api'
import { searchVideoLink, resolveVideo } from '../api/search'
import Hls from 'hls.js'
import LoadingSpinner from '../components/LoadingSpinner.vue'

// 默认视频解析服务列表
const DEFAULT_API_LIST = [
  { value: 'https://jx.xmflv.com/?url=', label: '虾米视频解析' },
  { value: 'https://jx.77flv.cc/?url=', label: '七七云解析' },
  { value: 'https://jx.playerjy.com/?url=', label: 'Player-JY' },
  { value: 'https://jiexi.789jiexi.icu:4433/?url=', label: '789解析' },
  { value: 'https://jx.2s0.cn/player/?url=', label: '极速解析' },
  { value: 'https://bd.jx.cn/?url=', label: '冰豆解析' },
  { value: 'https://jx.973973.xyz/?url=', label: '973解析' },
  { value: 'https://www.ckplayer.vip/jiexi/?url=', label: 'CK' },
  { value: 'https://jx.nnxv.cn/tv.php?url=', label: '七哥解析' },
  { value: 'https://www.yemu.xyz/?url=', label: '夜幕' },
  { value: 'https://www.pangujiexi.com/jiexi/?url=', label: '盘古' },
  { value: 'https://www.playm3u8.cn/jiexi.php?url=', label: 'playm3u8' },
  { value: 'https://video.isyour.love/player/getplayer?url=', label: '芒果TV1' },
  { value: 'https://im1907.top/?jx=', label: '芒果TV2' },
  { value: 'https://jx.hls.one/?url=', label: 'HLS解析' },
  { value: 'https://jx.jsonplayer.com/player/?url=', label: 'JSON解析' },
  { value: 'https://jx.dj6u.com/?url=', label: 'DJ6U解析' },
  { value: 'https://jx.rdhk.net/?v=', label: 'RDHK解析' },
  { value: 'https://api.okjx.cc:3389/jx.php?url=', label: 'OKJX解析1' },
  { value: 'https://okjx.cc/?url=', label: 'OKJX解析2' },
  { value: 'https://jx.aidouer.net/?url=', label: 'Aidouer解析' },
  { value: 'https://jx.iztyy.com/Bei/?url=', label: 'iztyy解析' },
  { value: 'https://jx.yparse.com/index.php?url=', label: 'yparse解析' },
  { value: 'https://www.mtosz.com/m3u8.php?url=', label: 'mtosz解析' },
  { value: 'https://jx.m3u8.tv/jiexi/?url=', label: 'm3u8tv解析' },
  { value: 'https://parse.123mingren.com/?url=', label: '123明人解析' },
  { value: 'https://jx.4kdv.com/?url=', label: '4K解析' },
  { value: 'https://ckmov.ccyjjd.com/ckmov/?url=', label: 'CK解析' },
  { value: 'https://www.8090g.cn/?url=', label: '8090G解析' },
  { value: 'https://api.qianqi.net/vip/?url=', label: '千奇解析' },
  { value: 'https://vip.laobandq.com/jiexi.php?url=', label: '老板解析' },
  { value: 'https://www.administratorw.com/video.php?url=', label: '管理员解析' },
  { value: 'https://go.yh0523.cn/y.cy?url=', label: '解析14' },
  { value: 'https://jx.blbo.cc:4433/?url=', label: '人迷解析' },
  { value: 'http://27.124.4.42:4567/jhjson/ceshi.php?url=', label: '第一解析' },
  { value: 'https://jx.zui.cm/?url=', label: '最先解析' },
  { value: 'https://za.kuanjv.com/?url=', label: '王牌解析' },
  { value: 'http://47.98.234.2:7768/api.php?url=', label: '293' },
  { value: 'https://play.fuqizhishi.com/maotv/API.php?appkey=xiongdimenbieguaiwodingbuzhulegailekey07201538&url=', label: '云you秒解' }
]

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
const currentUrl = ref('')
const selectedSource = ref('tencent')
const selectedParser = ref(DEFAULT_API_LIST[0].value)
const parserServices = ref(DEFAULT_API_LIST)
const m3u8Url = ref('')
const hlsInstance = ref(null)
const currentSeason = ref(1)
const currentEpisode = ref(1)

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

const getSourceName = (platform) => {
  const source = videoSources.find(s => s.value === platform)
  return source ? source.label : platform
}

const loadData = async () => {
  loading.value = true
  try {
    const detailRes = await getVideoDetail(mediaType(), tmdbId())
    video.value = detailRes.data

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

const selectSeason = (season) => {
  currentSeason.value = season
  loadSeasonDetail(season)
}

const selectEpisode = (episode) => {
  currentEpisode.value = episode
}

const handlePlay = async () => {
  if (!video.value) {
    ElMessage.warning('请先选择要播放的影片')
    return
  }

  loading.value = true
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

    // 2. 解析为 m3u8
    const resolveRes = await resolveVideo({
      platform_url: platformUrl
    })

    const m3u8 = resolveRes.data.m3u8_url

    // 3. 使用 HLS.js 播放
    playM3u8(m3u8)

    ElMessage.success('正在播放...')
  } catch (err) {
    const msg = err.response?.data?.detail || '播放失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

const playM3u8 = (url) => {
  const videoEl = document.querySelector('.player-video')

  // 清理旧实例
  if (hlsInstance.value) {
    hlsInstance.value.destroy()
  }

  if (Hls.isSupported()) {
    const hls = new Hls()
    hls.loadSource(url)
    hls.attachMedia(videoEl)
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      videoEl.play()
    })
    hlsInstance.value = hls
  } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
    // Safari 原生支持 HLS
    videoEl.src = url
    videoEl.play()
  }
}

onUnmounted(() => {
  if (hlsInstance.value) {
    hlsInstance.value.destroy()
  }
})

watch(() => route.params.id, loadData)

onMounted(loadData)
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
.play-section,
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

/* 播放按钮 */
.play-btn-large {
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.play-btn-large:hover:not(:disabled) {
  transform: scale(1.02);
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}
.play-btn-large:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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