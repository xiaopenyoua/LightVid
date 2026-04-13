<template>
  <section class="hero-section">
    <div class="hero-slides">
      <div
        v-for="(item, index) in items"
        :key="item.tmdb_id"
        class="hero-slide"
        :class="{ active: currentIndex === index }"
        @click="handleClick(item)"
      >
        <img :src="item.backdrop_url" class="hero-bg" :alt="item.title" />
        <div class="hero-gradient"></div>
        <div class="hero-gradient-lr"></div>
      </div>
    </div>

    <!-- Hero Content -->
    <div class="hero-content" v-if="currentItem">
      <span class="hero-badge">🔥 热门推荐</span>
      <h1 class="hero-title">{{ currentItem.title }}</h1>
      <div class="hero-meta">
        <span class="rating">⭐ {{ currentItem.vote_average?.toFixed(1) }}</span>
        <span>{{ currentItem.release_date?.slice(0, 4) }}</span>
        <span>{{ currentItem.media_type === 'movie' ? '电影' : '剧集' }}</span>
        <span v-if="currentItem.runtime">{{ formatRuntime(currentItem.runtime) }}</span>
      </div>
      <p class="hero-desc">{{ currentItem.overview }}</p>
      <div class="hero-actions">
        <button class="btn-primary" @click.stop="handlePlay(currentItem)">
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          立即播放
        </button>
        <button class="btn-secondary" @click.stop="handleFavorite(currentItem)">
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          收藏
        </button>
      </div>
    </div>

    <!-- Carousel Dots -->
    <div class="carousel-dots">
      <div
        v-for="(item, index) in items"
        :key="item.tmdb_id"
        class="carousel-dot"
        :class="{ active: currentIndex === index }"
        @click="currentIndex = index"
      >
        <div class="dot-line"></div>
        <span class="dot-title">{{ item.title }}</span>
      </div>
    </div>

    <!-- Scroll Indicator -->
    <div class="scroll-indicator">
      <div class="mouse"><div class="wheel"></div></div>
      <span>滚动探索分类</span>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select', 'play', 'favorite'])

const currentIndex = ref(0)
let timer = null

const currentItem = computed(() => props.items[currentIndex.value])

const formatRuntime = (minutes) => {
  if (!minutes) return null
  if (Array.isArray(minutes)) minutes = minutes[0]
  if (!minutes) return null
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

const handleClick = (item) => emit('select', item)
const handlePlay = (item) => emit('play', item)
const handleFavorite = (item) => emit('favorite', item)

const startAutoPlay = () => {
  timer = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % props.items.length
  }, 5000)
}

const stopAutoPlay = () => {
  if (timer) clearInterval(timer)
}

onMounted(() => {
  if (props.items.length > 1) startAutoPlay()
})

onUnmounted(() => stopAutoPlay())
</script>

<style scoped>
.hero-section {
  position: relative;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background: #000;
}
.hero-slides { position: absolute; inset: 0; }
.hero-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 1.2s ease;
  cursor: pointer;
}
.hero-slide.active { opacity: 1; }
.hero-bg {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.55);
}
.hero-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(10,10,15,0.2) 0%, rgba(10,10,15,0.05) 30%, rgba(10,10,15,0.5) 70%, rgba(10,10,15,1) 100%);
}
.hero-gradient-lr {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(10,10,15,0.9) 0%, rgba(10,10,15,0.3) 50%, rgba(10,10,15,0.1) 100%);
}
.hero-content {
  position: absolute;
  bottom: 18%;
  left: 80px;
  max-width: 520px;
  z-index: 10;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 8px 18px;
  border-radius: 24px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 20px;
}
.hero-title {
  font-size: 52px;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: 16px;
  text-shadow: 0 4px 30px rgba(0,0,0,0.5);
}
.hero-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 14px;
  color: rgba(255,255,255,0.7);
}
.hero-meta .rating { color: #fbbf24; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.hero-desc {
  font-size: 15px;
  line-height: 1.7;
  color: rgba(255,255,255,0.8);
  margin-bottom: 28px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.hero-actions { display: flex; gap: 12px; }
.btn-primary {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  padding: 14px 30px;
  border-radius: 30px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.btn-primary:hover {
  transform: scale(1.04);
  box-shadow: 0 15px 40px rgba(99, 102, 241, 0.45);
}
.btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255,255,255,0.2);
  padding: 14px 24px;
  border-radius: 30px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-secondary:hover { background: rgba(255,255,255,0.25); }

/* Carousel Dots */
.carousel-dots {
  position: absolute;
  bottom: 50px;
  right: 60px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}
.carousel-dot {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 0;
}
.carousel-dot .dot-line {
  width: 24px;
  height: 2px;
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
  transition: all 0.3s;
}
.carousel-dot .dot-title {
  font-size: 13px;
  color: rgba(255,255,255,0.5);
  transition: all 0.3s;
  opacity: 0;
  transform: translateX(-10px);
}
.carousel-dot:hover .dot-title,
.carousel-dot.active .dot-title {
  opacity: 1;
  transform: translateX(0);
}
.carousel-dot.active .dot-line {
  width: 48px;
  background: #fff;
}
.carousel-dot:hover .dot-line { background: rgba(255,255,255,0.6); }

/* Scroll Indicator */
.scroll-indicator {
  position: absolute;
  bottom: 40px;
  right: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  z-index: 10;
  color: rgba(255,255,255,0.5);
  font-size: 12px;
  animation: scrollBounce 2s infinite;
}
@keyframes scrollBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(10px); }
}
.scroll-indicator .mouse {
  width: 26px;
  height: 40px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 13px;
  position: relative;
}
.scroll-indicator .wheel {
  width: 4px;
  height: 8px;
  background: rgba(255,255,255,0.5);
  border-radius: 2px;
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
}
</style>
