# LightVid 完整实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 构建完整的 LightVid 视频聚合播放应用——TV Box 源管理、豆瓣海报墙、智能测速播放

**架构:** 前后端分离架构。前端 Vue3 + Vite + Element Plus 通过 API 与后端 FastAPI 通信，后端管理 SQLite 数据库、爬虫任务、定时测速。前端 iframe 嵌入解析页面实现播放。

**技术栈:** Vue3 / Vite / Element Plus / FastAPI / SQLAlchemy / SQLite / httpx / BeautifulSoup / Docker Compose

---

## 文件结构总览

```
LightVid/
├── backend/
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置
│   ├── database.py                # SQLAlchemy 连接
│   ├── requirements.txt          # Python 依赖
│   ├── Dockerfile                # Docker 构建文件
│   ├── models/
│   │   ├── __init__.py
│   │   ├── video_source.py        # VideoSource 模型
│   │   ├── douban_video.py        # DoubanVideo 模型
│   │   └── parse_config.py        # ParseConfig 模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── video_source.py        # Pydantic schemas
│   │   ├── douban_video.py
│   │   └── parse_config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── sources.py             # /api/sources 路由
│   │   ├── douban.py              # /api/douban 路由
│   │   ├── parse_configs.py       # /api/parse-configs 路由
│   │   └── play.py               # /api/play 路由
│   ├── crawlers/
│   │   ├── __init__.py
│   │   ├── tvbox_crawler.py       # TV Box 源爬虫
│   │   └── douban_crawler.py      # 豆瓣爬虫
│   └── services/
│       ├── __init__.py
│       └── speed_test.py          # 测速服务
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── api/
│   │   │   └── index.js           # axios 封装
│   │   ├── views/
│   │   │   ├── Home.vue           # 海报墙
│   │   │   ├── Search.vue
│   │   │   ├── VideoDetail.vue
│   │   │   ├── Play.vue           # 播放页
│   │   │   ├── Tvbox.vue          # TV Box 列表
│   │   │   └── Settings.vue
│   │   └── components/
│   │       ├── PosterWall.vue     # 海报墙组件
│   │       └── SourceList.vue     # 源列表组件
│   └── package.json
├── nginx.conf                     # Nginx 配置
└── docker-compose.yml
```

---

## 阶段一：项目基础搭建

### Task 1: 初始化后端 FastAPI 项目

**Files:**
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: 创建 backend/requirements.txt**

```txt
fastapi==0.109.2
uvicorn[standard]==0.27.1
sqlalchemy==2.0.25
pydantic==2.6.1
httpx==0.26.0
beautifulsoup4==4.12.3
lxml==5.1.0
apscheduler==3.10.4
python-multipart==0.0.9
pydantic[email]==2.6.1
```

- [ ] **Step 2: 创建 backend/config.py**

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'lightvid.db'}"
```

- [ ] **Step 3: 创建 backend/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import HTTPException
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,  # 连接前验证
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """数据库依赖：每个请求创建独立 session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    finally:
        db.close()
```

- [ ] **Step 4: 创建 backend/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LightVid API")

# CORS 配置（允许前端开发服务器访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 验证后端运行**

Run: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000`
Expected: `Uvicorn running on http://127.0.0.1:8000`

---

### Task 2: 初始化前端 Vue3 + Vite 项目

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`

- [ ] **Step 1: 创建 frontend/package.json**

```json
{
  "name": "lightvid-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.21",
    "vue-router": "^4.3.0",
    "element-plus": "^2.6.1",
    "axios": "^1.6.7"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.4",
    "vite": "^5.1.4"
  }
}
```

- [ ] **Step 2: 创建 frontend/vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建 frontend/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LightVid - 轻影</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: 创建 frontend/src/main.js**

```javascript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 5: 创建 frontend/src/App.vue**

```vue
<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Arial, sans-serif;
}
</style>
```

- [ ] **Step 6: 安装依赖并验证前端运行**

Run: `cd frontend && npm install && npm run dev`
Expected: `VITE v5.1.4 ready on http://localhost:3000`

---

### Task 3: 配置 Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `Dockerfile.backend`

- [ ] **Step 1: 创建 docker-compose.yml**

```yaml
services:
  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      backend:
        condition: service_healthy

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    working_dir: /app
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  crawler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - ./data:/app/data
    working_dir: /app
    command: python -m crawlers.scheduler
    depends_on:
      backend:
        condition: service_healthy
```

- [ ] **Step 2: 创建 backend/Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

- [ ] **Step 3: 创建 nginx.conf**

```nginx
server {
    listen 80;
    server_name localhost;

    # Vue Router HTML5 History 模式（刷新不 404）
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        root /usr/share/nginx/html;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 阶段二：TV Box 源管理

### Task 4: 创建 VideoSource 数据模型

**Files:**
- Create: `backend/models/__init__.py`
- Create: `backend/models/video_source.py`
- Create: `backend/schemas/__init__.py`
- Create: `backend/schemas/video_source.py`

- [ ] **Step 1: 创建 backend/models/video_source.py**

```python
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class VideoSource(Base):
    __tablename__ = "video_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    type = Column(String, default="m3u8")  # m3u8 / direct / parse
    platform = Column(String, default="tvbox")  # tvbox / tencent / mango / youku / iqiyi
    source_type = Column(String, default="crawl")  # crawl / user
    speed = Column(Float, nullable=True)  # 秒，NULL 表示未测速
    status = Column(String, default="active")  # active / inactive / expired
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 创建 backend/schemas/video_source.py**

```python
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class VideoSourceBase(BaseModel):
    name: str
    url: str
    type: str = "m3u8"
    platform: str = "tvbox"
    source_type: str = "user"

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class VideoSourceCreate(VideoSourceBase):
    pass

class VideoSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None
    speed: Optional[float] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class VideoSourceResponse(VideoSourceBase):
    id: int
    speed: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 更新 backend/models/__init__.py**

```python
from database import Base
from video_source import VideoSource
from douban_video import DoubanVideo
from parse_config import ParseConfig

__all__ = ["Base", "VideoSource", "DoubanVideo", "ParseConfig"]
```

- [ ] **Step 4: 验证模型创建**

Run: `cd backend && python -c "from models import VideoSource; print('OK')"`
Expected: `OK`

---

### Task 5: TV Box 源爬虫

**Files:**
- Create: `backend/crawlers/__init__.py`
- Create: `backend/crawlers/tvbox_crawler.py`

- [ ] **Step 1: 创建 backend/crawlers/tvbox_crawler.py**

```python
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models.video_source import VideoSource
from httpx import Retry, Transport
import re

TVBOX_SOURCE_URLS = [
    "https://raw.githubusercontent.com/zbh2535/TVBox/main/lives.json",
    "https://raw.githubusercontent.com/zbh2535/TVBox/main/movies.json",
]

# httpx 重试配置
retry_transport = Transport(retries=3)

async def crawl_tvbox_sources(db: Session):
    discovered = []
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=30.0),
        transport=retry_transport
    ) as client:
        for url in TVBOX_SOURCE_URLS:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                channels = data.get("data", [])
                for ch in channels:
                    name = ch.get("name", "未知")
                    url_val = ch.get("url", "")
                    # URL 验证：必须是 http/https 开头
                    if url_val and url_val.startswith(("http://", "https://")):
                        source = VideoSource(
                            name=name,
                            url=url_val,
                            type="m3u8",
                            platform="tvbox",
                            source_type="crawl",
                            status="active"
                        )
                        discovered.append(source)
            except httpx.ConnectTimeout:
                print(f"Crawl timeout for {url}")
            except httpx.ConnectError as e:
                print(f"Crawl connection error for {url}: {e}")
            except Exception as e:
                print(f"Crawl failed for {url}: {e}")
    # 去重
    existing = {s.url for s in db.query(VideoSource).filter_by(source_type="crawl").all()}
    new_sources = [s for s in discovered if s.url not in existing]
    if new_sources:
        db.add_all(new_sources)
        db.commit()
    return len(new_sources)
```

- [ ] **Step 2: 验证爬虫可运行**

Run: `cd backend && python -c "import asyncio; from crawlers.tvbox_crawler import crawl_tvbox_sources; print('OK')"`
Expected: `OK`

---

### Task 6: 源 CRUD API

**Files:**
- Create: `backend/api/sources.py`

- [ ] **Step 1: 创建 backend/api/sources.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import case
from database import get_db
from models.video_source import VideoSource
from schemas.video_source import VideoSourceCreate, VideoSourceUpdate, VideoSourceResponse
from crawlers.tvbox_crawler import crawl_tvbox_sources
from services.speed_test import speed_test_source

router = APIRouter(prefix="/api/sources", tags=["sources"])

@router.get("", response_model=list[VideoSourceResponse])
def get_sources(
    type: str = None,
    platform: str = None,
    source_type: str = None,
    db: Session = Depends(get_db)
):
    q = db.query(VideoSource)
    if type:
        q = q.filter_by(type=type)
    if platform:
        q = q.filter_by(platform=platform)
    if source_type:
        q = q.filter_by(source_type=source_type)
    return q.order_by(
        case((VideoSource.speed == None, 1), else_=0),
        VideoSource.speed.asc()
    ).all()

@router.post("", response_model=VideoSourceResponse)
def create_source(data: VideoSourceCreate, db: Session = Depends(get_db)):
    existing = db.query(VideoSource).filter_by(url=data.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="URL already exists")
    source = VideoSource(**data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(VideoSource).get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"ok": True}

@router.post("/crawl")
def trigger_crawl(db: Session = Depends(get_db)):
    import asyncio
    count = asyncio.run(crawl_tvbox_sources(db))
    return {"crawled": count}

@router.post("/speed-test/{source_id}")
def test_single_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(VideoSource).get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    duration = speed_test_source(source.url)
    source.speed = duration
    db.commit()
    return {"id": source_id, "speed": duration}
```

- [ ] **Step 2: 更新 backend/main.py 注册路由**

```python
from fastapi import FastAPI
from database import engine, Base
from api.sources import router as sources_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LightVid API")
app.include_router(sources_router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: 创建 backend/services/speed_test.py**

```python
import httpx
import asyncio

async def _speed_test(url: str) -> float:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            start = asyncio.get_event_loop().time()
            resp = await client.head(url, follow_redirects=True)
            elapsed = asyncio.get_event_loop().time() - start
            if resp.status_code == 200:
                return round(elapsed, 3)
    except:
        pass
    return None

def speed_test_source(url: str) -> float:
    return asyncio.run(_speed_test(url))
```

- [ ] **Step 4: 创建 backend/services/__init__.py**

```python
# Services package
```

- [ ] **Step 5: 验证 API 运行**

Run: `cd backend && uvicorn main:app --reload --port 8000 &`
Run: `curl http://localhost:8000/api/health`
Expected: `{"status":"ok"}`

---

### Task 7: TV Box 前端页面

**Files:**
- Create: `frontend/src/api/index.js`
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/views/Tvbox.vue`

- [ ] **Step 1: 创建 frontend/src/api/index.js**

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

export const getSources = (params) => api.get('/sources', { params })
export const createSource = (data) => api.post('/sources', data)
export const deleteSource = (id) => api.delete(`/sources/${id}`)
export const triggerCrawl = () => api.post('/sources/crawl')
export const speedTest = (id) => api.post(`/sources/speed-test/${id}`)
```

- [ ] **Step 2: 创建 frontend/src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/search', component: () => import('../views/Search.vue') },
  { path: '/tvbox', component: () => import('../views/Tvbox.vue') },
  { path: '/settings', component: () => import('../views/Settings.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

- [ ] **Step 3: 创建 frontend/src/views/Tvbox.vue**

```vue
<template>
  <div class="tvbox-page">
    <el-button type="primary" @click="handleCrawl" :loading="crawling">
      爬取 TV Box 源
    </el-button>
    <el-table v-loading="loading" :data="sources" style="width: 100%; margin-top: 20px">
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="url" label="地址" show-overflow-tooltip />
      <el-table-column prop="speed" label="速度(秒)" width="100">
        <template #default="{ row }">
          {{ row.speed ? row.speed + 's' : '未测速' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="handleSpeedTest(row.id)" :loading="row.testing">测速</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeRouteLeave } from 'vue'
import { ElMessage } from 'element-plus'
import { getSources, triggerCrawl, speedTest, deleteSource } from '../api'

const sources = ref([])
const crawling = ref(false)
const loading = ref(false)
let controller = null  // 用于取消请求

onMounted(() => {
  loadSources()
})

onBeforeRouteLeave(() => {
  // 离开页面时取消未完成的请求
  if (controller) {
    controller.abort()
  }
})

const loadSources = async () => {
  loading.value = true
  controller = new AbortController()
  try {
    const { data } = await getSources({ platform: 'tvbox' })
    sources.value = data
  } catch (err) {
    if (err.name !== 'CanceledError') {
      ElMessage.error('加载数据失败')
    }
  } finally {
    loading.value = false
  }
}

const handleCrawl = async () => {
  crawling.value = true
  try {
    await triggerCrawl()
    await loadSources()
    ElMessage.success('爬取完成')
  } catch (err) {
    ElMessage.error('爬取失败')
  } finally {
    crawling.value = false
  }
}

const handleSpeedTest = async (id) => {
  const source = sources.value.find(s => s.id === id)
  if (source) source.testing = true
  try {
    await speedTest(id)
    await loadSources()
    ElMessage.success('测速完成')
  } catch (err) {
    ElMessage.error('测速失败')
  }
}

const handleDelete = async (id) => {
  try {
    await deleteSource(id)
    await loadSources()
    ElMessage.success('删除成功')
  } catch (err) {
    ElMessage.error('删除失败')
  }
}
</script>
```

---

## 阶段三：豆瓣数据

### Task 8: 创建 DoubanVideo 数据模型

**Files:**
- Create: `backend/models/douban_video.py`
- Update: `backend/models/__init__.py`
- Create: `backend/schemas/douban_video.py`
- Update: `backend/schemas/__init__.py`

- [ ] **Step 1: 创建 backend/models/douban_video.py**

```python
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from database import Base

class DoubanVideo(Base):
    __tablename__ = "douban_videos"

    id = Column(Integer, primary_key=True, index=True)
    douban_id = Column(String, unique=True, index=True)
    title = Column(String)
    poster_url = Column(String)
    rating = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    category = Column(String, default="movie")  # movie / tv
    genres = Column(String, nullable=True)  # 逗号分隔
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: 创建 backend/schemas/douban_video.py**

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DoubanVideoResponse(BaseModel):
    id: int
    douban_id: str
    title: str
    poster_url: Optional[str]
    rating: Optional[float]
    summary: Optional[str]
    year: Optional[int]
    category: str
    genres: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 更新 backend/models/__init__.py**

```python
from database import Base
from video_source import VideoSource
from douban_video import DoubanVideo
from parse_config import ParseConfig

__all__ = ["Base", "VideoSource", "DoubanVideo", "ParseConfig"]
```

- [ ] **Step 4: 验证**

Run: `cd backend && python -c "from models import DoubanVideo; print('OK')"`
Expected: `OK`

---

### Task 9: 豆瓣爬虫

**Files:**
- Create: `backend/crawlers/douban_crawler.py`

- [ ] **Step 1: 创建 backend/crawlers/douban_crawler.py**

```python
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models.douban_video import DoubanVideo

async def crawl_douban_video(db: Session, douban_id: str):
    existing = db.query(DoubanVideo).filter_by(douban_id=douban_id).first()
    if existing:
        return existing

    url = f"https://movie.douban.com/subject/{douban_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    try:
        async with httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(15.0, connect=30.0),
            follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            # 使用 lxml 解析器（更容错，处理乱码更好）
            soup = BeautifulSoup(resp.text, "lxml")

            title = soup.select_one("h1 span[property='v:itemreviewed']")
            title = title.text if title else "未知"

            img = soup.select_one("img[rel='v:image']")
            poster_url = img.get("src") if img else None

            rating = soup.select_one("strong[property='v:average']")
            rating = float(rating.text) if rating else None

            year = soup.select_one("span[property='v:initialReleaseDate']")
            year = int(year.text[:4]) if year else None

            summary = soup.select_one("span[property='v:summary']")
            summary = summary.text.strip() if summary else None

            genres = soup.select("span[property='v:genre']")
            genres = ",".join(g.text for g in genres)

            category = "tv" if "/tv/" in url else "movie"

            video = DoubanVideo(
                douban_id=douban_id,
                title=title,
                poster_url=poster_url,
                rating=rating,
                year=year,
                summary=summary,
                genres=genres,
                category=category,
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            return video
    except httpx.ConnectTimeout:
        print(f"连接超时: {douban_id}")
        return None
    except httpx.ConnectError as e:
        print(f"连接错误: {douban_id} - {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP 错误 {e.response.status_code}: {douban_id}")
        return None
    except Exception as e:
        print(f"Failed to crawl {douban_id}: {e}")
        return None
```

- [ ] **Step 2: 验证爬虫代码可导入**

Run: `cd backend && python -c "from crawlers.douban_crawler import crawl_douban_video; print('OK')"`
Expected: `OK`

---

### Task 10: 豆瓣 API 路由

**Files:**
- Create: `backend/api/douban.py`
- Update: `backend/main.py`

- [ ] **Step 1: 创建 backend/api/douban.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.douban_video import DoubanVideo
from schemas.douban_video import DoubanVideoResponse
from crawlers.douban_crawler import crawl_douban_video

router = APIRouter(prefix="/api/douban", tags=["douban"])

@router.get("/videos", response_model=list[DoubanVideoResponse])
def get_videos(
    category: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    q = db.query(DoubanVideo)
    if category:
        q = q.filter_by(category=category)
    return q.offset(skip).limit(limit).all()

@router.get("/videos/{douban_id}", response_model=DoubanVideoResponse)
def get_video(douban_id: str, db: Session = Depends(get_db)):
    video = db.query(DoubanVideo).filter_by(douban_id=douban_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.get("/search")
def search_videos(q: str, db: Session = Depends(get_db)):
    """搜索豆瓣视频（按标题模糊搜索本地数据库）"""
    videos = db.query(DoubanVideo).filter(
        DoubanVideo.title.like(f"%{q}%")
    ).limit(20).all()
    return videos

@router.post("/crawl")
def crawl_video(douban_id: str, db: Session = Depends(get_db)):
    import asyncio
    video = asyncio.run(crawl_douban_video(db, douban_id))
    if not video:
        raise HTTPException(status_code=500, detail="Crawl failed")
    return video
```

- [ ] **Step 2: 更新 backend/main.py**

```python
from fastapi import FastAPI
from database import engine, Base
from api.sources import router as sources_router
from api.douban import router as douban_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LightVid API")
app.include_router(sources_router)
app.include_router(douban_router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

---

### Task 11: 首页海报墙

**Files:**
- Update: `frontend/src/api/index.js`
- Update: `frontend/src/router/index.js`
- Update: `frontend/src/App.vue`
- Create: `frontend/src/views/Home.vue`
- Create: `frontend/src/components/PosterWall.vue`

- [ ] **Step 1: 更新 frontend/src/api/index.js**

```javascript
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

// Douban
export const getVideos = (params) => api.get('/douban/videos', { params })
export const getVideo = (doubanId) => api.get(`/douban/videos/${doubanId}`)
export const searchVideos = (q) => api.get('/douban/search', { params: { q } })
export const crawlVideo = (doubanId) => api.post('/douban/crawl', null, { params: { douban_id: doubanId } })

// Play
export const getPlaySources = () => api.get('/play/sources')

// Parse Configs
export const getParseConfigs = () => api.get('/parse-configs')
export const createParseConfig = (data) => api.post('/parse-configs', data)
export const updateParseConfig = (id, data) => api.put(`/parse-configs/${id}`, data)
export const deleteParseConfig = (id) => api.delete(`/parse-configs/${id}`)

// History
export const getHistory = () => api.get('/history')
export const updateHistory = (doubanId, data) => api.post('/history', data, { params: { douban_id: doubanId } })
export const deleteHistory = (doubanId) => api.delete(`/history/${doubanId}`)

// Favorites
export const getFavorites = () => api.get('/favorites')
export const addFavorite = (doubanId) => api.post(`/favorites/${doubanId}`)
export const removeFavorite = (doubanId) => api.delete(`/favorites/${doubanId}`)
export const checkFavorite = (doubanId) => api.get(`/favorites/check/${doubanId}`)
```

- [ ] **Step 2: 创建 frontend/src/components/PosterWall.vue**

```vue
<template>
  <div class="poster-wall">
    <div v-for="video in videos" :key="video.id" class="poster-item" @click="$emit('select', video)">
      <img :src="video.poster_url" :alt="video.title" loading="lazy" />
      <div class="poster-info">
        <span class="title">{{ video.title }}</span>
        <span class="rating" v-if="video.rating">{{ video.rating }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  videos: Array
})
defineEmits(['select'])
</script>

<style scoped>
.poster-wall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
  padding: 20px;
}
.poster-item {
  cursor: pointer;
  transition: transform 0.2s;
}
.poster-item:hover {
  transform: scale(1.05);
}
.poster-item img {
  width: 100%;
  border-radius: 8px;
}
.poster-info {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}
.title {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rating {
  color: #f5a623;
}
</style>
```

- [ ] **Step 3: 创建 frontend/src/views/Home.vue**

```vue
<template>
  <div class="home">
    <div class="header">
      <h1>LightVid 轻影</h1>
      <el-input v-model="keyword" placeholder="搜索..." style="width: 300px" @keyup.enter="handleSearch" />
      <el-tabs v-model="category" @tab-change="loadVideos">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="电影" name="movie" />
        <el-tab-pane label="剧集" name="tv" />
      </el-tabs>
    </div>
    <div v-loading="loading" class="content">
      <PosterWall :videos="videos" @select="handleSelect" />
      <el-empty v-if="!loading && videos.length === 0" description="暂无数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeRouteLeave } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideos } from '../api'
import PosterWall from '../components/PosterWall.vue'

const router = useRouter()
const videos = ref([])
const category = ref('all')
const keyword = ref('')
const loading = ref(false)
let controller = null

onMounted(() => {
  loadVideos()
})

onBeforeRouteLeave(() => {
  if (controller) {
    controller.abort()
  }
})

const loadVideos = async () => {
  loading.value = true
  controller = new AbortController()
  try {
    const params = {}
    if (category.value !== 'all') params.category = category.value
    const { data } = await getVideos(params)
    videos.value = data
  } catch (err) {
    if (err.name !== 'CanceledError') {
      ElMessage.error('加载数据失败')
    }
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  router.push({ path: '/search', query: { q: keyword.value } })
}

const handleSelect = (video) => {
  router.push(`/video/${video.douban_id}`)
}
</script>

<style scoped>
.header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
</style>
```

- [ ] **Step 4: 更新 frontend/src/App.vue 添加导航**

```vue
<template>
  <div id="app">
    <el-menu mode="horizontal" :router="true">
      <el-menu-item index="/">首页</el-menu-item>
      <el-menu-item index="/tvbox">TV Box</el-menu-item>
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
}
body {
  margin: 0;
}
</style>
```

---

## 阶段四：播放功能

### Task 12: ParseConfig 数据模型与 API

**Files:**
- Create: `backend/models/parse_config.py`
- Create: `backend/schemas/parse_config.py`
- Create: `backend/api/parse_configs.py`
- Update: `backend/main.py`

- [ ] **Step 1: 创建 backend/models/parse_config.py**

```python
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class ParseConfig(Base):
    __tablename__ = "parse_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    base_url = Column(String)
    priority = Column(Integer, default=0)
    status = Column(String, default="active")  # active / inactive
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: 创建 backend/schemas/parse_config.py**

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ParseConfigBase(BaseModel):
    name: str
    base_url: str
    priority: int = 0

class ParseConfigCreate(ParseConfigBase):
    pass

class ParseConfigUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None

class ParseConfigResponse(ParseConfigBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 创建 backend/api/parse_configs.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.parse_config import ParseConfig
from schemas.parse_config import ParseConfigCreate, ParseConfigUpdate, ParseConfigResponse

router = APIRouter(prefix="/api/parse-configs", tags=["parse-configs"])

@router.get("", response_model=list[ParseConfigResponse])
def get_configs(db: Session = Depends(get_db)):
    return db.query(ParseConfig).filter_by(status="active").order_by(ParseConfig.priority.desc()).all()

@router.post("", response_model=ParseConfigResponse)
def create_config(data: ParseConfigCreate, db: Session = Depends(get_db)):
    config = ParseConfig(**data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config

@router.put("/{config_id}", response_model=ParseConfigResponse)
def update_config(config_id: int, data: ParseConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(ParseConfig).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config

@router.delete("/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(ParseConfig).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    db.delete(config)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 4: 更新 backend/main.py**

```python
from fastapi import FastAPI
from database import engine, Base
from api.sources import router as sources_router
from api.douban import router as douban_router
from api.parse_configs import router as parse_configs_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LightVid API")
app.include_router(sources_router)
app.include_router(douban_router)
app.include_router(parse_configs_router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

---

### Task 12b: 播放源聚合 API

**Files:**
- Create: `backend/api/play.py`

- [ ] **Step 1: 创建 backend/api/play.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import case
from database import get_db
from models.video_source import VideoSource

router = APIRouter(prefix="/api/play", tags=["play"])

@router.get("/sources")
def get_play_sources(db: Session = Depends(get_db)):
    """
    获取所有可用播放源，按速度排序（未测速的排在最后）。
    """
    sources = db.query(VideoSource).filter_by(
        status="active"
    ).order_by(
        case((VideoSource.speed == None, 1), else_=0),
        VideoSource.speed.asc()
    ).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "type": s.type,
            "platform": s.platform,
            "speed": s.speed,
        }
        for s in sources
    ]

@router.get("/{source_id}")
def get_play_url(source_id: int, db: Session = Depends(get_db)):
    """
    播放指定源，返回解析后的播放地址。
    如果源类型是 parse，则拼接解析接口。
    """
    source = db.query(VideoSource).get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status != "active":
        raise HTTPException(status_code=400, detail="Source is not active")
    return {
        "id": source.id,
        "name": source.name,
        "url": source.url,
        "type": source.type,
        "platform": source.platform,
        "speed": source.speed,
    }
```

- [ ] **Step 2: 更新 backend/main.py 添加 play 路由**

```python
from fastapi import FastAPI
from database import engine, Base
from api.sources import router as sources_router
from api.douban import router as douban_router
from api.parse_configs import router as parse_configs_router
from api.play import router as play_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LightVid API")
app.include_router(sources_router)
app.include_router(douban_router)
app.include_router(parse_configs_router)
app.include_router(play_router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: 验证 API**

Run: `cd backend && uvicorn main:app --reload --port 8000 &`
Run: `curl "http://localhost:8000/api/play/sources"`
Expected: JSON array of sources

---

### Task 13: 播放页开发

**Files:**
- Create: `frontend/src/views/Play.vue`
- Update: `frontend/src/router/index.js`

- [ ] **Step 1: 创建 frontend/src/views/Play.vue**

```vue
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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getVideo, getPlaySources, getParseConfigs } from '../api'

const route = useRoute()
const video = ref(null)
const sources = ref([])
const parseConfigs = ref([])
const selectedParseConfig = ref(null)
const currentUrl = ref('')

const loadData = async () => {
  const doubanId = route.params.id
  video.value = await getVideo(doubanId)
  const { data } = await getPlaySources()
  sources.value = data
  const { data: configs } = await getParseConfigs()
  parseConfigs.value = configs
}

const playSource = (source) => {
  if (source.type === 'parse') {
    // 使用选中的解析接口解析视频 URL
    const config = parseConfigs.value.find(c => c.id === selectedParseConfig.value) || parseConfigs.value[0]
    if (config) {
      currentUrl.value = config.base_url + encodeURIComponent(source.url)
    }
  } else {
    currentUrl.value = source.url
  }
}

onMounted(loadData)
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
```

- [ ] **Step 2: 更新 frontend/src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/search', component: () => import('../views/Search.vue') },
  { path: '/video/:id', component: () => import('../views/VideoDetail.vue') },
  { path: '/video/:id/play', component: () => import('../views/Play.vue') },
  { path: '/tvbox', component: () => import('../views/Tvbox.vue') },
  { path: '/settings', component: () => import('../views/Settings.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

- [ ] **Step 3: 创建 frontend/src/views/VideoDetail.vue**

```vue
<template>
  <div class="video-detail" v-if="video">
    <img :src="video.poster_url" class="poster" />
    <div class="info">
      <h1>{{ video.title }}</h1>
      <p class="rating" v-if="video.rating">评分: {{ video.rating }}</p>
      <p class="year" v-if="video.year">{{ video.year }}年</p>
      <p class="genres" v-if="video.genres">{{ video.genres }}</p>
      <p class="summary">{{ video.summary }}</p>
      <el-button type="primary" size="large" @click="$router.push(`/video/${video.douban_id}/play`)">
        开始播放
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getVideo } from '../api'

const route = useRoute()
const video = ref(null)

onMounted(async () => {
  video.value = await getVideo(route.params.id)
})
</script>

<style scoped>
.video-detail {
  display: flex;
  gap: 40px;
  padding: 40px;
}
.poster {
  width: 300px;
  border-radius: 12px;
}
.info h1 {
  margin: 0 0 20px 0;
}
.summary {
  line-height: 1.6;
  color: #666;
}
</style>
```

---

## 阶段五：设置页与收尾

### Task 14: 设置页开发

**Files:**
- Create: `frontend/src/views/Settings.vue`

- [ ] **Step 1: 创建 frontend/src/views/Settings.vue**

```vue
<template>
  <div class="settings">
    <h2>解析接口管理</h2>
    <el-button type="primary" @click="openAddDialog">添加解析接口</el-button>
    <el-table v-loading="loading" :data="configs" style="width: 100%; margin-top: 20px">
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="base_url" label="地址" show-overflow-tooltip />
      <el-table-column prop="priority" label="优先级" width="100" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="editConfig(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showAddDialog" :title="editing ? '编辑' : '添加'" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如：虾米解析" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.base_url" placeholder="如：https://jx.xmflv.com/?url=" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="form.priority" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getParseConfigs, createParseConfig, updateParseConfig, deleteParseConfig } from '../api'

const configs = ref([])
const showAddDialog = ref(false)
const editing = ref(null)
const loading = ref(false)
const saving = ref(false)
const form = ref({ name: '', base_url: '', priority: 0 })

onMounted(() => {
  loadConfigs()
})

const loadConfigs = async () => {
  loading.value = true
  try {
    const { data } = await getParseConfigs()
    configs.value = data
  } catch (err) {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  editing.value = null
  form.value = { name: '', base_url: '', priority: 0 }
  showAddDialog.value = true
}

const editConfig = (config) => {
  editing.value = config.id
  form.value = { ...config }
  showAddDialog.value = true
}

const handleSave = async () => {
  if (!form.value.name || !form.value.base_url) {
    ElMessage.warning('请填写名称和地址')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateParseConfig(editing.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createParseConfig(form.value)
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    loadConfigs()
  } catch (err) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await deleteParseConfig(id)
    ElMessage.success('删除成功')
    loadConfigs()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}
</script>
```

---

### Task 15: 搜索页

**Files:**
- Create: `frontend/src/views/Search.vue`

- [ ] **Step 1: 创建 frontend/src/views/Search.vue**

```vue
<template>
  <div class="search-page">
    <div class="search-bar">
      <el-input v-model="keyword" placeholder="搜索视频名称..." style="width: 400px" @keyup.enter="handleSearch" />
      <el-button type="primary" @click="handleSearch" :loading="searching">搜索</el-button>
    </div>
    <div class="crawl-bar">
      <el-input v-model="doubanId" placeholder="输入豆瓣 ID（如 1292052）" style="width: 400px" @keyup.enter="handleCrawl" />
      <el-button type="success" @click="handleCrawl" :loading="crawling">添加视频</el-button>
    </div>
    <div v-loading="loading" class="results">
      <PosterWall :videos="videos" @select="handleSelect" />
      <el-empty v-if="!loading && videos.length === 0" description="暂无数据，请搜索或添加视频" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { searchVideos, crawlVideo, getVideos } from '../api'
import PosterWall from '../components/PosterWall.vue'

const router = useRouter()
const keyword = ref('')
const doubanId = ref('')
const videos = ref([])
const searching = ref(false)
const crawling = ref(false)
const loading = ref(false)

const handleSearch = async () => {
  if (!keyword.value) return
  searching.value = true
  try {
    const { data } = await searchVideos(keyword.value)
    videos.value = data
    if (data.length === 0) {
      ElMessage.info('未找到匹配的视频')
    }
  } catch (err) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

const handleCrawl = async () => {
  if (!doubanId.value) return
  crawling.value = true
  try {
    await crawlVideo(doubanId.value)
    ElMessage.success('添加成功')
    const { data } = await getVideos()
    videos.value = data
  } catch (err) {
    ElMessage.error('添加失败，请检查豆瓣 ID 是否正确')
  } finally {
    crawling.value = false
  }
}

const handleSelect = (video) => {
  router.push(`/video/${video.douban_id}`)
}
</script>

<style scoped>
.search-page {
  padding: 20px;
}
.search-bar, .crawl-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.results {
  min-height: 200px;
}
</style>
```

---

### Task 16: 观看历史与续播

**Files:**
- Create: `backend/models/watch_history.py`
- Create: `backend/schemas/watch_history.py`
- Create: `backend/api/history.py`
- Create: `frontend/src/views/History.vue`
- Update: `frontend/src/router/index.js`
- Update: `frontend/src/App.vue`

- [ ] **Step 1: 创建 backend/models/watch_history.py**

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from database import Base

class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    douban_id = Column(String, index=True)
    source_id = Column(Integer, ForeignKey("video_sources.id"), nullable=True)
    progress = Column(Float, default=0)  # 秒
    duration = Column(Float, nullable=True)  # 视频总时长
    last_watched = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 创建 backend/schemas/watch_history.py**

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WatchHistoryResponse(BaseModel):
    id: int
    douban_id: str
    source_id: Optional[int]
    progress: float
    duration: Optional[float]
    last_watched: datetime
    video: Optional[dict] = None  # 关联的 DoubanVideo 信息

    class Config:
        from_attributes = True

class WatchHistoryUpdate(BaseModel):
    progress: float
    duration: Optional[float] = None
    source_id: Optional[int] = None
```

- [ ] **Step 3: 创建 backend/api/history.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.watch_history import WatchHistory
from models.douban_video import DoubanVideo
from schemas.watch_history import WatchHistoryResponse, WatchHistoryUpdate

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("", response_model=list[WatchHistoryResponse])
def get_history(db: Session = Depends(get_db)):
    items = db.query(WatchHistory).order_by(WatchHistory.last_watched.desc()).limit(50).all()
    result = []
    for item in items:
        video = db.query(DoubanVideo).filter_by(douban_id=item.douban_id).first()
        result.append({
            "id": item.id,
            "douban_id": item.douban_id,
            "source_id": item.source_id,
            "progress": item.progress,
            "duration": item.duration,
            "last_watched": item.last_watched,
            "video": {
                "title": video.title,
                "poster_url": video.poster_url,
                "rating": video.rating,
            } if video else None
        })
    return result

@router.post("")
def update_history(douban_id: str, data: WatchHistoryUpdate, db: Session = Depends(get_db)):
    history = db.query(WatchHistory).filter_by(douban_id=douban_id).first()
    if history:
        history.progress = data.progress
        history.duration = data.duration
        history.source_id = data.source_id
        history.last_watched = datetime.utcnow()
    else:
        history = WatchHistory(
            douban_id=douban_id,
            progress=data.progress,
            duration=data.duration,
            source_id=data.source_id,
        )
        db.add(history)
    db.commit()
    return {"ok": True}

@router.delete("/{douban_id}")
def delete_history(douban_id: str, db: Session = Depends(get_db)):
    history = db.query(WatchHistory).filter_by(douban_id=douban_id).first()
    if history:
        db.delete(history)
        db.commit()
    return {"ok": True}
```

- [ ] **Step 4: 创建 frontend/src/views/History.vue**

```vue
<template>
  <div class="history-page">
    <h2>继续观看</h2>
    <div v-loading="loading" class="history-list">
      <div v-for="item in history" :key="item.id" class="history-item" @click="handleResume(item)">
        <img :src="item.video?.poster_url" class="poster" />
        <div class="info">
          <h3>{{ item.video?.title }}</h3>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getProgress(item) + '%' }"></div>
          </div>
          <span class="progress-text">{{ formatProgress(item) }}</span>
        </div>
      </div>
      <el-empty v-if="!loading && history.length === 0" description="暂无观看历史" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHistory, deleteHistory } from '../api'

const router = useRouter()
const history = ref([])
const loading = ref(false)

const loadHistory = async () => {
  loading.value = true
  try {
    const { data } = await getHistory()
    history.value = data
  } catch {
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

const getProgress = (item) => {
  if (!item.duration) return 0
  return Math.min(100, (item.progress / item.duration) * 100)
}

const formatProgress = (item) => {
  if (!item.progress) return '0%'
  const pct = getProgress(item)
  return `${Math.floor(item.progress / 60)}分 / ${Math.floor((item.duration || 0) / 60)}分`
}

const handleResume = (item) => {
  router.push(`/video/${item.douban_id}/play`)
}

onMounted(loadHistory)
</script>

<style scoped>
.history-page { padding: 20px; }
.history-list { display: flex; flex-direction: column; gap: 15px; }
.history-item {
  display: flex;
  gap: 15px;
  cursor: pointer;
  padding: 10px;
  border-radius: 8px;
  background: #1a1a2e;
}
.history-item:hover { background: #252540; }
.poster { width: 120px; height: 68px; object-fit: cover; border-radius: 6px; }
.info { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.info h3 { margin: 0 0 8px 0; font-size: 16px; }
.progress-bar { height: 4px; background: #333; border-radius: 2px; margin-bottom: 4px; }
.progress-fill { height: 100%; background: #409eff; border-radius: 2px; }
.progress-text { font-size: 12px; color: #888; }
</style>
```

---

### Task 17: 收藏功能

**Files:**
- Create: `backend/models/favorite.py`
- Create: `backend/api/favorites.py`
- Create: `frontend/src/views/Favorites.vue`
- Update: `frontend/src/router/index.js`
- Update: `frontend/src/App.vue`

- [ ] **Step 1: 创建 backend/models/favorite.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    douban_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('douban_id', name='uq_favorite_douban_id'),
    )
```

- [ ] **Step 2: 创建 backend/api/favorites.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.favorite import Favorite
from models.douban_video import DoubanVideo

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

@router.get("")
def get_favorites(db: Session = Depends(get_db)):
    favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
    result = []
    for f in favorites:
        video = db.query(DoubanVideo).filter_by(douban_id=f.douban_id).first()
        if video:
            result.append({
                "id": f.id,
                "douban_id": f.douban_id,
                "created_at": f.created_at,
                "video": {
                    "title": video.title,
                    "poster_url": video.poster_url,
                    "rating": video.rating,
                    "year": video.year,
                }
            })
    return result

@router.post("/{douban_id}")
def add_favorite(douban_id: str, db: Session = Depends(get_db)):
    existing = db.query(Favorite).filter_by(douban_id=douban_id).first()
    if existing:
        return {"ok": True, "message": "Already favorited"}
    favorite = Favorite(douban_id=douban_id)
    db.add(favorite)
    db.commit()
    return {"ok": True}

@router.delete("/{douban_id}")
def remove_favorite(douban_id: str, db: Session = Depends(get_db)):
    favorite = db.query(Favorite).filter_by(douban_id=douban_id).first()
    if favorite:
        db.delete(favorite)
        db.commit()
    return {"ok": True}

@router.get("/check/{douban_id}")
def check_favorite(douban_id: str, db: Session = Depends(get_db)):
    favorite = db.query(Favorite).filter_by(douban_id=douban_id).first()
    return {"is_favorite": favorite is not None}
```

- [ ] **Step 3: 创建 frontend/src/views/Favorites.vue**

```vue
<template>
  <div class="favorites-page">
    <h2>我的收藏</h2>
    <div v-loading="loading" class="favorites-list">
      <PosterWall :videos="videos" @select="handleSelect" />
      <el-empty v-if="!loading && videos.length === 0" description="暂无收藏" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFavorites } from '../api'
import PosterWall from '../components/PosterWall.vue'

const router = useRouter()
const videos = ref([])
const loading = ref(false)

const loadFavorites = async () => {
  loading.value = true
  try {
    const { data } = await getFavorites()
    videos.value = data.map(f => f.video)
  } catch {
    ElMessage.error('加载收藏失败')
  } finally {
    loading.value = false
  }
}

const handleSelect = (video) => {
  router.push(`/video/${video.douban_id}`)
}

onMounted(loadFavorites)
</script>

<style scoped>
.favorites-page { padding: 20px; }
.favorites-list { min-height: 200px; }
</style>
```

---

### Task 18: 更新 App.vue 添加导航菜单

**Files:**
- Update: `frontend/src/App.vue`

- [ ] **Step 1: 更新 frontend/src/App.vue**

```vue
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
```

- [ ] **Step 2: 更新 frontend/src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/search', component: () => import('../views/Search.vue') },
  { path: '/video/:id', component: () => import('../views/VideoDetail.vue') },
  { path: '/video/:id/play', component: () => import('../views/Play.vue') },
  { path: '/tvbox', component: () => import('../views/Tvbox.vue') },
  { path: '/history', component: () => import('../views/History.vue') },
  { path: '/favorites', component: () => import('../views/Favorites.vue') },
  { path: '/settings', component: () => import('../views/Settings.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

---

## 实施检查清单

在每个 Task 完成时，验证以下检查项：

1. 代码可以成功导入（无语法错误）
2. API 端点可用（curl 测试）
3. 前端页面可渲染
4. 数据流正确（前端 → API → 数据库 → 返回前端）

## 部署验证

完成后运行：

```bash
cd frontend && npm run build
docker-compose build
docker-compose up -d
curl http://localhost/api/health
```

预期：`{"status":"ok"}`
