from aiohttp_client_cache.session import CachedSession
import os
from dotenv import load_dotenv

from .schema import PostInfo


load_dotenv()
API_KEY = "vkrdownloader"
SHORT_URL_TOKEN = os.getenv("SHORT_URL_TOKEN")


async def shorten_url(client: CachedSession, *, url: str) -> str:
    if SHORT_URL_TOKEN:
        async with client.post(
            "https://link.seria.moe/api/link/create",
            json={"url": url},
            headers={
                "Authorization": f"Bearer {SHORT_URL_TOKEN}",
                "Content-Type": "application/json",
            },
        ) as response:
            data = await response.json()
            return f"https://link.seria.moe/{data['link']['slug']}"

    api_url = "https://tinyurl.com/api-create.php"
    params = {"url": url}
    async with client.get(api_url, params=params) as response:
        return (await response.text()).strip()


async def fetch_post_info(client: CachedSession, *, url: str) -> PostInfo:
    api_url = f"https://vkrdownloader.xyz/server/?api_key={API_KEY}&vkr={url}"
    async with client.get(api_url) as response:
        data = await response.json()
    return PostInfo(**data["data"])
