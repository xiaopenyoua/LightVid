<template>
  <div class="page-container">
    <header class="page-header">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <h1>搜索</h1>
    </header>

    <div class="page-content">
      <div class="search-wrapper">
        <input
          type="text"
          class="nav-search"
          placeholder="输入关键词搜索..."
          v-model="keyword"
          @keyup.enter="doSearch"
        >
      </div>

      <LoadingSpinner v-if="loading" :size="50" class="loading-center" />
      <div v-else-if="results.length" class="results-grid">
        <div
          v-for="item in results"
          :key="`${item.tmdb_id}-${item.season_number || 0}`"
          class="result-item"
        >
          <div class="item-poster" @click="goDetail(item)">
            <img :src="item.poster_url || posterPlaceholder" :alt="item.title" />
            <div class="play-overlay">
              <div class="play-btn">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
              </div>
            </div>
          </div>
          <div class="item-info">
            <h3>{{ item.title }}</h3>
            <span class="media-type">{{ item.media_type === 'movie' ? '电影' : '剧集' }}</span>
          </div>
        </div>
      </div>
      <el-empty v-else-if="searched" description="未找到结果" />
      <div v-else class="search-hint">
        <p>输入关键词搜索电影和剧集</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { searchVideos } from '../api'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const keyword = ref('')
const results = ref([])
const loading = ref(false)
const searched = ref(false)
const posterPlaceholder = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNTAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzMzMyIgc3Ryb2tlPSIjNjY2IiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSI3NSIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjOTk5IiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiBkeT0iLjNlbSI+Tm8gUG9zdGVyPC90ZXh0Pjwvc3ZnPg=='

const doSearch = async () => {
  if (!keyword.value.trim()) return
  loading.value = true
  searched.value = false
  try {
    const { data } = await searchVideos(keyword.value)
    results.value = data
  } catch {
    results.value = []
    ElMessage.error('搜索失败')
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
.page-container {
  min-height: 100vh;
  background: #0d0d1a;
}

.page-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  height: 90px;
  padding: 0 48px;
  box-sizing: border-box;
  background: rgba(20, 20, 30, 0.98);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.page-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin: 0;
  flex: 1;
  text-align: center;
  padding-right: 120px;
}

.nav-logo {
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-decoration: none;
  cursor: pointer;
}

.page-content {
  padding: 110px 32px 24px;
}

.search-wrapper {
  margin-bottom: 24px;
}

.nav-search {
  width: 400px;
  height: 44px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 22px;
  padding: 0 24px;
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
}
.nav-search::placeholder {
  color: rgba(255,255,255,0.4);
}
.nav-search:focus {
  background: rgba(255,255,255,0.15);
  border-color: rgba(255,255,255,0.25);
}

.loading-center {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 20px;
}

.result-item {
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255,255,255,0.04);
  transition: transform 0.2s;
}
.result-item:hover {
  transform: scale(1.03);
}

.item-poster {
  position: relative;
  cursor: pointer;
}
.item-poster img {
  width: 100%;
  aspect-ratio: 2/3;
  object-fit: cover;
  display: block;
}

.play-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}
.item-poster:hover .play-overlay {
  opacity: 1;
}

.play-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}
.play-btn svg {
  width: 24px;
  height: 24px;
  color: #fff;
  margin-left: 3px;
}

.item-info {
  padding: 10px 12px;
}
.item-info h3 {
  margin: 0 0 4px 0;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.media-type {
  font-size: 11px;
  color: #888;
}

.search-hint {
  text-align: center;
  padding: 60px 0;
  color: #666;
}

@media (max-width: 600px) {
  .page-header {
    padding: 0 20px;
    height: 70px;
  }
  .page-header h1 {
    padding-right: 80px;
    font-size: 18px;
  }
  .nav-logo {
    font-size: 22px;
  }
  .page-content {
    padding: 90px 16px 16px;
  }
  .nav-search {
    width: 100%;
    max-width: 300px;
  }
  .results-grid {
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 12px;
  }
}
</style>