import httpx

from .schema import PostInfo

API_KEY = "vkrdownloader"


async def shorten_url(client: httpx.AsyncClient, *, url: str) -> str:
    api_url = "https://tinyurl.com/api-create.php"
    params = {"url": url}

    response = await client.get(api_url, params=params)
    return response.text.strip()


async def fetch_post_info(client: httpx.AsyncClient, *, url: str) -> PostInfo:
    api_url = f"https://vkrdownloader.xyz/server/?api_key={API_KEY}&vkr={url}"
    response = await client.get(
        api_url,
        timeout=10,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    data = response.json()
    return PostInfo(**data["data"])
