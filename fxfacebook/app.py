from contextlib import asynccontextmanager
from typing import AsyncGenerator

import fastapi
import httpx

from .utils import fetch_post_info, shorten_url


@asynccontextmanager
async def app_lifespan(app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    app.state.client = httpx.AsyncClient()
    try:
        yield
    finally:
        await app.state.client.aclose()


app = fastapi.FastAPI(lifespan=app_lifespan)


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxfacebook")


async def embed_fixer(url: str) -> fastapi.responses.HTMLResponse:
    post = await fetch_post_info(app.state.client, url=url)

    if post.error:
        return fastapi.responses.HTMLResponse(f"<p>{post.error}</p>")

    if not post.description:
        post.description = "Facebook Video"

    if post.downloads:
        download = next(
            (d for d in post.downloads if d.ext == "mp4" and "hd" in d.format_id), None
        )
        if download:
            video_url = await shorten_url(app.state.client, url=download.url)
        else:
            return fastapi.responses.HTMLResponse(f"<p>No video found</p>")
    else:
        return fastapi.responses.HTMLResponse(f"<p>No video found</p>")

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
        
        <script>
            window.onload = function() {{
                window.location.href = "{post.source}";
            }}
        </script>
    </head>
    
    <body>
        <p>Redirecting you to the Facebook reel...</p>
        <p>If you are not redirected automatically, <a href="{post.source}">click here</a>.</p>
    </body>
    
    </html>
    """
    return fastapi.responses.HTMLResponse(html)


@app.get("/share/r/{reel_id}")
async def share_reel(reel_id: str) -> fastapi.responses.HTMLResponse:
    return await embed_fixer(f"https://www.facebook.com/share/r/{reel_id}")


@app.get("/reel/{reel_id}")
async def reel(reel_id: str) -> fastapi.responses.HTMLResponse:
    return await embed_fixer(f"https://www.facebook.com/reel/{reel_id}")


@app.get("/share/v/{video_id}")
async def share_video(video_id: str) -> fastapi.responses.HTMLResponse:
    # Find the final url after redirection
    response = await app.state.client.get(
        f"https://www.facebook.com/share/v/{video_id}", follow_redirects=True
    )
    url = response.url
    return await embed_fixer(url)


@app.get("/watch")
async def watch(request: fastapi.Request) -> fastapi.responses.HTMLResponse:
    params = dict(request.query_params)
    return await embed_fixer(
        f"https://www.facebook.com/watch/?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    )
