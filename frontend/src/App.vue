<template>
  <div id="app">
    <nav class="nav">
      <router-link to="/" class="nav-logo">轻影</router-link>
      <div class="nav-actions">
        <input type="text" class="nav-search" placeholder="搜索电影、剧集...">
        <button class="nav-btn">👤</button>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
body {
  margin: 0;
  background: #0d0d1a;
}
#app {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  background: #0d0d1a;
  min-height: 100vh;
  color: #fff;
}
/* 顶部导航栏 */
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
  padding: 24px 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(180deg, rgba(10,10,15,0.8) 0%, transparent 100%);
}
.nav-logo {
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-decoration: none;
}
.nav-links {
  display: flex;
  gap: 8px;
  list-style: none;
}
.nav-links a {
  color: rgba(255,255,255,0.65);
  text-decoration: none;
  padding: 10px 20px;
  border-radius: 24px;
  font-size: 14px;
  transition: all 0.2s;
}
.nav-links a:hover {
  color: #fff;
  background: rgba(255,255,255,0.08);
}
.nav-links a.active,
.nav-links a.router-link-active {
  color: #fff;
  background: rgba(255,255,255,0.12);
}
.nav-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
.nav-search {
  width: 200px;
  height: 40px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 20px;
  padding: 0 20px;
  color: #fff;
  font-size: 14px;
}
.nav-search::placeholder {
  color: rgba(255,255,255,0.4);
}
.nav-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 16px;
}
</style>
