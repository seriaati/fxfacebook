from pydantic import BaseModel, Field


class PostDownload(BaseModel):
    url: str
    format_id: str
    ext: str


class PostInfo(BaseModel):
    title: str | None
    description: str | None
    source: str
    thumbnail: str | None
    error: str | None
    downloads: list[PostDownload] = Field(default_factory=list)
