# LightVid 轻影

视频资源聚合与播放 Web 应用，支持 TV Box 源管理、TMDB 电影海报墙、智能测速播放、观看历史与收藏功能。

## 功能特性

- **TV Box 源管理** - 自动爬取网上公开的 TV Box 源，支持手动添加、测速、排序
- **TMDB 数据整合** - 通过 TMDB API 获取电影/剧集信息，展示海报墙
- **智能播放** - 聚合多源播放链接，支持自定义解析接口，按速度排序推荐最优源
- **观看历史与续播** - 自动记录播放进度，一键续播
- **收藏功能** - 收藏感兴趣的视频，快速访问

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue3 + Vite + Element Plus |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | SQLite |
| 数据源 | TMDB API |
| 爬虫 | httpx + BeautifulSoup |
| 部署 | Docker Compose |

## 本地运行

### 前置依赖

- Python 3.11+
- Node.js 18+
- npm
- TMDB API Key（免费申请：https://www.themoviedb.org/settings/api）

### 环境配置

1. 复制环境变量模板并配置：
```bash
cp backend/.env.example backend/.env
```

2. 编辑 `backend/.env`，填入你的 TMDB API Key：
```
TMDB_API_KEY=你的API密钥
```

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务 (http://127.0.0.1:18668)
python main.py
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器 (http://localhost:18778)
npm run dev
```

首次启动后端时，会自动初始化 10 个预置解析接口。

## Docker Compose 部署

### 构建并启动

```bash
# 构建镜像并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

服务启动后：
- 前端：http://localhost
- 后端 API：http://localhost:18668
- 健康检查：http://localhost:18668/api/health

### 停止服务

```bash
docker-compose down
```

### 重新构建

```bash
docker-compose up -d --build
```

## 项目结构

```
LightVid/
├── backend/                  # FastAPI 后端
│   ├── api/                # API 路由
│   ├── models/             # SQLAlchemy 模型
│   ├── schemas/            # Pydantic schemas
│   ├── crawlers/           # 爬虫模块
│   ├── services/           # 业务服务（TMDB API、定时任务）
│   ├── config.py          # 配置（从 .env 读取）
│   ├── main.py            # 应用入口
│   └── requirements.txt   # Python 依赖
├── frontend/               # Vue3 前端
│   ├── src/
│   │   ├── api/          # API 封装
│   │   ├── components/   # 公共组件
│   │   ├── views/       # 页面组件
│   │   └── router/      # 路由配置
│   └── package.json
├── docker-compose.yml      # 容器编排
└── nginx.conf              # Nginx 配置
```

## API 文档

后端启动后可访问 http://127.0.0.1:18668/docs 查看 Swagger UI API 文档。

主要 API 端点：

- `GET /api/sources` - 获取播放源列表
- `POST /api/sources/crawl` - 触发爬取 TV Box 源
- `GET /api/douban/videos` - 获取本地视频列表
- `GET /api/douban/tmdb/search` - 搜索 TMDB
- `POST /api/douban/crawl/{tmdb_id}` - 添加视频到本地
- `GET /api/play/sources` - 获取播放源（按速度排序）
- `GET /api/history` - 获取观看历史
- `POST /api/history` - 更新播放进度
- `GET /api/favorites` - 获取收藏列表
- `POST /api/favorites` - 添加收藏
