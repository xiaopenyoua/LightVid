"""
TMDB 数据同步服务
用于定时同步 TMDB 数据到本地数据库缓存
"""
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.tmdb_genre import TmdbGenre
from models.tmdb_cached_list import TmdbCachedList
from config import TMDB_API_KEY, TMDB_BASE_URL
from services.tmdb_service import tmdb_service

LANGUAGE = "zh-CN"


class SyncService:
    """TMDB 数据同步服务"""

    def __init__(self, db: Session):
        self.db = db
        self.api_key = TMDB_API_KEY
        self.base_url = TMDB_BASE_URL

    def _fetch_json(self, url: str, params: dict, max_retries: int = 3) -> dict:
        """带重试的 HTTP GET，返回 JSON"""
        for attempt in range(max_retries):
            try:
                response = httpx.Client(timeout=15.0).get(url, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"[Sync] Failed after {max_retries} attempts: {e}")
                    return {}
                import time
                time.sleep(1)
        return {}

    async def sync_genres(self):
        """同步电影和剧集类型列表到本地数据库"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 获取电影类型
            movie_resp = await client.get(
                f"{self.base_url}/genre/movie/list",
                params={"api_key": self.api_key, "language": LANGUAGE}
            )
            movie_genres = movie_resp.json().get("genres", [])

            # 获取剧集类型
            tv_resp = await client.get(
                f"{self.base_url}/genre/tv/list",
                params={"api_key": self.api_key, "language": LANGUAGE}
            )
            tv_genres = tv_resp.json().get("genres", [])

        # 写入数据库
        self.db.query(TmdbGenre).delete()  # 清空旧数据

        for g in movie_genres:
            self.db.add(TmdbGenre(tmdb_id=g["id"], name=g["name"], media_type="movie"))

        for g in tv_genres:
            self.db.add(TmdbGenre(tmdb_id=g["id"], name=g["name"], media_type="tv"))

        self.db.commit()
        return len(movie_genres) + len(tv_genres)

    async def sync_trending(self):
        """同步 Trending（本周热门）"""
        url = f"{self.base_url}/trending/all/week"
        params = {"api_key": self.api_key, "language": LANGUAGE}

        data = self._fetch_json(url, params)
        results = data.get("results", [])
        if not results:
            return 0

        self.db.query(TmdbCachedList).filter_by(list_type="trending").delete()

        now = datetime.utcnow()
        for item in results:
            # 判断 media_type
            if item.get("media_type") == "movie" or not item.get("first_air_date"):
                item_media = "movie"
            else:
                item_media = "tv"

            formatted = tmdb_service.format_tmdb_item(item, item_media)
            self.db.add(TmdbCachedList(
                list_type="trending",
                media_type=formatted["media_type"],
                tmdb_id=formatted["tmdb_id"],
                title=formatted["title"],
                poster_url=formatted["poster_url"],
                backdrop_url=formatted["backdrop_url"],
                vote_average=formatted["vote_average"],
                vote_count=formatted["vote_count"],
                popularity=formatted["popularity"],
                overview=formatted["overview"],
                release_date=formatted["release_date"],
                genre_ids=formatted["genre_ids"],
                season_number=formatted["season_number"],
                cached_at=now,
            ))

        self.db.commit()
        return len(results)

    async def sync_popular(self):
        """同步 Popular（热门电影和剧集）"""
        # 获取热门电影
        movie_url = f"{self.base_url}/movie/popular"
        movie_params = {"api_key": self.api_key, "language": LANGUAGE}
        movie_data = self._fetch_json(movie_url, movie_params)
        movie_results = movie_data.get("results", [])

        self.db.query(TmdbCachedList).filter_by(list_type="popular", media_type="movie").delete()
        now = datetime.utcnow()
        for item in movie_results:
            formatted = tmdb_service.format_tmdb_item(item, "movie")
            self.db.add(TmdbCachedList(
                list_type="popular",
                media_type="movie",
                tmdb_id=formatted["tmdb_id"],
                title=formatted["title"],
                poster_url=formatted["poster_url"],
                backdrop_url=formatted["backdrop_url"],
                vote_average=formatted["vote_average"],
                vote_count=formatted["vote_count"],
                popularity=formatted["popularity"],
                overview=formatted["overview"],
                release_date=formatted["release_date"],
                genre_ids=formatted["genre_ids"],
                season_number=formatted["season_number"],
                cached_at=now,
            ))

        # 获取热门剧集
        tv_url = f"{self.base_url}/tv/popular"
        tv_params = {"api_key": self.api_key, "language": LANGUAGE}
        tv_data = self._fetch_json(tv_url, tv_params)
        tv_results = tv_data.get("results", [])

        self.db.query(TmdbCachedList).filter_by(list_type="popular", media_type="tv").delete()
        for item in tv_results:
            formatted = tmdb_service.format_tmdb_item(item, "tv")
            self.db.add(TmdbCachedList(
                list_type="popular",
                media_type="tv",
                tmdb_id=formatted["tmdb_id"],
                title=formatted["title"],
                poster_url=formatted["poster_url"],
                backdrop_url=formatted["backdrop_url"],
                vote_average=formatted["vote_average"],
                vote_count=formatted["vote_count"],
                popularity=formatted["popularity"],
                overview=formatted["overview"],
                release_date=formatted["release_date"],
                genre_ids=formatted["genre_ids"],
                season_number=formatted["season_number"],
                cached_at=now,
            ))

        self.db.commit()
        return len(movie_results) + len(tv_results)

    async def sync_top_rated(self):
        """同步 Top Rated（高分电影和剧集）"""
        # 获取高分电影
        movie_url = f"{self.base_url}/movie/top_rated"
        movie_params = {"api_key": self.api_key, "language": LANGUAGE}
        movie_data = self._fetch_json(movie_url, movie_params)
        movie_results = movie_data.get("results", [])

        self.db.query(TmdbCachedList).filter_by(list_type="top_rated", media_type="movie").delete()
        now = datetime.utcnow()
        for item in movie_results:
            formatted = tmdb_service.format_tmdb_item(item, "movie")
            self.db.add(TmdbCachedList(
                list_type="top_rated",
                media_type="movie",
                tmdb_id=formatted["tmdb_id"],
                title=formatted["title"],
                poster_url=formatted["poster_url"],
                backdrop_url=formatted["backdrop_url"],
                vote_average=formatted["vote_average"],
                vote_count=formatted["vote_count"],
                popularity=formatted["popularity"],
                overview=formatted["overview"],
                release_date=formatted["release_date"],
                genre_ids=formatted["genre_ids"],
                season_number=formatted["season_number"],
                cached_at=now,
            ))

        # 获取高分剧集
        tv_url = f"{self.base_url}/tv/top_rated"
        tv_params = {"api_key": self.api_key, "language": LANGUAGE}
        tv_data = self._fetch_json(tv_url, tv_params)
        tv_results = tv_data.get("results", [])

        self.db.query(TmdbCachedList).filter_by(list_type="top_rated", media_type="tv").delete()
        for item in tv_results:
            formatted = tmdb_service.format_tmdb_item(item, "tv")
            self.db.add(TmdbCachedList(
                list_type="top_rated",
                media_type="tv",
                tmdb_id=formatted["tmdb_id"],
                title=formatted["title"],
                poster_url=formatted["poster_url"],
                backdrop_url=formatted["backdrop_url"],
                vote_average=formatted["vote_average"],
                vote_count=formatted["vote_count"],
                popularity=formatted["popularity"],
                overview=formatted["overview"],
                release_date=formatted["release_date"],
                genre_ids=formatted["genre_ids"],
                season_number=formatted["season_number"],
                cached_at=now,
            ))

        self.db.commit()
        return len(movie_results) + len(tv_results)

    async def sync_upcoming(self):
        """同步 Upcoming（即将上映，仅电影）"""
        url = f"{self.base_url}/movie/upcoming"
        params = {"api_key": self.api_key, "language": LANGUAGE}
        data = self._fetch_json(url, params)
        results = data.get("results", [])

        self.db.query(TmdbCachedList).filter_by(list_type="upcoming", media_type="movie").delete()
        now = datetime.utcnow()
        for item in results:
            formatted = tmdb_service.format_tmdb_item(item, "movie")
            self.db.add(TmdbCachedList(
                list_type="upcoming",
                media_type="movie",
                tmdb_id=formatted["tmdb_id"],
                title=formatted["title"],
                poster_url=formatted["poster_url"],
                backdrop_url=formatted["backdrop_url"],
                vote_average=formatted["vote_average"],
                vote_count=formatted["vote_count"],
                popularity=formatted["popularity"],
                overview=formatted["overview"],
                release_date=formatted["release_date"],
                genre_ids=formatted["genre_ids"],
                season_number=formatted["season_number"],
                cached_at=now,
            ))

        self.db.commit()
        return len(results)

    def cleanup_old_cache(self, max_age_hours: int = 24):
        """清理超过指定时间的缓存"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        deleted = self.db.query(TmdbCachedList).filter(
            TmdbCachedList.cached_at < cutoff
        ).delete()
        self.db.commit()
        return deleted
