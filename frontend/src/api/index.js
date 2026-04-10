import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

// ============ Videos API（替换原来的 /douban）============

// 首页全量数据
export const getHome = () => api.get('/videos/home')

// 类型列表
export const getGenres = () => api.get('/videos/genres')

// 电影列表（实时 TMDB discover）
export const getMovies = (params) => api.get('/videos/movies', { params })

// 剧集列表（实时 TMDB discover）
export const getTvShows = (params) => api.get('/videos/tv', { params })

// 电影/剧集详情（实时 TMDB）
export const getVideoDetail = (mediaType, tmdbId) => api.get(`/videos/${mediaType}/${tmdbId}`)

// 剧集某季详情
export const getSeasonDetail = (tmdbId, season) => api.get(`/videos/tv/${tmdbId}/seasons/${season}`)

// 搜索
export const searchVideos = (q, page) => api.get('/videos/search', { params: { q, page } })

// ============ Sources API（保持不变）============

export const getSources = (params) => api.get('/sources', { params })
export const createSource = (data) => api.post('/sources', data)
export const deleteSource = (id) => api.delete(`/sources/${id}`)
export const triggerCrawl = () => api.post('/sources/crawl')
export const speedTest = (id) => api.post(`/sources/speed-test/${id}`)

// ============ Play API（保持不变）============

export const getPlaySources = () => api.get('/play/sources')

// ============ Parse Configs API（保持不变）============

export const getParseConfigs = () => api.get('/parse-configs')
export const createParseConfig = (data) => api.post('/parse-configs', data)
export const updateParseConfig = (id, data) => api.put(`/parse-configs/${id}`, data)
export const deleteParseConfig = (id) => api.delete(`/parse-configs/${id}`)

// ============ History API（保持不变）============

export const getHistory = () => api.get('/history')
export const updateHistory = (tmdbId, data) => api.post('/history', { tmdb_id: tmdbId, ...data })
export const deleteHistory = (tmdbId) => api.delete(`/history/${tmdbId}`)

// ============ Favorites API（保持不变）============

export const getFavorites = () => api.get('/favorites')
export const addFavorite = (tmdbId) => api.post('/favorites', { tmdb_id: tmdbId })
export const removeFavorite = (tmdbId) => api.delete(`/favorites/${tmdbId}`)
export const checkFavorite = (tmdbId) => api.get(`/favorites/check/${tmdbId}`)
