<template>
  <div class="page-container">
    <header class="page-header">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <h1>TV Box 播放源</h1>
    </header>

    <div class="page-content">
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="source-count">{{ sources.length }} 个播放源</span>
        </div>
        <div class="toolbar-right">
          <el-button @click="handleSpeedTestAll" :loading="speedTesting" :disabled="sources.length === 0">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>
            全部测速
          </el-button>
          <el-button type="primary" @click="handleCrawl" :loading="crawling">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg>
            爬取新源
          </el-button>
        </div>
      </div>

      <div v-if="loading" class="loading-wrapper">
        <LoadingSpinner :size="50" />
      </div>
      <div v-else-if="sources.length" class="source-list">
        <div v-for="source in sources" :key="source.id" class="source-item">
          <div class="source-info">
            <h3 class="source-name">{{ source.name }}</h3>
            <p class="source-url">{{ source.url }}</p>
          </div>
          <div class="source-status" :class="getSpeedClass(source.speed)">
            <template v-if="source.testing">
              <LoadingSpinner :size="16" />
              <span>测速中...</span>
            </template>
            <template v-else-if="source.speed">
              <span class="speed-value">{{ source.speed.toFixed(1) }}s</span>
            </template>
            <template v-else>
              <span class="speed-untested">未测速</span>
            </template>
          </div>
          <div class="source-actions">
            <button class="action-btn" @click="handleSpeedTest(source)" title="测速">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>
            </button>
            <button class="action-btn delete" @click="handleDelete(source)" title="删除">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
            </button>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无播放源，点击爬取新源获取" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSources, triggerCrawl, speedTest, deleteSource } from '../api'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const sources = ref([])
const crawling = ref(false)
const speedTesting = ref(false)
const loading = ref(false)

onMounted(() => {
  loadSources()
})

const loadSources = async () => {
  loading.value = true
  try {
    const { data } = await getSources({ platform: 'tvbox' })
    sources.value = data
  } catch {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleCrawl = async () => {
  crawling.value = true
  try {
    await triggerCrawl()
    await loadSources()
    ElMessage.success('爬取完成')
  } catch (err) {
    ElMessage.error('爬取失败')
  } finally {
    crawling.value = false
  }
}

const handleSpeedTest = async (source) => {
  source.testing = true
  try {
    await speedTest(source.id)
    await loadSources()
  } catch (err) {
    ElMessage.error('测速失败')
    source.testing = false
  }
}

const handleSpeedTestAll = async () => {
  speedTesting.value = true
  sources.value.forEach(s => s.testing = true)
  try {
    for (const source of sources.value) {
      try {
        await speedTest(source.id)
      } catch {}
    }
    await loadSources()
    ElMessage.success('全部测速完成')
  } catch {
    ElMessage.error('测速过程出错')
    await loadSources()
  } finally {
    speedTesting.value = false
  }
}

const handleDelete = async (source) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${source.name}" 吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteSource(source.id)
    ElMessage.success('已删除')
    loadSources()
  } catch {}
}

const getSpeedClass = (speed) => {
  if (!speed) return 'untested'
  if (speed < 1) return 'fast'
  if (speed < 3) return 'normal'
  return 'slow'
}
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
  padding: 100px 32px 24px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.source-count {
  font-size: 14px;
  color: #888;
}

.toolbar-right {
  display: flex;
  gap: 12px;
}

.toolbar-right .el-button {
  display: flex;
  align-items: center;
  gap: 6px;
}
.toolbar-right .el-button svg {
  width: 16px;
  height: 16px;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  transition: all 0.2s;
}
.source-item:hover {
  background: rgba(255,255,255,0.06);
}

.source-info {
  flex: 1;
  min-width: 0;
}

.source-name {
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-url {
  font-size: 12px;
  color: #666;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  min-width: 80px;
  justify-content: center;
}
.source-status.fast {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}
.source-status.normal {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}
.source-status.slow {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.source-status.untested {
  background: rgba(255,255,255,0.05);
  color: #666;
}
.speed-value {
  font-weight: 500;
}

.source-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}
.source-item:hover .source-actions {
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
  background: rgba(255,255,255,0.12);
  color: #fff;
}
.action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

@media (max-width: 600px) {
  .page-header {
    padding: 16px 20px;
  }
  .page-content {
    padding: 16px 20px;
  }
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .toolbar-right {
    justify-content: flex-end;
  }
  .source-actions {
    opacity: 1;
  }
}
</style>