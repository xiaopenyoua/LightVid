<template>
  <div class="home">
    <div class="header">
      <h1>LightVid 轻影</h1>
      <el-input v-model="keyword" placeholder="搜索..." style="width: 300px" @keyup.enter="handleSearch" />
      <el-tabs v-model="category" @tab-change="loadVideos">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="电影" name="movie" />
        <el-tab-pane label="剧集" name="tv" />
      </el-tabs>
    </div>
    <div v-loading="loading" class="content">
      <PosterWall :videos="videos" @select="handleSelect" />
      <el-empty v-if="!loading && videos.length === 0" description="暂无数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideos } from '../api'
import PosterWall from '../components/PosterWall.vue'

const router = useRouter()
const videos = ref([])
const category = ref('all')
const keyword = ref('')
const loading = ref(false)

onMounted(() => {
  loadVideos()
})

const loadVideos = async () => {
  loading.value = true
  try {
    const params = {}
    if (category.value !== 'all') params.category = category.value
    const { data } = await getVideos(params)
    videos.value = data
  } catch {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  router.push({ path: '/search', query: { q: keyword.value } })
}

const handleSelect = (video) => {
  router.push(`/video/${video.tmdb_id}`)
}
</script>

<style scoped>
.header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
</style>
