from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime, timezone

class Video(BaseModel):
    """video doc in es."""
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    published_at: datetime = Field(..., description="Video publishing timestamp")
    thumbnails: HttpUrl = Field(..., description="thumbnail")
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VideoListResponse(BaseModel):
    """response for paginated video lists."""
    total: int = Field(..., description="Total number of videos matching the criteria")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of videos per page")
    videos: List[Video] = Field(..., description="List of video objects for the current page")