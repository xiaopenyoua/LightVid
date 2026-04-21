<template>
  <div class="page-container">
    <header class="page-header">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <h1>设置</h1>
    </header>

    <div class="page-content">
      <section class="settings-section">
        <h2 class="section-title">解析接口管理</h2>
        <el-button type="primary" @click="openAddDialog" class="add-btn">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
          添加解析接口
        </el-button>
        <div class="table-wrapper">
          <el-table v-loading="loading" :data="configs" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="base_url" label="地址" show-overflow-tooltip />
            <el-table-column prop="priority" label="优先级" width="100" align="center" />
            <el-table-column label="操作" width="150" align="center">
              <template #default="{ row }">
                <el-button size="small" @click="editConfig(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>
    </div>

    <el-dialog v-model="showAddDialog" :title="editing ? '编辑解析接口' : '添加解析接口'" destroy-on-close class="settings-dialog">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如：虾米解析" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.base_url" placeholder="如：https://jx.xmflv.com/?url=" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="form.priority" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getParseConfigs, createParseConfig, updateParseConfig, deleteParseConfig } from '../api'

const configs = ref([])
const showAddDialog = ref(false)
const editing = ref(null)
const loading = ref(false)
const saving = ref(false)
const form = ref({ name: '', base_url: '', priority: 0 })

onMounted(() => {
  loadConfigs()
})

const loadConfigs = async () => {
  loading.value = true
  try {
    const { data } = await getParseConfigs()
    configs.value = data
  } catch (err) {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  editing.value = null
  form.value = { name: '', base_url: '', priority: 0 }
  showAddDialog.value = true
}

const editConfig = (config) => {
  editing.value = config.id
  form.value = { ...config }
  showAddDialog.value = true
}

const handleSave = async () => {
  if (!form.value.name || !form.value.base_url) {
    ElMessage.warning('请填写名称和地址')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateParseConfig(editing.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createParseConfig(form.value)
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    loadConfigs()
  } catch (err) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await deleteParseConfig(id)
    ElMessage.success('删除成功')
    loadConfigs()
  } catch (err) {
    ElMessage.error('删除失败')
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

.page-content {
  padding: 100px 32px 24px;
}

.settings-section {
  background: rgba(255,255,255,0.03);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid rgba(255,255,255,0.06);
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  margin: 0 0 20px 0;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 20px;
}
.add-btn svg {
  width: 18px;
  height: 18px;
}

.table-wrapper {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table) {
  background: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255,255,255,0.03);
  color: #ccc;
}
:deep(.el-table th.el-table__cell) {
  background: rgba(255,255,255,0.03);
  color: #888;
  font-weight: 500;
}
:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
:deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(255,255,255,0.05);
}

@media (max-width: 600px) {
  .page-header {
    padding: 16px 20px;
  }
  .page-content {
    padding: 16px 20px;
  }
  .settings-section {
    padding: 16px;
  }
}
</style>