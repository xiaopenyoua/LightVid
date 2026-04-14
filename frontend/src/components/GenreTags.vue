<template>
  <div class="genre-tags">
    <span
      v-for="(genre, index) in genreList"
      :key="index"
      class="tag"
    >
      {{ genre }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  genres: {
    type: [Array, String],
    default: () => []
  }
})

const genreList = computed(() => {
  if (Array.isArray(props.genres)) {
    return props.genres
  }
  if (typeof props.genres === 'string') {
    return props.genres.split(',').filter(g => g.trim())
  }
  return []
})
</script>

<style scoped>
.genre-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.tag {
  padding: 6px 14px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 16px;
  font-size: 13px;
  color: #a5b4fc;
  cursor: pointer;
  transition: all 0.2s;
}
.tag:hover {
  background: rgba(99, 102, 241, 0.25);
  border-color: rgba(99, 102, 241, 0.5);
}
</style>