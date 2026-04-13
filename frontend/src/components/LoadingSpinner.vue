<template>
  <div class="loading-spinner" :style="{ width: size + 'px', height: size + 'px' }">
    <div class="spinner-ring">
      <div class="ring"></div>
      <div class="ring"></div>
      <div class="ring"></div>
    </div>
    <div class="film-icon">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 4H8V8H4V4Z" fill="currentColor"/>
        <path d="M16 4H20V8H16V4Z" fill="currentColor"/>
        <path d="M4 16H8V20H4V16Z" fill="currentColor"/>
        <path d="M16 16H20V20H16V16Z" fill="currentColor"/>
        <path d="M10 4V20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="M14 4V20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="M4 10H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="M4 14H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
defineProps({
  size: {
    type: Number,
    default: 60
  }
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  animation: rotate 2s linear infinite;
}

.ring {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid transparent;
  transform: translate(-50%, -50%);
}

.ring:nth-child(1) {
  border-top-color: #6366f1;
  animation: ring-1 1.5s ease-in-out infinite;
}

.ring:nth-child(2) {
  width: 80%;
  height: 80%;
  border-right-color: #8b5cf6;
  animation: ring-2 1.5s ease-in-out infinite 0.15s;
}

.ring:nth-child(3) {
  width: 60%;
  height: 60%;
  border-bottom-color: #a855f7;
  animation: ring-3 1.5s ease-in-out infinite 0.3s;
}

.film-icon {
  position: relative;
  z-index: 1;
  width: 24px;
  height: 24px;
  color: rgba(255, 255, 255, 0.9);
  animation: pulse 2s ease-in-out infinite;
}

.film-icon svg {
  width: 100%;
  height: 100%;
}

@keyframes rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes ring-1 {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 0.3; }
}

@keyframes ring-2 {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.2; }
}

@keyframes ring-3 {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.1; }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(0.9); opacity: 0.6; }
}
</style>