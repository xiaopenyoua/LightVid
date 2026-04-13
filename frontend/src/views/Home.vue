<template>
  <div id="fullpage" ref="fullpageRef">
    <!-- ==================== SECTION 1: HERO ==================== -->
    <div class="section hero-section">
      <HeroCarousel
        v-if="homeData?.trending_all?.length"
        :items="homeData.trending_all"
        @select="handleSelect"
        @play="handlePlay"
        @favorite="handleFavorite"
      />
    </div>

    <!-- ==================== SECTION 2: CONTENT ==================== -->
    <div class="section content-section">
      <GenreSidebar
        :genres="filteredGenres"
        @select="handleGenreSelect"
      />

      <main class="content-area" ref="contentRef">
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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

const fullpageRef = ref(null)
const contentRef = ref(null)
const currentSection = ref(0)
let isScrolling = false
let expectedDelta = 0 // 期望的滚动方向（来自 wheel 事件）

const filteredGenres = computed(() => homeData.value?.genres || [])
const allGenres = computed(() => homeData.value?.genres || [])
const trendingAll = computed(() => homeData.value?.trending_all || [])

const loadHome = async () => {
  try {
    const { data } = await getHome()
    homeData.value = data
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

const goToSection = (index) => {
  if (isScrolling || index < 0 || index > 1) return
  if (index === currentSection.value) return
  isScrolling = true
  currentSection.value = index
  const section = fullpageRef.value.children[index]
  section.scrollIntoView({ behavior: 'smooth', block: 'start' })
  setTimeout(() => {
    isScrolling = false
  }, 800)
}

const handleWheel = (e) => {
  if (isScrolling) {
    e.preventDefault()
    return
  }

  const delta = e.deltaY || e.detail || -e.wheelDelta
  const contentArea = e.target.closest('.content-area')
  const genreList = e.target.closest('.genre-list')

  // 如果在内容区或侧边栏内部
  if (contentArea || genreList) {
    // 记录期望的滚动方向
    expectedDelta = delta
    return
  }

  // 在空白区域滚动
  if (delta > 30) {
    goToSection(1)
  } else if (delta < -30) {
    goToSection(0)
  }
}

const handleScroll = (e) => {
  if (isScrolling) return

  const area = e.target
  if (!area) return
  const isContentArea = area.closest?.('.content-area')
  const isGenreSidebar = area.closest?.('.genre-sidebar')
  if (!isContentArea && !isGenreSidebar) return

  const scrollTop = area.scrollTop
  const scrollHeight = area.scrollHeight
  const clientHeight = area.clientHeight
  const isAtTop = scrollTop <= 1
  const isAtBottom = scrollTop + clientHeight >= scrollHeight - 2

  // 检测是否在边界处继续滚动
  if (expectedDelta < -10 && isAtTop && currentSection.value === 1) {
    goToSection(0)
    expectedDelta = 0
    return
  }
  if (expectedDelta > 10 && isAtBottom && currentSection.value === 0) {
    goToSection(1)
    expectedDelta = 0
    return
  }

  // 如果滚动到中间位置，清除期望方向
  if (!isAtTop && !isAtBottom) {
    expectedDelta = 0
  }
}

const handleKeydown = (e) => {
  if (isScrolling) return
  if (e.key === 'ArrowDown' || e.key === 'PageDown') {
    e.preventDefault()
    goToSection(1)
  } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
    e.preventDefault()
    goToSection(0)
  }
}

onMounted(() => {
  loadHome()
  window.addEventListener('wheel', handleWheel, { passive: false })
  window.addEventListener('keydown', handleKeydown)
  document.querySelectorAll('.content-area, .genre-list').forEach(el => {
    el.addEventListener('scroll', handleScroll, { passive: true })
  })
})

onUnmounted(() => {
  window.removeEventListener('wheel', handleWheel)
  window.removeEventListener('keydown', handleKeydown)
  document.querySelectorAll('.content-area, .genre-list').forEach(el => {
    el.removeEventListener('scroll', handleScroll)
  })
})
</script>

<style scoped>
#fullpage {
  height: 100vh;
  overflow: hidden;
}

.section {
  height: 100vh;
  overflow: hidden;
}

.hero-section {
  background: #0d0d15;
}

.content-section {
  display: flex;
  height: 100vh;
  background: #0d0d15;
}

:deep(.genre-sidebar) {
  height: 100vh;
  overflow-y: auto;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 100px 48px 60px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.content-area::-webkit-scrollbar {
  display: none;
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
