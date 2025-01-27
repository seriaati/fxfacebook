from aiohttp_client_cache.session import CachedSession

from .schema import PostInfo

API_KEY = "vkrdownloader"


async def shorten_url(client: CachedSession, *, url: str) -> str:
    api_url = "https://tinyurl.com/api-create.php"
    params = {"url": url}

    async with client.get(api_url, params=params) as response:
        return (await response.text()).strip()


async def fetch_post_info(client: CachedSession, *, url: str) -> PostInfo:
    api_url = f"https://vkrdownloader.xyz/server/?api_key={API_KEY}&vkr={url}"
    async with client.get(api_url) as response:
        data = await response.json()
    return PostInfo(**data["data"])
