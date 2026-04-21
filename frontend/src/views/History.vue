<template>
  <div class="page-container">
    <header class="page-header">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <h1>继续观看</h1>
    </header>

    <div class="page-content">
      <LoadingSpinner v-if="loading" :size="50" class="loading-center" />
      <div v-else-if="history.length" class="history-grid">
        <div
          v-for="item in history"
          :key="`${item.tmdb_id}-${item.season || 0}`"
          class="history-item"
        >
          <div class="item-poster" @click="handleResume(item)">
            <img :src="item.poster_url || posterPlaceholder" :alt="item.title" />
            <div class="play-overlay">
              <div class="play-btn">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
              </div>
            </div>
            <div class="progress-indicator">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: getProgress(item) + '%' }"></div>
              </div>
            </div>
          </div>
          <div class="item-info">
            <h3>{{ item.title }}</h3>
            <span class="subtitle" v-if="item.season">第{{ item.season }}季</span>
            <span class="subtitle" v-else>电影</span>
          </div>
          <button class="delete-btn" @click="handleDelete(item)" title="删除">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
          </button>
        </div>
      </div>
      <el-empty v-else description="暂无观看历史" />
    </div>

    <ConfirmDialog
      ref="confirmDialog"
      title="删除播放记录"
      confirmText="删除"
      type="danger"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHistory, deleteHistory } from '../api'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const router = useRouter()
const history = ref([])
const loading = ref(false)
const confirmDialog = ref(null)
const posterPlaceholder = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNTAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzMzMyIgc3Ryb2tlPSIjNjY2IiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSI3NSIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjOTk5IiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiBkeT0iLjNlbSI+Tm8gUG9zdGVyPC90ZXh0Pjwvc3ZnPg=='

const loadHistory = async () => {
  loading.value = true
  try {
    const { data } = await getHistory()
    history.value = data
  } catch {
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

const getProgress = (item) => {
  if (!item.duration) return 0
  return Math.min(100, (item.current_time / item.duration) * 100)
}

const handleResume = (item) => {
  const query = {}
  if (item.season) {
    query.season = item.season
    query.episode = item.episode || 1
  }
  router.push({ path: `/video/${item.media_type}/${item.tmdb_id}/play`, query })
}

const handleDelete = async (item) => {
  const msg = item.season
    ? `确定要删除 "${item.title}" 第${item.season}季的播放记录吗？`
    : `确定要删除 "${item.title}" 的播放记录吗？`

  confirmDialog.value.message = msg
  const confirmed = await confirmDialog.value.show()
  if (confirmed) {
    await deleteHistory(item.tmdb_id, item.season || null, null)
    ElMessage.success('已删除')
    loadHistory()
  }
}

onMounted(loadHistory)
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

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 24px;
}

.history-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255,255,255,0.04);
  transition: transform 0.2s;
}
.history-item:hover {
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

.progress-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
}
.progress-bar {
  height: 3px;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
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
.subtitle {
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
.history-item:hover .delete-btn {
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
  .history-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 16px;
  }
  .delete-btn {
    opacity: 1;
  }
}
</style>