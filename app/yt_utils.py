import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from itertools import cycle

from .config import YOUTUBE_API_KEYS
from .pydantic_models import Video

logger = logging.getLogger(__name__)

# Simple API key rotation using itertools.cycle
if YOUTUBE_API_KEYS:
    api_key_cycler = cycle(YOUTUBE_API_KEYS)
    current_api_key_index = 0
else:
    logger.error("FATAL: No YouTube API keys found in settings. Fetching will fail.")
    api_key_cycler = cycle([None])

def get_next_api_key() -> Optional[str]:
    """Gets the next available API key from the cycle."""
    global current_api_key_index
    key = next(api_key_cycler)
    if key:

        current_api_key_index = (current_api_key_index + 1) % len(YOUTUBE_API_KEYS)
        logger.debug(f"Using API Key index: {current_api_key_index}")
        pass
    else:
         logger.warning("No valid API key available.")
    return key

async def fetch_latest_videos(
    search_query: str,
    api_key: str,
    published_after: Optional[datetime] = None
) -> List[Video]:
    """Fetches latest videos from YouTube API for a given query."""
    if not api_key:
        logger.error("Cannot fetch YouTube videos: No API key provided.")
        return []

    YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": search_query,
        "key": api_key,
        "type": "video",
        "order": "date",
        "maxResults": 50 
    }

    if published_after:
        if published_after.tzinfo is None:
             published_after = published_after.replace(tzinfo=timezone.utc)
        published_after_buffered = published_after + timedelta(seconds=1)
        params["publishedAfter"] = published_after_buffered.isoformat(timespec='seconds').replace('+00:00', 'Z')
        logger.info(f"Fetching videos published after: {params['publishedAfter']}")
    else:
        logger.info("Fetching initial set of videos (no publishedAfter timestamp).")


    fetched_videos: List[Video] = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(YOUTUBE_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                logger.info(f"No new videos found for query '{search_query}' since last check.")
                return []

            logger.info(f"Fetched {len(items)} video items from YouTube API.")

            for item in items:
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId")
                published_at_str = snippet.get("publishedAt")
                thumbnails_data = snippet.get("thumbnails", {})

                if not video_id or not published_at_str:
                    logger.warning(f"Skipping item due to missing videoId or publishedAt: {item}")
                    continue

                try:
                    # Parse the timestamp string into a datetime object
                    published_dt = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))

                    video = Video(
                        video_id=video_id,
                        title=snippet.get("title", "No Title"),
                        description=snippet.get("description", "No Description"),
                        published_at=published_dt,
                        thumbnails=thumbnails_data["medium"]['url']
                    )
                    fetched_videos.append(video)
                except Exception as e:
                    logger.error(f"Error parsing video data for ID {video_id}: {e}", exc_info=True)
                    continue

            return fetched_videos

    except httpx.HTTPStatusError as e:

        if e.response.status_code == 403:
            logger.warning(f"YouTube API quota likely exceeded for the current key or access forbidden. Status: {e.response.status_code}. Response: {e.response.text}")
        else:
            logger.error(f"HTTP error fetching YouTube videos: {e.response.status_code} - {e.response.text}", exc_info=True)
        return []
    except httpx.RequestError as e:
        logger.error(f"Network error fetching YouTube videos: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching/processing YouTube videos: {e}", exc_info=True)
        return []