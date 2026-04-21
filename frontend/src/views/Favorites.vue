<template>
  <div class="page-container">
    <header class="page-header">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <h1>我的收藏</h1>
    </header>

    <div class="page-content">
      <LoadingSpinner v-if="loading" :size="50" class="loading-center" />
      <div v-else-if="favorites.length" class="favorites-grid">
        <div
          v-for="item in favorites"
          :key="item.id"
          class="favorite-item"
        >
          <div class="item-poster" @click="handlePlay(item.video)">
            <img :src="item.video?.poster_url || posterPlaceholder" :alt="item.video?.title" />
            <div class="play-overlay">
              <div class="play-btn">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
              </div>
            </div>
          </div>
          <div class="item-info">
            <h3>{{ item.video?.title }}</h3>
            <span class="media-type">{{ item.video?.media_type === 'movie' ? '电影' : '剧集' }}</span>
          </div>
          <button class="delete-btn" @click="handleDelete(item)" title="取消收藏">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          </button>
        </div>
      </div>
      <el-empty v-else description="暂无收藏" />
    </div>

    <ConfirmDialog
      ref="confirmDialog"
      title="取消收藏"
      confirmText="取消收藏"
      type="danger"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFavorites, removeFavorite } from '../api'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const router = useRouter()
const favorites = ref([])
const loading = ref(false)
const confirmDialog = ref(null)
const posterPlaceholder = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNTAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzMzMyIgc3Ryb2tlPSIjNjY2IiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSI3NSIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjOTk5IiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiBkeT0iLjNlbSI+Tm8gUG9zdGVyPC90ZXh0Pjwvc3ZnPg=='

const loadFavorites = async () => {
  loading.value = true
  try {
    const { data } = await getFavorites()
    favorites.value = data
  } catch {
    ElMessage.error('加载收藏失败')
  } finally {
    loading.value = false
  }
}

const handlePlay = (video) => {
  if (video) {
    router.push(`/video/${video.media_type}/${video.tmdb_id}/play`)
  }
}

const handleDelete = async (item) => {
  confirmDialog.value.message = `确定要取消收藏 "${item.video?.title}" 吗？`
  const confirmed = await confirmDialog.value.show()
  if (confirmed) {
    await removeFavorite(item.tmdb_id)
    ElMessage.success('已取消收藏')
    loadFavorites()
  }
}

onMounted(loadFavorites)
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

.loading-center {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 20px;
}

.favorite-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255,255,255,0.04);
  transition: transform 0.2s;
}
.favorite-item:hover {
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

.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(0,0,0,0.5);
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
}
.delete-btn svg {
  width: 16px;
  height: 16px;
}
.favorite-item:hover .delete-btn {
  opacity: 1;
}
.delete-btn:hover {
  background: rgba(239, 68, 68, 0.8);
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
  .favorites-grid {
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 12px;
  }
  .delete-btn {
    opacity: 1;
  }
}
</style>