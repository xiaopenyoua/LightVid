<template>
  <div class="page-container">
    <header class="page-header">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <h1>解析服务</h1>
      <el-button type="primary" @click="handleSpeedTestAll" :loading="speedingAll" class="header-btn">
        全部测速
      </el-button>
    </header>

    <div class="page-content">
      <div v-if="loading" class="loading-center">
        <span class="loading-text">加载中...</span>
      </div>
      <div v-else class="parser-list">
        <div
          v-for="(config, index) in configs"
          :key="config.id"
          class="parser-item"
        >
          <span class="parser-index">{{ index + 1 }}</span>
          <span class="parser-name">{{ config.name }}</span>
          <a :href="config.base_url" target="_blank" class="parser-url">{{ formatUrl(config.base_url) }}</a>
          <span class="parser-status" :class="getStatusClass(config)">
            <template v-if="config.speedTesting || config.testing">测速中...</template>
            <template v-else>{{ formatLatency(config.latency1) }} / {{ formatLatency(config.latency2) }}</template>
          </span>
          <div class="parser-actions">
            <button class="action-btn" @click="handleCopy(config.base_url)" title="复制链接">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
            </button>
            <button
              class="action-btn primary"
              @click="handleSpeedTest(config)"
              :disabled="config.speedTesting"
              title="测速"
            >
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 2.05v2.02c3.95.49 7 3.85 7 7.93 0 3.21-1.92 6-4.72 7.28l-1.02-1.78c2.04-.94 3.44-2.89 3.44-5.5 0-3.04-2.18-5.6-5.04-6.17v-.02C9.02 6.73 7 8.79 7 11.2c0 2.74 1.95 5.02 4.53 5.54l-1.03 1.78C7.44 17.58 5 14.47 5 11.2c0-4.31 3.86-7.81 8.68-7.98V2.05c-.94.19-1.78.64-2.45 1.27L12 2H8l.45 4.32c.67-.63 1.51-1.08 2.45-1.27z"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getParseConfigs } from '../api'
import { speedTestParser, speedTestAllParsers } from '../api/search'

const configs = ref([])
const loading = ref(false)
const speedingAll = ref(false)
let refreshTimer = null

onMounted(() => {
  loadConfigs()
})

const loadConfigs = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const { data } = await getParseConfigs()
    configs.value = data.map(c => ({ ...c, speedTesting: c.testing || false }))
  } catch (err) {
    if (!silent) ElMessage.error('加载解析服务失败')
  } finally {
    if (!silent) loading.value = false
  }
}

const formatLatency = (latency) => {
  if (latency === null || latency === undefined) return '✗'
  return `${latency}s`
}

const formatUrl = (url) => {
  return url
}

const getStatusClass = (config) => {
  if (config.testing || config.speedTesting) return 'testing'
  // 两轮都失败
  if (config.latency1 === null && config.latency2 === null) return 'failed'
  // 第二轮失败（第一轮可能通过）
  if (config.latency2 === null) return 'failed'
  // 根据第二轮延迟判断颜色
  const lat = config.latency2
  if (lat <= 3) return 'fast'
  if (lat <= 8) return 'medium'
  return 'slow'
}

const handleCopy = async (url) => {
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

const handleSpeedTest = async (config) => {
  config.speedTesting = true
  try {
    const { data } = await speedTestParser(config.id)
    config.latency1 = data.latency1
    config.latency2 = data.latency2
    ElMessage.success('测速完成')
  } catch (err) {
    ElMessage.error('测速失败')
  } finally {
    config.speedTesting = false
  }
}

const handleSpeedTestAll = async () => {
  speedingAll.value = true
  configs.value.forEach(c => c.speedTesting = true)

  try {
    await speedTestAllParsers()
    ElMessage.success('测速任务已启动')

    // 启动定时刷新，每 3 秒获取最新状态
    if (refreshTimer) clearInterval(refreshTimer)
    refreshTimer = setInterval(async () => {
      await loadConfigs(true)
      // 如果所有测试都完成，停止定时刷新
      const allDone = configs.value.every(c => !c.testing)
      if (allDone) {
        clearInterval(refreshTimer)
        refreshTimer = null
        speedingAll.value = false
        configs.value.forEach(c => c.speedTesting = false)
      }
    }, 3000)
  } catch (err) {
    ElMessage.error('启动测速失败')
    speedingAll.value = false
    configs.value.forEach(c => c.speedTesting = false)
  }
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

.header-btn {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
}

.page-content {
  padding: 110px 32px 24px;
  max-width: 900px;
  margin: 0 auto;
}

.loading-center {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.loading-text {
  color: #888;
  font-size: 14px;
}

.parser-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.parser-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  transition: all 0.2s;
}

.parser-item > * {
  flex-shrink: 0;
}

.parser-item > .parser-actions {
  margin-left: auto;
}

.parser-item:hover {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.1);
}

.parser-index {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(99, 102, 241, 0.2);
  color: #8b5cf6;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.parser-name {
  width: 100px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.parser-url {
  flex: 1;
  font-size: 13px;
  color: #6366f1;
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 150px;
}

.parser-url:hover {
  text-decoration: underline;
}

.parser-status {
  width: 100px;
  text-align: center;
  font-size: 13px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #888;
  flex-shrink: 0;
}

.parser-status.testing {
  color: #6366f1;
}

.parser-status.fast {
  color: #22c55e;
}

.parser-status.medium {
  color: #eab308;
}

.parser-status.slow {
  color: #f97316;
}

.parser-status.failed {
  color: #ef4444;
}

.parser-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

.action-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #fff;
}

.action-btn.primary {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
  color: #8b5cf6;
}

.action-btn.primary:hover {
  background: rgba(99, 102, 241, 0.25);
  color: #a78bfa;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 700px) {
  .page-header {
    padding: 0 20px;
    height: 70px;
  }
  .page-header h1 {
    padding-right: 90px;
    font-size: 18px;
  }
  .page-content {
    padding: 90px 16px 16px;
  }
  .parser-item {
    padding: 12px 14px;
    gap: 10px;
    flex-wrap: wrap;
  }
  .parser-name {
    width: 80px;
  }
  .parser-status {
    width: 80px;
    font-size: 12px;
  }
  .parser-url {
    order: 3;
    flex: 1 1 100%;
    font-size: 11px;
    padding-top: 4px;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
}
</style>