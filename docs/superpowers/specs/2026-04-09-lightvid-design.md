# LightVid 项目设计规格

## 一、项目概述

**项目名：** LightVid（轻影）
**类型：** 视频资源聚合 + 播放的 Web 应用
**定位：** 单用户本地使用，无需账号系统

## 二、技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | Vue3 + Vite + Element Plus | 现代前端框架，组件丰富 |
| 后端 | FastAPI + SQLAlchemy | 异步高性能 API 框架 |
| 数据库 | SQLite | 轻量零配置 |
| 爬虫 | httpx + BeautifulSoup | 异步 HTTP + HTML 解析 |
| 部署 | Docker Compose | 一键部署 |

## 三、功能模块

### 3.1 TV Box 源管理

**功能：**
- 自动爬取网上公开的 TV Box 源（m3u8 链接）
- 用户可手动添加自定义源
- 自动合并去重
- 后台定时更新

**数据模型：**
```
VideoSource {
  id: int (PK)
  name: str
  url: str
  type: str  # m3u8 / direct / parse
  platform: str  # tvbox / tencent / mango / youku / iqiyi
  source_type: str  # crawl / user
  speed: float  # 测速结果（秒），NULL 表示未测速
  status: str  # active / inactive / expired
  created_at: datetime
  updated_at: datetime
}
```

**API：**
- `GET /api/sources` - 获取所有源，支持过滤（type, platform, source_type）
- `POST /api/sources` - 添加自定义源
- `DELETE /api/sources/{id}` - 删除源
- `POST /api/sources/crawl` - 触发爬取任务
- `POST /api/sources/speed-test` - 批量测速

### 3.2 豆瓣数据获取

**功能：**
- 爬取豆瓣电影/剧集信息（海报、名称、简介、评分、年份、分类）
- 生成海报墙展示
- 搜索功能

**数据模型：**
```
DoubanVideo {
  id: int (PK)
  douban_id: str  # 豆瓣 ID，如 "1292052"
  title: str
  poster_url: str
  rating: float
  summary: str
  year: int
  category: str  # movie / tv
  genres: str  # 逗号分隔，如 "动作,冒险"
  created_at: datetime
}
```

**API：**
- `GET /api/douban/videos` - 获取视频列表，支持分页、分类过滤
- `GET /api/douban/videos/{douban_id}` - 获取视频详情
- `GET /api/douban/search?q={keyword}` - 搜索豆瓣
- `POST /api/douban/crawl` - 爬取指定豆瓣 ID 或批量爬取

### 3.3 播放链接聚合

**功能：**
- 从各视频平台获取播放页面 URL
- 对接视频解析接口

**API：**
- `GET /api/play-sources?douban_id={id}` - 获取某视频的所有可用播放源

### 3.4 智能测速与播放

**功能：**
- 进入播放页后自动对所有可用源测速
- 按速度排序，默认推荐最优源
- 用户可手动切换解析源和视频平台
- 前端播放器使用 iframe 嵌入解析页面

**API：**
- `POST /api/play/{source_id}` - 播放指定源，返回解析后的播放地址

### 3.5 解析接口管理

**数据模型：**
```
ParseConfig {
  id: int (PK)
  name: str  # 如 "解析接口A"
  base_url: str  # 如 "https://jx.example.com/?url="
  priority: int  # 优先级
  status: str  # active / inactive
  created_at: datetime
}
```

**API：**
- `GET /api/parse-configs` - 获取所有解析配置
- `POST /api/parse-configs` - 添加解析接口
- `PUT /api/parse-configs/{id}` - 更新解析接口
- `DELETE /api/parse-configs/{id}` - 删除解析接口

## 四、前端页面结构

```
/                   # 首页，海报墙
├── /search         # 搜索页
├── /video/:id      # 视频详情页
│   └── /video/:id/play  # 播放页（带测速）
├── /tvbox          # TV Box 频道列表
└── /settings       # 设置页（管理自定义源、解析接口）
```

### 4.1 首页（海报墙）
- 展示豆瓣视频海报瀑布流
- 支持分类切换（全部/电影/剧集）
- 支持搜索

### 4.2 播放页
- 左侧：视频信息（海报、名称、简介）
- 右侧：播放器和源列表
- 自动测速后，源列表按速度排序
- 用户可手动切换源，显示当前速度

## 五、数据流

```
1. 爬虫抓取 TV Box 源 → 存储到 SQLite → 前端展示
2. 爬虫抓取豆瓣信息 → 存储到 SQLite → 前端海报墙
3. 用户点击视频 → 查询该视频的所有播放源 → 后台测速 → 返回排序结果 → 前端展示
4. 用户选择解析源 → iframe 加载解析页面 → 播放视频
```

## 六、定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| 爬取 TV Box 源 | 每 6 小时 | 自动更新 |
| 爬取豆瓣新内容 | 每日一次 | 增量更新 |
| 清理过期源 | 每日一次 | 标记超时不响应的源 |

## 七、部署架构

```yaml
services:
  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - backend

  backend:
    image: python:3.11-slim
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data  # SQLite 数据持久化
      - ./backend:/app
    working_dir: /app
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    environment:
      - PYTHONPATH=/app
```

## 八、开发阶段划分

**第一阶段：项目搭建**
- [ ] 初始化前端 Vue3 + Vite 项目
- [ ] 初始化后端 FastAPI 项目
- [ ] 配置 Docker Compose

**第二阶段：TV Box 源管理**
- [ ] 数据库模型
- [ ] 爬取 TV Box 源
- [ ] 用户自定义源 CRUD
- [ ] 源列表页面
- [ ] 测速功能

**第三阶段：豆瓣数据**
- [ ] 爬取豆瓣数据
- [ ] 海报墙页面
- [ ] 搜索功能

**第四阶段：播放功能**
- [ ] 播放页开发
- [ ] 自动测速 + 推荐最优源
- [ ] 手动切换源

**第五阶段：测试与部署**
- [ ] 手动测试核心流程
- [ ] Docker Compose 部署验证
