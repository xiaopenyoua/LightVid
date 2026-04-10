<template>
  <div id="app">
    <el-menu mode="horizontal" :router="true">
      <el-menu-item index="/">首页</el-menu-item>
      <el-menu-item index="/tvbox">TV Box</el-menu-item>
      <el-menu-item index="/history">继续观看</el-menu-item>
      <el-menu-item index="/favorites">我的收藏</el-menu-item>
      <el-menu-item index="/settings">设置</el-menu-item>
    </el-menu>
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  background: #0d0d1a;
  min-height: 100vh;
  color: #fff;
}
body {
  margin: 0;
  background: #0d0d1a;
}
/* 暗色主题覆盖 */
.el-menu {
  background: #1a1a2e !important;
  border-bottom: 1px solid #333;
}
.el-menu-item {
  color: #b8c2ce !important;
}
.el-menu-item:hover, .el-menu-item.is-active {
  background: #252540 !important;
  color: #409eff !important;
}
</style>
