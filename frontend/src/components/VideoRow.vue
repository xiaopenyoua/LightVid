<template>
  <div class="video-row">
    <h3 class="row-title">{{ title }}</h3>
    <div class="row-content" ref="rowRef" @mousedown="startDrag" @mousemove="onDrag" @mouseup="endDrag" @mouseleave="endDrag">
      <div v-for="item in items" :key="`${item.tmdb_id}-${item.season_number || 0}`" class="video-card" @click="$emit('select', item)">
        <div class="card-poster">
          <img :src="item.poster_url" :alt="item.title" loading="lazy" />
          <span v-if="item.season_number" class="season-badge">第{{ item.season_number }}季</span>
          <span class="rating" v-if="item.vote_average">{{ item.vote_average.toFixed(1) }}</span>
        </div>
        <p class="card-title">{{ item.title }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  title: String,
  items: Array
})

defineEmits(['select'])

const rowRef = ref(null)
const isDragging = ref(false)
const startX = ref(0)
const scrollLeft = ref(0)

const startDrag = (e) => {
  isDragging.value = true
  startX.value = e.pageX - rowRef.value.offsetLeft
  scrollLeft.value = rowRef.value.scrollLeft
  rowRef.value.style.cursor = 'grabbing'
}

const onDrag = (e) => {
  if (!isDragging.value) return
  e.preventDefault()
  const x = e.pageX - rowRef.value.offsetLeft
  const walk = (x - startX.value) * 2
  rowRef.value.scrollLeft = scrollLeft.value - walk
}

const endDrag = () => {
  isDragging.value = false
  if (rowRef.value) rowRef.value.style.cursor = 'grab'
}
</script>

<style scoped>
.video-row {
  margin-bottom: 30px;
}
.row-title {
  padding: 0 20px;
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: 600;
}
.row-content {
  display: flex;
  gap: 16px;
  padding: 10px 20px;
  overflow-x: auto;
  scroll-behavior: smooth;
  cursor: grab;
  -webkit-overflow-scrolling: touch;
}
.row-content::-webkit-scrollbar {
  display: none;
}
.video-card {
  min-width: 180px;
  max-width: 180px;
  cursor: pointer;
}
.card-poster {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}
.card-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s;
}
.video-card:hover .card-poster img {
  transform: scale(1.05);
}
.season-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0,0,0,0.8);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.rating {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0,0,0,0.8);
  color: #f5a623;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}
.card-title {
  margin: 8px 0 0 0;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
