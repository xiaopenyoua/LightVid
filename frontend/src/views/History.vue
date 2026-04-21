<template>
  <div class="page-container">
    <header class="page-header">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <h1>继续观看</h1>
    </header>

    <div class="page-content">
      <LoadingSpinner v-if="loading" :size="50" class="loading-center" />
      <div v-else-if="history.length" class="history-list">
        <div
          v-for="item in history"
          :key="`${item.tmdb_id}-${item.season || 0}`"
          class="history-item"
        >
          <div class="item-main" @click="handleResume(item)">
            <img :src="item.poster_url || posterPlaceholder" class="poster" />
            <div class="info">
              <h3>{{ item.title }}</h3>
              <p class="subtitle" v-if="item.season">
                第{{ item.season }}季
              </p>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: getProgress(item) + '%' }"></div>
              </div>
              <span class="progress-text">{{ formatProgress(item) }}</span>
            </div>
          </div>
          <div class="item-actions">
            <button class="action-btn play" @click="handleResume(item)" title="继续播放">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            </button>
            <button class="action-btn delete" @click="handleDelete(item)" title="删除">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
            </button>
          </div>
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

const formatProgress = (item) => {
  if (!item.current_time) return '0%'
  const pct = getProgress(item)
  return `${Math.floor(item.current_time / 60)}分 / ${Math.floor((item.duration || 0) / 60)}分`
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.2s;
}
.history-item:hover {
  background: rgba(255,255,255,0.08);
}

.item-main {
  display: flex;
  gap: 16px;
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.poster {
  width: 120px;
  height: 68px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
  background: #333;
}

.info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.info h3 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtitle {
  margin: 0 0 6px 0;
  font-size: 12px;
  color: #888;
}

.progress-bar {
  height: 3px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
  margin-bottom: 4px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
  transition: width 0.3s;
}

.progress-text {
  font-size: 11px;
  color: #666;
}

.item-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}
.history-item:hover .item-actions {
  opacity: 1;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  border: none;
  color: #888;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.action-btn svg {
  width: 18px;
  height: 18px;
}
.action-btn:hover {
  background: rgba(255,255,255,0.15);
  color: #fff;
}
.action-btn.play:hover {
  background: rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
}
.action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
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
  .poster {
    width: 90px;
    height: 50px;
  }
  .info h3 {
    font-size: 14px;
  }
  .item-actions {
    opacity: 1;
  }
}
</style>