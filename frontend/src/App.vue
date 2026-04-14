<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
/* 全局覆盖 Element Plus 加载动画 */
.el-loading-mask {
  background-color: rgba(13, 13, 26, 0.9) !important;
}
.el-loading-spinner .circular {
  width: 40px;
  height: 40px;
}
.el-loading-spinner .path {
  stroke: #6366f1 !important;
  stroke-width: 2 !important;
}
.el-loading-spinner .el-loading-text {
  color: rgba(255, 255, 255, 0.8) !important;
}

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
</style>
