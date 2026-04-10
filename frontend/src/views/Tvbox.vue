<template>
  <div class="tvbox-page">
    <el-button type="primary" @click="handleCrawl" :loading="crawling">
      爬取 TV Box 源
    </el-button>
    <el-table v-loading="loading" :data="sources" style="width: 100%; margin-top: 20px">
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="url" label="地址" show-overflow-tooltip />
      <el-table-column prop="speed" label="速度(秒)" width="100">
        <template #default="{ row }">
          {{ row.speed ? row.speed + 's' : '未测速' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="handleSpeedTest(row.id)" :loading="row.testing">测速</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSources, triggerCrawl, speedTest, deleteSource } from '../api'

const sources = ref([])
const crawling = ref(false)
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

const handleSpeedTest = async (id) => {
  const source = sources.value.find(s => s.id === id)
  if (source) source.testing = true
  try {
    await speedTest(id)
    await loadSources()
    ElMessage.success('测速完成')
  } catch (err) {
    ElMessage.error('测速失败')
  }
}

const handleDelete = async (id) => {
  try {
    await deleteSource(id)
    await loadSources()
    ElMessage.success('删除成功')
  } catch (err) {
    ElMessage.error('删除失败')
  }
}
</script>
