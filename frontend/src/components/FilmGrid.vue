<template>
  <div class="film-grid">
    <div
      v-for="item in items"
      :key="item.tmdb_id"
      class="film-card"
      @click="handleClick(item)"
    >
      <div class="poster-wrap">
        <img :src="item.poster_url || 'https://via.placeholder.com/300x450?text=No+Image'" :alt="item.title" />
        <div class="hover-overlay">
          <div class="play-btn" @click.stop="handlePlay(item)">
            <svg width="20" height="20" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </div>
          <div class="film-info">
            <div class="rating">⭐ {{ item.vote_average?.toFixed(1) }}</div>
            <div class="tags" v-if="item.genre_ids">
              <span class="tag" v-for="gid in (item.genre_ids.split(',').slice(0, 2))" :key="gid">
                {{ genreName(gid) }}
              </span>
            </div>
          </div>
        </div>
        <div class="score-badge">⭐ {{ item.vote_average?.toFixed(1) }}</div>
      </div>
      <div class="film-title">{{ item.title }}</div>
      <div class="film-meta">{{ item.release_date?.slice(0, 4) }} · {{ item.media_type === 'movie' ? '电影' : '剧集' }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  genres: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select', 'play'])

const handleClick = (item) => emit('select', item)
const handlePlay = (item) => emit('play', item)

const genreName = (gid) => {
  const g = props.genres.find(g => g.tmdb_id === Number(gid))
  return g ? g.name : ''
}
</script>

<style scoped>
.film-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 24px;
}
.film-card { cursor: pointer; }
.poster-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 12px;
  background: linear-gradient(145deg, #1e1e30, #252540);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s;
}
.film-card:hover .poster-wrap {
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 24px 48px rgba(0,0,0,0.5);
}
.poster-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.hover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 30%, rgba(0,0,0,0.92) 100%);
  opacity: 0;
  transition: opacity 0.3s;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 16px;
}
.film-card:hover .hover-overlay { opacity: 1; }
.play-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  align-self: center;
  transform: scale(0.7);
  opacity: 0;
  transition: all 0.3s 0.1s;
  cursor: pointer;
}
.film-card:hover .play-btn {
  transform: scale(1);
  opacity: 1;
}
.play-btn svg { fill: #1a1a2e; margin-left: 3px; }
.film-info {
  transform: translateY(10px);
  opacity: 0;
  transition: all 0.3s 0.15s;
}
.film-card:hover .film-info {
  transform: translateY(0);
  opacity: 1;
}
.rating {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #fbbf24;
  margin-bottom: 6px;
}
.tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag {
  font-size: 11px;
  color: rgba(255,255,255,0.75);
  background: rgba(255,255,255,0.15);
  padding: 3px 8px;
  border-radius: 8px;
}
.score-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(10px);
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #fbbf24;
}
.film-title {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}
.film-meta {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}
</style>
