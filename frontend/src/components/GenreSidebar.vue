<template>
  <aside class="genre-sidebar">
    <div class="sidebar-header">
      <h2>分类浏览</h2>
    </div>
    <div class="genre-list">
      <!-- 固定导航入口 -->
      <div
        v-for="nav in fixedNav"
        :key="nav.key"
        class="genre-item"
        :class="{ active: activeKey === nav.key }"
        @click="handleNavClick(nav)"
      >
        <div class="genre-icon">{{ nav.icon }}</div>
        <div class="genre-info">
          <div class="genre-name">{{ nav.name }}</div>
        </div>
      </div>

      <!-- 真实类型列表 -->
      <div
        v-for="genre in genres"
        :key="genre.tmdb_id"
        class="genre-item"
        :class="{ active: activeKey === `genre-${genre.tmdb_id}` }"
        @click="handleGenreClick(genre)"
      >
        <div class="genre-icon">{{ getGenreIcon(genre.name) }}</div>
        <div class="genre-info">
          <div class="genre-name">{{ genre.name }}</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  genres: {
    type: Array,
    default: () => []  // [{ tmdb_id, name, media_type }]
  }
})

const emit = defineEmits(['select'])  // select(genre { tmdb_id, name, media_type })

const fixedNav = [
  { key: 'hot', name: '热门推荐', icon: '🔥', media_type: null },
  { key: 'movie', name: '电影', icon: '🎬', media_type: 'movie' },
  { key: 'tv', name: '剧集', icon: '📺', media_type: 'tv' },
  { key: 'variety', name: '综艺', icon: '🎭', media_type: null },
  { key: 'anime', name: '动漫', icon: '🦸', media_type: null },
]

const activeKey = ref('hot')

const handleNavClick = (nav) => {
  activeKey.value = nav.key
  emit('select', { key: nav.key, name: nav.name, media_type: nav.media_type, tmdb_id: null })
}

const handleGenreClick = (genre) => {
  activeKey.value = `genre-${genre.tmdb_id}`
  emit('select', { key: `genre-${genre.tmdb_id}`, name: genre.name, media_type: genre.media_type, tmdb_id: genre.tmdb_id })
}

const ICON_MAP = {
  '科幻': '🚀', '爱情': '💕', '动作': '🔫', '奇幻': '🗡️',
  '恐怖': '👻', '喜剧': '😂', '剧情': '📜', '悬疑': '🔎',
  '冒险': '🌍', '动画': '🎨', '纪录片': '📽️', '音乐': '🎵',
  '战争': '⚔️', '犯罪': '🚔', '历史': '🏛️', '家庭': '👨‍👩‍👧',
}

const getGenreIcon = (name) => ICON_MAP[name] || '🎬'
</script>

<style scoped>
.genre-sidebar {
  width: 280px;
  height: 100vh;
  position: sticky;
  top: 0;
  background: linear-gradient(180deg, #12121f 0%, #0d0d18 100%);
  border-right: 1px solid rgba(255,255,255,0.06);
  padding: 100px 0 40px;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 0 32px;
  margin-bottom: 24px;
}
.sidebar-header h2 {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 1px;
}
.genre-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}
.genre-list::-webkit-scrollbar { width: 4px; }
.genre-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
.genre-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  margin-bottom: 4px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}
.genre-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 60%;
  background: linear-gradient(180deg, #6366f1, #a855f7);
  border-radius: 2px;
  transition: transform 0.25s;
}
.genre-item:hover {
  background: rgba(255,255,255,0.06);
  transform: scale(1.03);
}
.genre-item.active {
  background: rgba(99, 102, 241, 0.15);
}
.genre-item.active::before {
  transform: translateY(-50%) scaleY(1);
}
.genre-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: transform 0.25s;
}
.genre-item:hover .genre-icon { transform: scale(1.15); }
.genre-item.active .genre-icon {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}
.genre-info { flex: 1; }
.genre-name {
  font-size: 15px;
  font-weight: 500;
  color: rgba(255,255,255,0.85);
  transition: color 0.2s;
}
.genre-item:hover .genre-name,
.genre-item.active .genre-name { color: #fff; }
</style>
