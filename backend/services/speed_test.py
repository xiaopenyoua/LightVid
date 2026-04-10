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
