<template>
  <div class="history-page">
    <h2>继续观看</h2>
    <div v-loading="loading" class="history-list">
      <div v-for="item in history" :key="item.id" class="history-item" @click="handleResume(item)">
        <img :src="item.video?.poster_url" class="poster" />
        <div class="info">
          <h3>{{ item.video?.title }}</h3>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getProgress(item) + '%' }"></div>
          </div>
          <span class="progress-text">{{ formatProgress(item) }}</span>
        </div>
      </div>
      <el-empty v-if="!loading && history.length === 0" description="暂无观看历史" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHistory, deleteHistory } from '../api'

const router = useRouter()
const history = ref([])
const loading = ref(false)

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
  return Math.min(100, (item.progress / item.duration) * 100)
}

const formatProgress = (item) => {
  if (!item.progress) return '0%'
  const pct = getProgress(item)
  return `${Math.floor(item.progress / 60)}分 / ${Math.floor((item.duration || 0) / 60)}分`
}

const handleResume = (item) => {
  router.push(`/video/${item.tmdb_id}/play`)
}

onMounted(loadHistory)
</script>

<style scoped>
.history-page { padding: 20px; }
.history-list { display: flex; flex-direction: column; gap: 15px; }
.history-item {
  display: flex;
  gap: 15px;
  cursor: pointer;
  padding: 10px;
  border-radius: 8px;
  background: #1a1a2e;
}
.history-item:hover { background: #252540; }
.poster { width: 120px; height: 68px; object-fit: cover; border-radius: 6px; }
.info { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.info h3 { margin: 0 0 8px 0; font-size: 16px; }
.progress-bar { height: 4px; background: #333; border-radius: 2px; margin-bottom: 4px; }
.progress-fill { height: 100%; background: #409eff; border-radius: 2px; }
.progress-text { font-size: 12px; color: #888; }
</style>
