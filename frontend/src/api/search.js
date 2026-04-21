import axios from 'axios'

const api = axios.create({
    baseURL: '/api'
})

/**
 * 获取支持的视频平台列表
 */
export function getPlatforms() {
    return api.get('/search/platforms')
}

/**
 * 获取可用的解析服务列表
 */
export function getParsers() {
    return api.get('/search/parsers')
}

/**
 * 搜索视频播放链接
 * @param {Object} params - 请求参数
 * @param {AbortSignal} params.signal - 可选的取消信号
 */
export function searchVideoLink(params, signal) {
    return api.post('/search/video-link', params, signal ? { signal } : {})
}

/**
 * 解析视频链接为 m3u8
 * @param {Object} params - 请求参数
 * @param {AbortSignal} params.signal - 可选的取消信号
 */
export function resolveVideo(params, signal) {
    return api.post('/search/resolve', params, signal ? { signal } : {})
}

/**
 * 清除视频链接缓存
 */
export function clearVideoCache(params) {
    return api.delete('/search/cache', { data: params })
}

/**
 * 继续预缓存未完成的集数
 */
export function continuePrecache(params) {
    return api.post('/search/continue-precache', params)
}
// ============ Parse Configs API（测速扩展）============

export const speedTestParser = (id) => api.post(`/parse-configs/speed-test/${id}`)
export const speedTestAllParsers = () => api.post('/parse-configs/speed-test-all')
