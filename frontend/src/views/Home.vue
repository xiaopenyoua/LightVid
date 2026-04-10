<template>
  <div class="home">
    <div class="header">
      <h1>LightVid 轻影</h1>
      <el-input v-model="keyword" placeholder="搜索..." style="width: 300px" @keyup.enter="handleSearch" />
    </div>
    <div v-loading="loading" class="content">
      <!-- 顶部轮播 -->
      <div class="carousel-section" v-if="homeData?.lists?.trending_movie?.length">
        <Carousel :items="homeData.lists.trending_movie.slice(0, 10)" @select="handleSelect" />
      </div>

      <!-- 横向滚动分区 -->
      <VideoRow
        v-if="homeData?.lists?.popular_movie?.length"
        title="热门电影"
        :items="homeData.lists.popular_movie"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.popular_tv?.length"
        title="热门剧集"
        :items="homeData.lists.popular_tv"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.trending_movie?.length"
        title="本周热门"
        :items="homeData.lists.trending_movie"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.top_rated_movie?.length"
        title="高分电影"
        :items="homeData.lists.top_rated_movie"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.top_rated_tv?.length"
        title="高分剧集"
        :items="homeData.lists.top_rated_tv"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.upcoming_movie?.length"
        title="即将上映"
        :items="homeData.lists.upcoming_movie"
        @select="handleSelect"
      />

      <!-- Genre 分区（按类型） -->
      <template v-if="movieGenres.length">
        <VideoRow
          v-for="genre in movieGenres"
          :key="`movie-${genre.tmdb_id}`"
          :title="`${genre.name}电影`"
          :items="genreMovies[genre.tmdb_id] || []"
          @select="handleSelect"
        />
      </template>

      <template v-if="tvGenres.length">
        <VideoRow
          v-for="genre in tvGenres"
          :key="`tv-${genre.tmdb_id}`"
          :title="`${genre.name}剧集`"
          :items="genreTv[genre.tmdb_id] || []"
          @select="handleSelect"
        />
      </template>

      <el-empty v-if="!loading && !homeData" description="暂无数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHome, getMovies, getTvShows } from '../api'
import Carousel from '../components/Carousel.vue'
import VideoRow from '../components/VideoRow.vue'

const router = useRouter()
const loading = ref(false)
const homeData = ref(null)
const genreMovies = ref({})
const genreTv = ref({})

const movieGenres = computed(() => homeData.value?.genres?.filter(g => g.media_type === 'movie') || [])
const tvGenres = computed(() => homeData.value?.genres?.filter(g => g.media_type === 'tv') || [])

const loadHome = async () => {
  loading.value = true
  try {
    const { data } = await getHome()
    homeData.value = data
  } catch {
    ElMessage.error('加载首页数据失败')
  } finally {
    loading.value = false
  }
}

const loadGenreMovies = async (genreId) => {
  if (genreMovies.value[genreId]) return  // 已加载
  try {
    const { data } = await getMovies({ genre: genreId, page: 1 })
    genreMovies.value[genreId] = data.slice(0, 20)
  } catch {
    genreMovies.value[genreId] = []
  }
}

const loadGenreTv = async (genreId) => {
  if (genreTv.value[genreId]) return
  try {
    const { data } = await getTvShows({ genre: genreId, page: 1 })
    genreTv.value[genreId] = data.slice(0, 20)
  } catch {
    genreTv.value[genreId] = []
  }
}

const handleSearch = () => {
  router.push({ path: '/search', query: { q: keyword.value } })
}

const handleSelect = (item) => {
  router.push(`/video/${item.media_type}/${item.tmdb_id}`)
}

const keyword = ref('')

onMounted(async () => {
  await loadHome()
  // 预加载前3个 genre 的内容
  movieGenres.value.slice(0, 3).forEach(g => loadGenreMovies(g.tmdb_id))
  tvGenres.value.slice(0, 3).forEach(g => loadGenreTv(g.tmdb_id))
})
</script>

<style scoped>
.home {
  min-height: 100vh;
}
.header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.content {
  padding: 0;
}
.carousel-section {
  padding: 20px 20px 0 20px;
}
</style>
