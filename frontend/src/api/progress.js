import axios from 'axios'

const api = axios.create({
    baseURL: '/api'
})

/**
 * 获取播放进度
 * @param {number} tmdbId - TMDB ID
 * @param {number|null} season - 季数（电影为 null）
 * @param {number|null} episode - 集数（电影为 null）
 */
export function getProgress(tmdbId, season = null, episode = null) {
    const params = { tmdb_id: tmdbId }
    if (season !== null) params.season = season
    if (episode !== null) params.episode = episode
    return api.get('/progress', { params })
}

/**
 * 保存播放进度
 * @param {number} tmdbId - TMDB ID
 * @param {number|null} season - 季数
 * @param {number|null} episode - 集数
 * @param {number} currentTime - 当前播放位置（秒）
 * @param {number} duration - 视频总时长（秒）
 * @param {string} mediaType - 媒体类型 "movie" 或 "tv"
 */
export function saveProgress(tmdbId, season, episode, currentTime, duration, mediaType) {
    return api.post('/progress', {
        tmdb_id: tmdbId,
        season: season,
        episode: episode,
        current_time: currentTime,
        duration: duration,
        media_type: mediaType
    })
}

/**
 * 获取影片所有剧集的进度
 * @param {number} tmdbId - TMDB ID
 */
export function getProgressList(tmdbId) {
    return api.get(`/progress/list/${tmdbId}`)
}