<template>
  <div class="poster-wall">
    <div v-for="video in videos" :key="video.id" class="poster-item" @click="$emit('select', video)">
      <img :src="video.poster_url" :alt="video.title" loading="lazy" />
      <div class="poster-info">
        <span class="title">{{ video.title }}</span>
        <span class="rating" v-if="video.rating">{{ video.rating }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  videos: Array
})
defineEmits(['select'])
</script>

<style scoped>
.poster-wall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
  padding: 20px;
}
.poster-item {
  cursor: pointer;
  transition: transform 0.2s;
}
.poster-item:hover {
  transform: scale(1.05);
}
.poster-item img {
  width: 100%;
  border-radius: 8px;
}
.poster-info {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}
.title {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rating {
  color: #f5a623;
}
</style>
