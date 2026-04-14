<template>
  <div class="home-page">
    <!-- 顶部导航栏 -->
    <nav class="nav">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <div class="nav-actions">
        <input type="text" class="nav-search" placeholder="搜索电影、剧集...">
        <button class="nav-btn">👤</button>
      </div>
    </nav>

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
        @select="handleGenreSelect"
      />

      <main class="content-area">
        <div class="content-header">
          <div class="content-title">
            <h2>{{ currentGenre.name }}</h2>
            <span class="genre-tag" v-if="currentGenre.name !== '热门推荐'">按分类浏览</span>
          </div>
          <a href="#" class="content-more">查看全部 →</a>
        </div>

        <!-- 筛选条件 -->
        <div class="filter-bar" v-if="showFilter">
          <div class="filter-group">
            <span class="filter-label">排序</span>
            <div class="filter-chips">
              <span
                v-for="item in sortOptions"
                :key="item.value"
                class="chip"
                :class="{ active: filters.sort_by === item.value }"
                @click="selectFilter('sort_by', item.value)"
              >{{ item.label }}</span>
            </div>
          </div>
          <div class="filter-group">
            <span class="filter-label">类型</span>
            <div class="filter-chips">
              <span
                v-for="item in genreOptions"
                :key="item.value"
                class="chip"
                :class="{ active: filters.genre === item.value }"
                @click="selectFilter('genre', item.value)"
              >{{ item.label }}</span>
            </div>
          </div>
          <div class="filter-group">
            <span class="filter-label">语言</span>
            <div class="filter-chips">
              <span
                v-for="item in languageOptions"
                :key="item.value"
                class="chip"
                :class="{ active: filters.language === item.value }"
                @click="selectFilter('language', item.value)"
              >{{ item.label }}</span>
            </div>
          </div>
          <div class="filter-group">
            <span class="filter-label">年份</span>
            <div class="filter-chips">
              <span
                v-for="item in yearOptions"
                :key="item.value"
                class="chip"
                :class="{ active: filters.year === item.value }"
                @click="selectFilter('year', item.value)"
              >{{ item.label }}</span>
            </div>
          </div>
        </div>

        <div v-if="loading" class="loading-wrapper">
          <LoadingSpinner :size="60" />
        </div>
        <FilmGrid
          v-else-if="currentItems.length"
          :items="currentItems"
          @select="handleSelect"
          @play="handlePlay"
        />
        <el-empty v-else description="暂无数据" />
      </main>
    </div>
  </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHome, getMovies, getTvShows, getGenres, addFavorite } from '../api'
import HeroCarousel from '../components/HeroCarousel.vue'
import GenreSidebar from '../components/GenreSidebar.vue'
import FilmGrid from '../components/FilmGrid.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const router = useRouter()
const loading = ref(false)
const homeData = ref(null)
const genreData = ref({ movie: [], tv: [] })
const currentItems = ref([])
const currentGenre = ref({ key: 'hot', name: '热门推荐', media_type: null, tmdb_id: null })
const filters = ref({
  sort_by: 'popularity.desc',
  genre: '',
  language: '',
  year: '',
})

// 排序选项
const sortOptions = [
  { label: '热门', value: 'popularity.desc' },
  { label: '评分', value: 'vote_average.desc' },
  { label: '最新', value: 'release_date.desc' },
]

// 语言选项
const languageOptions = [
  { label: '全部', value: '' },
  { label: '中文', value: 'zh' },
  { label: '英语', value: 'en' },
  { label: '日语', value: 'ja' },
  { label: '韩语', value: 'ko' },
]

// 年份选项（动态生成）
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = [{ label: '全部', value: '' }]
  for (let y = currentYear; y >= currentYear - 10; y--) {
    years.push({ label: String(y), value: String(y) })
  }
  years.push({ label: '更早', value: 'before' })
  return years
})

const fullpageRef = ref(null)
const currentSection = ref(0)
let isScrolling = false
let expectedDelta = 0

const showFilter = computed(() => {
  return ['movie', 'tv', 'variety', 'anime'].includes(currentGenre.value.key)
})

// 根据当前选中分类动态获取类型选项
const genreOptions = computed(() => {
  // 综艺不需要类型筛选
  if (currentGenre.value.key === 'variety') {
    return [{ label: '全部', value: '' }]
  }
  // 动漫使用电影类型，但默认选中动画
  const genres = genreData.value.movie
  return [{ label: '全部', value: '' }, ...genres.map(g => ({ label: g.name, value: String(g.tmdb_id) }))]
})

const popularAll = computed(() => homeData.value?.popular_all || [])

const loadHome = async () => {
  try {
    const [homeRes, genresRes] = await Promise.all([getHome(), getGenres()])
    homeData.value = homeRes.data
    // 按 media_type 分离 genres
    const allGenres = genresRes.data
    genreData.value = {
      movie: allGenres.filter(g => g.media_type === 'movie'),
      tv: allGenres.filter(g => g.media_type === 'tv'),
    }
    currentItems.value = popularAll.value
  } catch {
    ElMessage.error('加载首页数据失败')
  }
}

const loadGenreContent = async (genre) => {
  loading.value = true
  currentItems.value = []
  try {
    if (genre.key === 'hot') {
      currentItems.value = popularAll.value
    }
    // 电影
    else if (genre.key === 'movie') {
      const params = { page: 1, sort_by: filters.value.sort_by }
      if (filters.value.genre) params.genres = filters.value.genre
      if (filters.value.language) params.language = filters.value.language
      if (filters.value.year) {
        if (filters.value.year === 'before') {
          params.year = 2018
        } else {
          params.year = Number(filters.value.year)
        }
      }
      const { data } = await getMovies(params)
      currentItems.value = data.slice(0, 20)
    }
    // 剧集
    else if (genre.key === 'tv') {
      const params = { page: 1, sort_by: filters.value.sort_by }
      if (filters.value.genre) params.genres = filters.value.genre
      if (filters.value.language) params.language = filters.value.language
      if (filters.value.year) {
        if (filters.value.year === 'before') {
          params.year = 2018
        } else {
          params.year = Number(filters.value.year)
        }
      }
      const { data } = await getTvShows(params)
      currentItems.value = data.slice(0, 20)
    }
    // 综艺：使用 TV discover，genre 10764(Reality)+10767(Talk)+10766(Soap)
    else if (genre.key === 'variety') {
      const params = { page: 1, sort_by: filters.value.sort_by }
      params.genres = '10764,10767,10766'
      if (filters.value.language) params.language = filters.value.language
      if (filters.value.year) {
        if (filters.value.year === 'before') {
          params.year = 2018
        } else {
          params.year = Number(filters.value.year)
        }
      }
      const { data } = await getTvShows(params)
      currentItems.value = data.slice(0, 20)
    }
    // 动漫：默认使用 genre 16 (Animation)，但允许用户选择其他类型
    else if (genre.key === 'anime') {
      const params = { page: 1, sort_by: filters.value.sort_by }
      // 用户选择的类型，或者默认 Animation
      params.genres = filters.value.genre || '16'
      if (filters.value.language) params.language = filters.value.language
      if (filters.value.year) {
        if (filters.value.year === 'before') {
          params.year = 2018
        } else {
          params.year = Number(filters.value.year)
        }
      }
      const { data } = await getMovies(params)
      currentItems.value = data.slice(0, 20)
    }
    else {
      currentItems.value = popularAll.value
    }
  } catch {
    currentItems.value = []
  } finally {
    loading.value = false
  }
}

const handleGenreSelect = (genre) => {
  currentGenre.value = genre
  filters.value = {
    sort_by: 'popularity.desc',
    genre: '',
    language: '',
    year: '',
  }
  loadGenreContent(genre)
}

const selectFilter = (key, value) => {
  filters.value[key] = value
  loadGenreContent(currentGenre.value)
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
/* 页面容器 */
.home-page {
  min-height: 100vh;
  background: #0d0d1a;
}

/* 顶部导航栏 */
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
  text-decoration: none;
}
.nav-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
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
.nav-search::placeholder {
  color: rgba(255,255,255,0.4);
}
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
.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 0;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.filter-label {
  font-size: 13px;
  color: rgba(255,255,255,0.5);
  min-width: 40px;
}
.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  color: rgba(255,255,255,0.7);
  background: rgba(255,255,255,0.08);
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}
.chip:hover {
  background: rgba(255,255,255,0.12);
  color: #fff;
}
.chip.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}
.loading-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  width: 100%;
}
</style>
