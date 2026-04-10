<template>
  <div class="settings">
    <h2>解析接口管理</h2>
    <el-button type="primary" @click="openAddDialog">添加解析接口</el-button>
    <el-table v-loading="loading" :data="configs" style="width: 100%; margin-top: 20px">
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="base_url" label="地址" show-overflow-tooltip />
      <el-table-column prop="priority" label="优先级" width="100" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="editConfig(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showAddDialog" :title="editing ? '编辑' : '添加'" destroy-on-close>
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
