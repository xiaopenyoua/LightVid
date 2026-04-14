<template>
  <div class="cast-scroll" v-if="cast.length">
    <div class="cast-header">
      <h3>导演 & 演员</h3>
    </div>
    <div class="cast-list">
      <div
        v-for="person in cast"
        :key="person.id || person.name"
        class="cast-item"
      >
        <div class="cast-avatar">
          <img v-if="person.profile_path" :src="person.profile_path" :alt="person.name" />
          <span v-else class="avatar-placeholder">🎭</span>
        </div>
        <p class="cast-name">{{ person.name }}</p>
        <p class="cast-role">{{ person.character || person.job }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  cast: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.cast-scroll {
  margin-top: 40px;
}
.cast-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.cast-header h3 {
  font-size: 14px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0;
}
.view-all {
  font-size: 13px;
  color: #666;
  cursor: pointer;
}
.view-all:hover {
  color: #fff;
}
.cast-list {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 10px;
  scrollbar-width: none;
}
.cast-list::-webkit-scrollbar {
  display: none;
}
.cast-item {
  flex-shrink: 0;
  width: 80px;
  text-align: center;
}
.cast-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 8px;
  background: #1a1a2e;
}
.cast-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 24px;
}
.cast-name {
  font-size: 13px;
  color: #fff;
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cast-role {
  font-size: 12px;
  color: #666;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>