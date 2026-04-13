<template>
  <div class="home">
    <!-- ==================== SECTION 1: HERO ==================== -->
    <section class="fullpage-section">
      <!-- Navigation -->
      <nav class="nav">
        <div class="nav-logo">轻影</div>
        <ul class="nav-links">
          <li><a href="#" class="active">首页</a></li>
          <li><a href="#">电影</a></li>
          <li><a href="#">剧集</a></li>
          <li><a href="#">综艺</a></li>
          <li><a href="#">动漫</a></li>
        </ul>
        <div class="nav-actions">
          <input type="text" class="nav-search" placeholder="搜索电影、剧集..." @keyup.enter="handleSearch" v-model="keyword" />
          <button class="nav-btn">👤</button>
        </div>
      </nav>

      <!-- Hero Carousel -->
      <HeroCarousel
        v-if="homeData?.trending_all?.length"
        :items="homeData.trending_all"
        @select="handleSelect"
        @play="handlePlay"
        @favorite="handleFavorite"
      />
    </section>

    <!-- ==================== SECTION 2: CONTENT ==================== -->
    <section class="fullpage-section content-section">
      <!-- Left Sidebar (sticky within this section) -->
      <GenreSidebar
        :genres="filteredGenres"
        @select="handleGenreSelect"
      />

      <!-- Right Content Area (scrollable) -->
      <main class="content-area">
        <div class="content-header">
          <div class="content-title">
            <h2>{{ currentGenre.name }}</h2>
            <span class="genre-tag" v-if="currentGenre.name !== '热门推荐'">按分类浏览</span>
          </div>
          <a href="#" class="content-more">查看全部 →</a>
        </div>

        <div v-if="loading" v-loading="true" style="min-height: 400px;"></div>
        <FilmGrid
          v-else-if="currentItems.length"
          :items="currentItems"
          :genres="allGenres"
          @select="handleSelect"
          @play="handlePlay"
        />
        <el-empty v-else description="暂无数据" />
      </main>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHome, getMovies, getTvShows, addFavorite } from '../api'
import HeroCarousel from '../components/HeroCarousel.vue'
import GenreSidebar from '../components/GenreSidebar.vue'
import FilmGrid from '../components/FilmGrid.vue'

const router = useRouter()
const loading = ref(false)
const homeData = ref(null)
const currentItems = ref([])
const currentGenre = ref({ key: 'hot', name: '热门推荐', media_type: null, tmdb_id: null })

// 合并电影类型和剧集类型
const filteredGenres = computed(() => homeData.value?.genres || [])
const allGenres = computed(() => homeData.value?.genres || [])

// 热门推荐 = trending_all
const trendingAll = computed(() => homeData.value?.trending_all || [])

const loadHome = async () => {
  try {
    const { data } = await getHome()
    homeData.value = data
    // 默认显示热门推荐
    currentItems.value = trendingAll.value
  } catch {
    ElMessage.error('加载首页数据失败')
  }
}

const loadGenreContent = async (genre) => {
  loading.value = true
  currentItems.value = []
  try {
    if (genre.media_type === 'movie') {
      const { data } = await getMovies({ genre: genre.tmdb_id, page: 1 })
      currentItems.value = data.slice(0, 20)
    } else if (genre.media_type === 'tv') {
      const { data } = await getTvShows({ genre: genre.tmdb_id, page: 1 })
      currentItems.value = data.slice(0, 20)
    } else if (genre.key === 'hot') {
      currentItems.value = trendingAll.value
    } else {
      // 综艺/动漫等未知类型，显示 trending_all 作为兜底
      currentItems.value = trendingAll.value
    }
  } catch {
    currentItems.value = []
  } finally {
    loading.value = false
  }
}

const handleGenreSelect = (genre) => {
  currentGenre.value = genre
  loadGenreContent(genre)
}

const handleSelect = (item) => {
  router.push(`/video/${item.media_type}/${item.tmdb_id}`)
}

const handlePlay = (item) => {
  router.push(`/video/${item.media_type}/${item.tmdb_id}/play`)
}

const handleFavorite = async (item) => {
  try {
    await addFavorite(item.tmdb_id)
    ElMessage.success('收藏成功')
  } catch {
    ElMessage.error('收藏失败')
  }
}

const keyword = ref('')

const handleSearch = () => {
  if (keyword.value.trim()) {
    router.push({ path: '/search', query: { q: keyword.value.trim() } })
  }
}

onMounted(async () => {
  await loadHome()
})
</script>

<style scoped>
/* ===== Scroll Snap 容器 ===== */
.home {
  min-height: 100vh;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  scroll-behavior: smooth;
  background: #0d0d15;
}

/* ===== Fullpage Section ===== */
.fullpage-section {
  height: 100vh;
  scroll-snap-align: start;
  position: relative;
  overflow: hidden;
}

/* ===== Navigation ===== */
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
  padding: 24px 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(180deg, rgba(10,10,15,0.8) 0%, transparent 100%);
}
.nav-logo {
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.nav-links {
  display: flex;
  gap: 8px;
  list-style: none;
}
.nav-links a {
  color: rgba(255,255,255,0.65);
  text-decoration: none;
  padding: 10px 20px;
  border-radius: 24px;
  font-size: 14px;
  transition: all 0.2s;
}
.nav-links a:hover { color: #fff; background: rgba(255,255,255,0.08); }
.nav-links a.active {
  color: #fff;
  background: rgba(255,255,255,0.12);
}
.nav-actions { display: flex; gap: 12px; align-items: center; }
.nav-search {
  width: 200px;
  height: 40px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 20px;
  padding: 0 20px;
  color: #fff;
  font-size: 14px;
}
.nav-search::placeholder { color: rgba(255,255,255,0.4); }
.nav-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 16px;
}

/* ===== Content Section ===== */
.content-section {
  display: flex;
  height: 100vh;
  background: #0d0d15;
  flex-shrink: 0;
}

/* GenreSidebar 在 content-section 内是 sticky 的 */
:deep(.genre-sidebar) {
  height: 100vh;
  position: sticky;
  top: 0;
  flex-shrink: 0;
}

/* ===== Content Area (independent scroll) ===== */
.content-area {
  flex: 1;
  height: 100vh;
  overflow-y: auto;
  padding: 100px 48px 60px;
  scroll-snap-align: none;
}
.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  position: sticky;
  top: 0;
  background: #0d0d15;
  padding-bottom: 16px;
  z-index: 10;
}
.content-title {
  display: flex;
  align-items: center;
  gap: 16px;
}
.content-title h2 {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}
.genre-tag {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
}
.content-more {
  color: rgba(255,255,255,0.5);
  text-decoration: none;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s;
}
.content-more:hover { color: #fff; }
</style>
