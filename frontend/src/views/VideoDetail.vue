<template>
  <div class="video-detail" v-if="video">
    <div class="backdrop" v-if="video.backdrop_url">
      <img :src="video.backdrop_url" />
    </div>
    <div class="detail-content">
      <div class="poster">
        <img :src="video.poster_url" />
      </div>
      <div class="info">
        <h1>{{ video.title }}</h1>
        <div class="meta">
          <span v-if="video.vote_average">评分: {{ video.vote_average.toFixed(1) }}</span>
          <span v-if="video.release_date">{{ video.release_date.slice(0, 4) }}年</span>
          <span v-if="video.genres">{{ video.genres }}</span>
        </div>
        <p class="tagline" v-if="video.tagline">{{ video.tagline }}</p>
        <p class="overview">{{ video.overview }}</p>

        <!-- 剧集季节选择 -->
        <div v-if="video.seasons?.length" class="seasons">
          <span
            v-for="season in video.seasons"
            :key="season.season_number"
            :class="{ active: currentSeason === season.season_number }"
            @click="selectSeason(season.season_number)"
          >
            {{ season.name }}
          </span>
        </div>

        <div class="actions">
          <el-button type="primary" size="large" @click="goPlay">
            开始播放
          </el-button>
          <el-button size="large" @click="toggleFavorite">
            {{ isFavorite ? '取消收藏' : '收藏' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideoDetail, addFavorite, removeFavorite, checkFavorite } from '../api'

const route = useRoute()
const router = useRouter()
const video = ref(null)
const isFavorite = ref(false)
const currentSeason = ref(1)

const mediaType = () => route.params.media_type || 'movie'
const tmdbId = () => parseInt(route.params.id)

const loadDetail = async () => {
  try {
    const { data } = await getVideoDetail(mediaType(), tmdbId())
    video.value = data
    if (video.value?.seasons?.length) {
      currentSeason.value = video.value.seasons[0].season_number
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
  }
}

const selectSeason = (season) => {
  currentSeason.value = season
  router.replace({
    query: { ...route.query, season }
  })
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

const goPlay = () => {
  router.push(`/video/${mediaType()}/${tmdbId()}/play?season=${currentSeason.value}`)
}

watch(() => route.params.id, loadDetail)

onMounted(loadDetail)
</script>

<style scoped>
.video-detail {
  position: relative;
  min-height: 100vh;
  padding: 40px;
}
.backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
}
.backdrop img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(30px);
  opacity: 0.3;
}
.detail-content {
  display: flex;
  gap: 40px;
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
}
.poster img {
  width: 300px;
  border-radius: 12px;
}
.info {
  flex: 1;
}
.info h1 {
  margin: 0 0 16px 0;
}
.meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  color: #999;
}
.tagline {
  font-style: italic;
  color: #666;
  margin-bottom: 16px;
}
.overview {
  line-height: 1.6;
  color: #ccc;
  margin-bottom: 20px;
}
.seasons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.seasons span {
  padding: 4px 12px;
  background: rgba(255,255,255,0.1);
  border-radius: 16px;
  cursor: pointer;
}
.seasons span.active {
  background: #409eff;
  color: white;
}
.actions {
  display: flex;
  gap: 12px;
}
</style>
