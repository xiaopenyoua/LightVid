import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

// Sources
export const getSources = (params) => api.get('/sources', { params })
export const createSource = (data) => api.post('/sources', data)
export const deleteSource = (id) => api.delete(`/sources/${id}`)
export const triggerCrawl = () => api.post('/sources/crawl')
export const speedTest = (id) => api.post(`/sources/speed-test/${id}`)

// Douban / TMDB Videos
export const getVideos = (params) => api.get('/douban/videos', { params })
export const getVideo = (tmdbId) => api.get(`/douban/videos/${tmdbId}`)
export const searchVideos = (q) => api.get('/douban/search', { params: { q } })
export const searchTmdb = (q, mediaType) => api.get('/douban/tmdb/search', { params: { q, media_type: mediaType } })
export const crawlVideo = (tmdbId, category) => api.post(`/douban/crawl/${tmdbId}`, null, { params: { category } })
export const getTrending = (mediaType) => api.get('/douban/trending', { params: { media_type: mediaType } })

// Play
export const getPlaySources = () => api.get('/play/sources')

// Parse Configs
export const getParseConfigs = () => api.get('/parse-configs')
export const createParseConfig = (data) => api.post('/parse-configs', data)
export const updateParseConfig = (id, data) => api.put(`/parse-configs/${id}`, data)
export const deleteParseConfig = (id) => api.delete(`/parse-configs/${id}`)

// History
export const getHistory = () => api.get('/history')
export const updateHistory = (tmdbId, data) => api.post('/history', { tmdb_id: tmdbId, ...data })
export const deleteHistory = (tmdbId) => api.delete(`/history/${tmdbId}`)

// Favorites
export const getFavorites = () => api.get('/favorites')
export const addFavorite = (tmdbId) => api.post('/favorites', { tmdb_id: tmdbId })
export const removeFavorite = (tmdbId) => api.delete(`/favorites/${tmdbId}`)
export const checkFavorite = (tmdbId) => api.get(`/favorites/check/${tmdbId}`)
