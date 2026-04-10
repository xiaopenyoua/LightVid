import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/search', component: () => import('../views/Search.vue') },
  { path: '/video/:media_type/:id', component: () => import('../views/VideoDetail.vue') },
  { path: '/video/:media_type/:id/play', component: () => import('../views/Play.vue') },
  { path: '/tvbox', component: () => import('../views/Tvbox.vue') },
  { path: '/history', component: () => import('../views/History.vue') },
  { path: '/favorites', component: () => import('../views/Favorites.vue') },
  { path: '/settings', component: () => import('../views/Settings.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
