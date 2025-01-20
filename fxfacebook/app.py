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


@app.get("/share/r/{reel_id}")
async def clip(reel_id: str) -> fastapi.responses.HTMLResponse:
    post = await fetch_post_info(
        app.state.client, url=f"https://www.facebook.com/share/r/{reel_id}"
    )

    if post.error:
        return fastapi.responses.HTMLResponse(f"<p>{post.error}</p>")

    if not post.description:
        post.description = "Facebook Video"

    if post.downloads:
        video_url = await shorten_url(app.state.client, url=post.downloads[-1].url)
    else:
        return fastapi.responses.HTMLResponse(f"<p>No video found</p>")

    html = f"""
    <html>
    
    <head>
        <meta property="charset" content="utf-8">
        <meta property="theme-color" content="#6441a5">
        <meta property="og:title" content="{post.description}">
        <meta property="og:type" content="video">
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
        <p>Redirecting you to the Twitch clip...</p>
        <p>If you are not redirected automatically, <a href="{post.source}">click here</a>.</p>
    </body>
    
    </html>
    """
    return fastapi.responses.HTMLResponse(html)
