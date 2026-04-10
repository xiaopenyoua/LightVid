<template>
  <div class="carousel" @mouseenter="stopAutoPlay" @mouseleave="startAutoPlay">
    <div class="carousel-inner" :style="{ transform: `translateX(-${currentIndex * 100}%)` }">
      <div v-for="(item, index) in items" :key="index" class="carousel-item" @click="$emit('select', item)">
        <img :src="item.backdrop_url || item.poster_url" :alt="item.title" />
        <div class="carousel-caption">
          <h2>{{ item.title }}</h2>
          <p>{{ item.overview?.slice(0, 100) }}...</p>
        </div>
      </div>
    </div>
    <div class="carousel-indicators">
      <span
        v-for="(_, index) in items"
        :key="index"
        :class="{ active: index === currentIndex }"
        @click="goTo(index)"
      />
    </div>
    <button class="carousel-prev" @click="prev">&#10094;</button>
    <button class="carousel-next" @click="next">&#10095;</button>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  autoPlay: {
    type: Boolean,
    default: true
  },
  interval: {
    type: Number,
    default: 5000
  }
})

const emit = defineEmits(['select'])

const currentIndex = ref(0)
let timer = null

const goTo = (index) => {
  currentIndex.value = index
}

const next = () => {
  if (props.items.length > 0) {
    currentIndex.value = (currentIndex.value + 1) % props.items.length
  }
}

const prev = () => {
  if (props.items.length > 0) {
    currentIndex.value = (currentIndex.value - 1 + props.items.length) % props.items.length
  }
}

const startAutoPlay = () => {
  if (props.autoPlay && props.items.length > 1) {
    timer = setInterval(next, props.interval)
  }
}

const stopAutoPlay = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onMounted(startAutoPlay)
onBeforeUnmount(stopAutoPlay)

watch(() => props.items, () => {
  if (currentIndex.value >= props.items.length && props.items.length > 0) {
    currentIndex.value = 0
  }
  startAutoPlay()
})
</script>

<style scoped>
.carousel {
  position: relative;
  width: 100%;
  height: 400px;
  overflow: hidden;
  border-radius: 8px;
}
.carousel-inner {
  display: flex;
  height: 100%;
  transition: transform 0.5s ease;
}
.carousel-item {
  min-width: 100%;
  height: 100%;
  position: relative;
  cursor: pointer;
}
.carousel-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.carousel-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  color: white;
}
.carousel-caption h2 {
  margin: 0 0 8px 0;
}
.carousel-caption p {
  margin: 0;
  font-size: 14px;
  color: #ccc;
}
.carousel-indicators {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}
.carousel-indicators span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  cursor: pointer;
}
.carousel-indicators span.active {
  background: white;
}
.carousel-prev, .carousel-next {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0,0,0,0.5);
  color: white;
  border: none;
  padding: 12px 16px;
  cursor: pointer;
  font-size: 18px;
}
.carousel-prev { left: 10px; }
.carousel-next { right: 10px; }
</style>
