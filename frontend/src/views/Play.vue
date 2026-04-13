<template>
  <div class="play-page" v-if="video">
    <div class="play-left">
      <h2>{{ video.title }}</h2>
      <img :src="video.poster_url" class="poster" />
      <p>{{ video.summary }}</p>
    </div>
    <div class="play-right">
      <div class="player-container">
        <iframe
          v-if="currentUrl"
          :src="currentUrl"
          frameborder="0"
          allowfullscreen
          class="player-iframe"
        ></iframe>
        <div v-else class="no-source">选择下方源进行播放</div>
      </div>
      <div class="parse-selector" v-if="parseConfigs.length > 0">
        <el-select v-model="selectedParseConfig" placeholder="选择解析接口" style="width: 200px">
          <el-option v-for="config in parseConfigs" :key="config.id" :label="config.name" :value="config.id" />
        </el-select>
      </div>
      <div class="source-list">
        <h3>播放源</h3>
        <div v-for="source in sources" :key="source.id" class="source-item">
          <span class="source-name">{{ source.name }}</span>
          <span class="source-speed" v-if="source.speed">{{ source.speed }}s</span>
          <span class="source-speed testing" v-else>未测速</span>
          <el-button size="small" @click="playSource(source)">播放</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getVideoDetail, getPlaySources, getParseConfigs, updateHistory } from '../api'

const route = useRoute()
const video = ref(null)
const sources = ref([])
const parseConfigs = ref([])
const selectedParseConfig = ref(null)
const currentUrl = ref('')

const loadData = async () => {
  const mediaType = route.params.media_type
  const tmdbId = route.params.id
  const { data } = await getVideoDetail(mediaType, tmdbId)
  video.value = data
  const { data: sourcesData } = await getPlaySources()
  sources.value = sourcesData
  const { data: configs } = await getParseConfigs()
  parseConfigs.value = configs
}

const playSource = (source) => {
  if (source.type === 'parse') {
    const config = parseConfigs.value.find(c => c.id === selectedParseConfig.value) || parseConfigs.value[0]
    if (config) {
      currentUrl.value = config.base_url + encodeURIComponent(source.url)
    }
  } else {
    currentUrl.value = source.url
  }
}

const saveProgress = async () => {
  if (video.value) {
    try {
      await updateHistory(video.value.tmdb_id, {
        progress: 0,
        duration: null,
        source_id: sources.value[0]?.id
      })
    } catch {}
  }
}

onMounted(loadData)
onBeforeUnmount(saveProgress)
</script>

<style scoped>
.play-page {
  display: flex;
  gap: 20px;
  padding: 20px;
}
.play-left {
  width: 300px;
}
.poster {
  width: 100%;
  border-radius: 8px;
}
.play-right {
  flex: 1;
}
.parse-selector {
  margin-bottom: 10px;
}
.player-container {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  margin-bottom: 20px;
}
.player-iframe {
  width: 100%;
  height: 100%;
}
.source-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}
.source-speed {
  color: #67c23a;
  font-size: 12px;
}
.source-speed.testing {
  color: #909399;
}
</style>
