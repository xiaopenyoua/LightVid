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
 */
export function searchVideoLink(params) {
    return api.post('/search/video-link', params)
}

/**
 * 解析视频链接为 m3u8
 */
export function resolveVideo(params) {
    return api.post('/search/resolve', params)
}