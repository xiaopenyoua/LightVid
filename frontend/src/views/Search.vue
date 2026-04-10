<template>
  <div class="search-page">
    <div class="search-bar">
      <el-input v-model="keyword" placeholder="搜索视频名称..." style="width: 400px" @keyup.enter="handleSearch" />
      <el-button type="primary" @click="handleSearch" :loading="searching">搜索</el-button>
      <el-select v-model="mediaType" style="width: 120px">
        <el-option label="电影" value="movie" />
        <el-option label="剧集" value="tv" />
      </el-select>
    </div>
    <div class="crawl-bar">
      <el-input v-model="tmdbId" placeholder="输入 TMDB ID（如 550）" style="width: 400px" @keyup.enter="handleCrawl" />
      <el-button type="success" @click="handleCrawl" :loading="crawling">添加到本地</el-button>
    </div>
    <div v-loading="loading" class="results">
      <PosterWall :videos="videos" @select="handleSelect" />
      <el-empty v-if="!loading && videos.length === 0" description="暂无数据，请搜索或添加视频" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { searchTmdb, crawlVideo } from '../api'
import PosterWall from '../components/PosterWall.vue'

const router = useRouter()
const keyword = ref('')
const tmdbId = ref('')
const videos = ref([])
const searching = ref(false)
const crawling = ref(false)
const loading = ref(false)
const mediaType = ref('movie')

const handleSearch = async () => {
  if (!keyword.value) return
  searching.value = true
  try {
    const { data } = await searchTmdb(keyword.value, mediaType.value)
    videos.value = data
    if (data.length === 0) {
      ElMessage.info('未找到匹配的视频')
    }
  } catch (err) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

const handleCrawl = async () => {
  if (!tmdbId.value) return
  crawling.value = true
  try {
    await crawlVideo(tmdbId.value, mediaType.value)
    ElMessage.success('添加成功')
    // 重新搜索显示最新结果
    await handleSearch()
  } catch (err) {
    ElMessage.error('添加失败，请检查 TMDB ID 是否正确')
  } finally {
    crawling.value = false
  }
}

const handleSelect = (video) => {
  router.push(`/video/${video.tmdb_id}`)
}
</script>

<style scoped>
.search-page {
  padding: 20px;
}
.search-bar, .crawl-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.results {
  min-height: 200px;
}
</style>
