from contextlib import asynccontextmanager
from typing import AsyncGenerator

import fastapi
import logging
from aiohttp_client_cache.session import CachedSession
from aiohttp_client_cache.backends.sqlite import SQLiteBackend
from fake_useragent import UserAgent

from .utils import fetch_post_info, shorten_url


@asynccontextmanager
async def app_lifespan(app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    app.state.client = CachedSession(
        cache=SQLiteBackend(cache_name="cache.db", expire_after=3600),
    )
    try:
        yield
    finally:
        await app.state.client.close()


ua = UserAgent()
logger = logging.getLogger("uvicorn")
app = fastapi.FastAPI(lifespan=app_lifespan)


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxfacebook")


async def embed_fixer(request: fastapi.Request, url: str) -> fastapi.responses.Response:
    if "Discordbot" not in request.headers.get("User-Agent", ""):
        return fastapi.responses.RedirectResponse(url)

    try:
        post = await fetch_post_info(app.state.client, url=url)
    except Exception:
        logger.exception(f"Error fetching post info")
        return fastapi.responses.RedirectResponse(url)

    if post.error:
        return fastapi.responses.RedirectResponse(url)

    if not post.description:
        post.description = "Facebook Video"

    if post.downloads:
        download = next(
            (d for d in post.downloads if d.ext == "mp4" and "hd" in d.format_id), None
        )
        if download:
            video_url = await shorten_url(app.state.client, url=download.url)
        else:
            logger.error(f"No HD downloads found: {post}")
            return fastapi.responses.RedirectResponse(url)
    else:
        logger.error(f"No downloads found: {post}")
        return fastapi.responses.RedirectResponse(url)

    logger.info(f"Video URL: {video_url}")

    html = f"""
    <html>
    <head>
        <meta property="charset" content="utf-8">
        <meta property="theme-color" content="#395898">
        <meta property="og:title" content="{post.description}">
        <meta property="og:type" content="video">
        <meta property="og:site_name" content="Facebook Reels">
        <meta property="og:url" content="{post.source}">
        <meta property="og:video" content="{video_url}">
        <meta property="og:video:secure_url" content="{video_url}">
        <meta property="og:video:type" content="video/mp4">
    </head>
    </html>
    """
    return fastapi.responses.HTMLResponse(html)


@app.get("/share/r/{reel_id}")
async def share_reel(
    request: fastapi.Request, reel_id: str
) -> fastapi.responses.Response:
    url = f"https://www.facebook.com/share/r/{reel_id}"
    return await embed_fixer(request, url)


@app.get("/reel/{reel_id}")
async def reel(request: fastapi.Request, reel_id: str) -> fastapi.responses.Response:
    url = f"https://www.facebook.com/reel/{reel_id}"
    return await embed_fixer(request, url)


@app.get("/share/v/{video_id}")  # NOTE: Unstable
async def share_video(
    request: fastapi.Request, video_id: str
) -> fastapi.responses.Response:
    # Find the final url after redirection
    async with app.state.client.get(
        f"https://www.facebook.com/share/v/{video_id}",
        headers={"User-Agent": ua.random},
    ) as response:
        url = response.url
    logger.info(f"Final URL: {url}")
    return await embed_fixer(request, url)


@app.get("/watch")
async def watch(request: fastapi.Request) -> fastapi.responses.Response:
    params = dict(request.query_params)
    return await embed_fixer(
        request,
        f"https://www.facebook.com/watch/?{'&'.join(f'{k}={v}' for k, v in params.items())}",
    )
