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
            # 使用 lxml 解析器
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
