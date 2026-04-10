# LightVid 项目设计规格

> **竞品参考：** Younify TV、AgileTV、IPTV Smarters Pro、PlayBox IPTV
> **研究日期：** 2026/04/10

## 一、项目概述

**项目名：** LightVid（轻影）
**类型：** 视频资源聚合 + 播放的 Web 应用
**定位：** 单用户本地使用，无需账号系统

**差异化机会：** 完全本地化、免费开源、整合免费解析接口、续播和播放历史

---

## 二、技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | Vue3 + Vite + Element Plus | 现代前端框架，组件丰富 |
| 后端 | FastAPI + SQLAlchemy | 异步高性能 API 框架 |
| 数据库 | SQLite | 轻量零配置，本地持久化 |
| 爬虫 | httpx + BeautifulSoup + lxml | 异步 HTTP + HTML 解析 |
| 部署 | Docker Compose | 一键部署 |

---

## 三、竞品分析

| 竞品 | 核心功能 | LightVid 可借鉴点 |
|------|---------|------------------|
| Younify TV | 多平台 watchlist 整合、统一搜索、续播 | 本地源聚合 + 续播功能 |
| AgileTV | 超级聚合、无缝导航、个性化推荐 | 单一界面聚合多源体验 |
| IPTV Smarters | 格式兼容、内容管理、高级播放控制 | 播放控制、源质量显示 |
| PlayBox IPTV | 玻璃拟态、流畅 UX | 现代暗色主题设计 |

---

## 四、功能模块

### 4.1 TV Box 源管理

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
  url: str  # URL 验证：必须 http:// 或 https:// 开头
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
- `POST /api/sources/speed-test/{id}` - 单源测速

---

### 4.2 豆瓣数据获取

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
- `GET /api/douban/search?q={keyword}` - 搜索豆瓣（本地数据库模糊搜索）
- `POST /api/douban/crawl` - 爬取指定豆瓣 ID

---

### 4.3 播放链接聚合

**功能：**
- 从各视频平台获取播放页面 URL
- 对接视频解析接口
- 播放源按速度排序

**API：**
- `GET /api/play/sources` - 获取所有可用播放源（按速度排序）

---

### 4.4 智能测速与播放

**功能：**
- 进入播放页后自动对所有可用源测速
- 按速度排序，默认推荐最优源
- 用户可手动切换解析源和视频平台
- 前端播放器使用 iframe 嵌入解析页面

**API：**
- `GET /api/play/{source_id}` - 获取指定源信息

---

### 4.5 解析接口管理

**数据模型：**
```
ParseConfig {
  id: int (PK)
  name: str  # 如 "虾米解析"
  base_url: str  # 如 "https://jx.xmflv.com/?url="
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

---

### 4.6 观看历史与续播 ⭐ 竞品启发

**功能：**
- 自动记录每个视频的上次播放位置
- 首页展示"继续观看"模块
- 一键续播到上次位置

**数据模型：**
```
WatchHistory {
  id: int (PK)
  douban_id: str  # 关联 DoubanVideo
  source_id: int  # 上次播放的源
  progress: float  # 播放进度（秒）
  duration: float  # 视频总时长（秒）
  last_watched: datetime
  updated_at: datetime
}
```

**API：**
- `GET /api/history` - 获取观看历史列表
- `POST /api/history` - 记录播放进度
- `DELETE /api/history/{douban_id}` - 删除历史记录

---

### 4.7 收藏与心愿单 ⭐ 竞品启发

**功能：**
- 用户可收藏感兴趣的视频
- 收藏列表展示
- 快速访问收藏内容

**数据模型：**
```
Favorite {
  id: int (PK)
  douban_id: str  # 关联 DoubanVideo
  created_at: datetime
}
```

**API：**
- `GET /api/favorites` - 获取收藏列表
- `POST /api/favorites/{douban_id}` - 添加收藏
- `DELETE /api/favorites/{douban_id}` - 取消收藏

---

## 五、前端页面结构

```
/                   # 首页，海报墙
├── /search         # 搜索页
├── /video/:id      # 视频详情页
│   └── /video/:id/play  # 播放页（带测速）
├── /tvbox          # TV Box 频道列表
├── /history        # 观看历史 ⭐
├── /favorites      # 我的收藏 ⭐
└── /settings       # 设置页（管理自定义源、解析接口）
```

### 5.1 首页（海报墙）
- 展示豆瓣视频海报瀑布流
- 支持分类切换（全部/电影/剧集）
- 支持搜索
- **新增：** "继续观看" 模块（观看历史入口）
- **新增：** "我的收藏" 模块（收藏入口）

### 5.2 播放页
- 左侧：视频信息（海报、名称、简介）
- 右侧：播放器和源列表
- 自动测速后，源列表按速度排序
- 用户可手动切换源，显示当前速度
- **新增：** 收藏按钮、播放进度记录

### 5.3 UI 设计参考（PlayBox 风格）
- 暗色主题背景（#080C0D 深色系）
- 玻璃拟态效果
- 发光高亮强调
- 流畅的源切换动画
- 清晰的分类导航

---

## 六、数据流

```
1. 爬虫抓取 TV Box 源 → 存储到 SQLite → 前端展示
2. 爬虫抓取豆瓣信息 → 存储到 SQLite → 前端海报墙
3. 用户点击视频 → 查询所有播放源 → 后台测速 → 返回排序结果 → 前端展示
4. 用户选择解析源 → iframe 加载解析页面 → 播放视频
5. 播放过程中 → 记录播放进度 → 下次打开可直接续播
6. 用户收藏视频 → 存储到 SQLite → 收藏列表展示
```

---

## 七、定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| 爬取 TV Box 源 | 每 6 小时 | 自动更新 |
| 爬取豆瓣新内容 | 每日一次 | 增量更新 |
| 清理过期源 | 每日一次 | 标记超时不响应的源 |

---

## 八、部署架构

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
      - ./data:/app/data  # SQLite 数据持久化
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

---

## 九、开发阶段划分

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
- [ ] 解析接口管理

**第五阶段：观看历史与收藏**
- [ ] 观看历史模型与 API
- [ ] 收藏功能模型与 API
- [ ] 历史/收藏页面开发

**第六阶段：测试与部署**
- [ ] 手动测试核心流程
- [ ] Docker Compose 部署验证
