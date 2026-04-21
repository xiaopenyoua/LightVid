<template>
  <Teleport to="body">
    <div v-if="visible" class="confirm-overlay" @click.self="handleCancel">
      <div class="confirm-dialog">
        <p class="confirm-title">{{ title }}</p>
        <p class="confirm-message">{{ message }}</p>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="handleCancel">取消</button>
          <button class="btn-confirm" :class="confirmClass" @click="handleConfirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '提示'
  },
  message: {
    type: String,
    default: '确定要执行此操作吗？'
  },
  confirmText: {
    type: String,
    default: '确定'
  },
  type: {
    type: String,
    default: 'danger' // 'danger' | 'primary'
  }
})

const emit = defineEmits(['confirm', 'cancel'])

const visible = ref(false)
let resolvePromise = null

const confirmClass = computed(() => props.type)

const show = () => {
  visible.value = true
  return new Promise((resolve) => {
    resolvePromise = resolve
  })
}

const handleConfirm = () => {
  visible.value = false
  if (resolvePromise) resolvePromise(true)
  emit('confirm')
}

const handleCancel = () => {
  visible.value = false
  if (resolvePromise) resolvePromise(false)
  emit('cancel')
}

defineExpose({ show })
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.confirm-dialog {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 24px 28px;
  width: 280px;
  text-align: center;
}

.confirm-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
}

.confirm-message {
  font-size: 14px;
  color: #999;
  margin: 0 0 24px;
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  gap: 12px;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}
.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.12);
}

.btn-confirm {
  background: #ef4444;
  color: #fff;
}
.btn-confirm:hover {
  background: #dc2626;
}
.btn-confirm.primary {
  background: #6366f1;
}
.btn-confirm.primary:hover {
  background: #4f46e5;
}
</style>