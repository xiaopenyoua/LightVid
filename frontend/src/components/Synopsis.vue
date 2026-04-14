<template>
  <div class="synopsis">
    <p class="synopsis-text" :class="{ expanded: isExpanded }" ref="textRef">
      {{ text || '暂无简介' }}
    </p>
    <button
      v-if="needsTruncate"
      class="expand-btn"
      @click="isExpanded = !isExpanded"
    >
      {{ isExpanded ? '收起 ▲' : '展开全部 ▼' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  text: {
    type: String,
    default: ''
  }
})

const isExpanded = ref(false)
const needsTruncate = ref(false)
const textRef = ref(null)

const checkTruncate = () => {
  if (textRef.value) {
    needsTruncate.value = textRef.value.scrollHeight > textRef.value.clientHeight
  }
}

onMounted(() => {
  setTimeout(checkTruncate, 100)
})

watch(() => props.text, () => {
  setTimeout(checkTruncate, 100)
})
</script>

<style scoped>
.synopsis {
  margin-bottom: 24px;
}
.synopsis-text {
  font-size: 14px;
  line-height: 1.7;
  color: #ccc;
  margin: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  transition: all 0.3s;
}
.synopsis-text.expanded {
  display: block;
  -webkit-line-clamp: unset;
}
.expand-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 13px;
  cursor: pointer;
  padding: 8px 0;
  transition: color 0.2s;
}
.expand-btn:hover {
  color: #fff;
}
</style>