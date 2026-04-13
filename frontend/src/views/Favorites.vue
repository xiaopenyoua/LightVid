<template>
  <div class="favorites-page">
    <h2>我的收藏</h2>
    <div class="favorites-list">
      <LoadingSpinner v-if="loading" :size="50" class="loading-center" />
      <PosterWall :videos="videos" @select="handleSelect" />
      <el-empty v-if="!loading && videos.length === 0" description="暂无收藏" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFavorites } from '../api'
import PosterWall from '../components/PosterWall.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const router = useRouter()
const videos = ref([])
const loading = ref(false)

const loadFavorites = async () => {
  loading.value = true
  try {
    const { data } = await getFavorites()
    videos.value = data.map(f => f.video)
  } catch {
    ElMessage.error('加载收藏失败')
  } finally {
    loading.value = false
  }
}

const handleSelect = (video) => {
  router.push(`/video/${video.tmdb_id}`)
}

onMounted(loadFavorites)
</script>

<style scoped>
.favorites-page { padding: 20px; }
.favorites-list { min-height: 200px; }
.loading-center { display: flex; justify-content: center; padding: 40px 0; }
</style>
