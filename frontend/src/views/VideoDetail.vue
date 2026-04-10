<template>
  <div class="video-detail" v-if="video">
    <img :src="video.poster_url" class="poster" />
    <div class="info">
      <h1>{{ video.title }}</h1>
      <p class="rating" v-if="video.rating">评分: {{ video.rating }}</p>
      <p class="year" v-if="video.year">{{ video.year }}年</p>
      <p class="genres" v-if="video.genres">{{ video.genres }}</p>
      <p class="summary">{{ video.summary }}</p>
      <div class="actions">
        <el-button type="primary" size="large" @click="$router.push(`/video/${video.tmdb_id}/play`)">
          开始播放
        </el-button>
        <el-button size="large" @click="toggleFavorite">
          {{ isFavorite ? '取消收藏' : '收藏' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideo, addFavorite, removeFavorite, checkFavorite } from '../api'

const route = useRoute()
const video = ref(null)
const isFavorite = ref(false)

const loadData = async () => {
  video.value = await getVideo(route.params.id)
  try {
    const { data } = await checkFavorite(route.params.id)
    isFavorite.value = data.is_favorite
  } catch {}
}

const toggleFavorite = async () => {
  try {
    if (isFavorite.value) {
      await removeFavorite(route.params.id)
      isFavorite.value = false
      ElMessage.success('已取消收藏')
    } else {
      await addFavorite(route.params.id)
      isFavorite.value = true
      ElMessage.success('已添加收藏')
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.video-detail {
  display: flex;
  gap: 40px;
  padding: 40px;
}
.poster {
  width: 300px;
  border-radius: 12px;
}
.info h1 {
  margin: 0 0 20px 0;
}
.summary {
  line-height: 1.6;
  color: #666;
}
.actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}
</style>
