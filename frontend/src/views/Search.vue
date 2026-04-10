<template>
  <div class="search-page">
    <div class="search-header">
      <h1>搜索</h1>
      <el-input v-model="keyword" placeholder="输入关键词搜索..." style="width: 400px" @keyup.enter="doSearch" />
    </div>
    <div v-loading="loading" class="search-results">
      <div v-if="results.length" class="results-grid">
        <div v-for="item in results" :key="`${item.tmdb_id}-${item.season_number || 0}`" class="result-item" @click="goDetail(item)">
          <img :src="item.poster_url" />
          <div class="result-info">
            <h3>{{ item.title }}</h3>
            <span class="media-type">{{ item.media_type === 'movie' ? '电影' : '剧集' }}</span>
          </div>
        </div>
      </div>
      <el-empty v-else-if="!loading && searched" description="未找到结果" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchVideos } from '../api'

const route = useRoute()
const router = useRouter()
const keyword = ref('')
const results = ref([])
const loading = ref(false)
const searched = ref(false)

const doSearch = async () => {
  if (!keyword.value.trim()) return
  loading.value = true
  searched.value = false
  try {
    const { data } = await searchVideos(keyword.value)
    results.value = data
  } catch {
    results.value = []
  } finally {
    loading.value = false
    searched.value = true
  }
}

const goDetail = (item) => {
  router.push(`/video/${item.media_type}/${item.tmdb_id}`)
}

onMounted(() => {
  if (route.query.q) {
    keyword.value = route.query.q
    doSearch()
  }
})
</script>

<style scoped>
.search-page {
  padding: 20px;
}
.search-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}
.result-item {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}
.result-item img {
  width: 100%;
  aspect-ratio: 2/3;
  object-fit: cover;
}
.result-info {
  padding: 12px;
}
.result-info h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
}
.media-type {
  font-size: 12px;
  color: #999;
}
</style>
