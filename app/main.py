import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException

from .config import DEFAULT_PAGE_SIZE,FETCH_INTERVAL_SECONDS,MAX_PAGE_SIZE,SEARCH_QUERY
from .pydantic_models import VideoListResponse
from . import es_utils
from . import yt_utils
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

background_task = None
shutdown_event = asyncio.Event()

async def periodic_fetch():
    """Background task to periodically fetch videos from YouTube."""
    logger.info("Starting periodic YouTube video fetch task...")
    while not shutdown_event.is_set():
        try:
            logger.info("Running fetch cycle...")
            latest_timestamp = await es_utils.get_latest_video_timestamp()

            api_key = yt_utils.get_next_api_key()
            if not api_key:
                logger.error("No YouTube API key available. Skipping fetch cycle.")
                await asyncio.sleep(FETCH_INTERVAL_SECONDS * 5)
                continue

            try:
                new_videos = await yt_utils.fetch_latest_videos(
                    search_query=SEARCH_QUERY,
                    api_key=api_key,
                    published_after=latest_timestamp
                )
            except Exception as fetch_err:
                 logger.error(f"Error during yt_utils.fetch_latest_videos: {fetch_err}", exc_info=True)
                 new_videos = []

            if new_videos:
                logger.info(f"Fetched {len(new_videos)} new videos. Indexing...")
                indexed_count = 0
                for video in new_videos:
                    try:
                        await es_utils.index_video(video)
                        indexed_count += 1
                    except Exception as index_err:
                        logger.error(f"Failed to index video {video.video_id}: {index_err}", exc_info=True)
                        
                logger.info(f"Successfully indexed {indexed_count}/{len(new_videos)} videos.")
            else:
                logger.info("No new videos fetched in this cycle.")

            try:
                 await asyncio.wait_for(shutdown_event.wait(), timeout=FETCH_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                 pass

        except Exception as e:
            logger.error(f"Error in periodic_fetch loop: {e}", exc_info=True)
            await asyncio.sleep(FETCH_INTERVAL_SECONDS)

    logger.info("Periodic YouTube video fetch task stopped.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    global background_task
    logger.info("Application startup...")

    # initialize ES
    es_client = es_utils.get_es_client()
    try:
        if not await es_client.ping():
             raise ConnectionError("Elasticsearch connection failed!")
        logger.info("Elasticsearch connection successful.")
        await es_utils.ensure_index_exists()
    except Exception as e:
         logger.critical(f"Failed to connect to Elasticsearch or ensure index exists: {e}", exc_info=True)
         raise RuntimeError(f"Elasticsearch setup failed: {e}") from e


    # Start the background task
    shutdown_event.clear()
    loop = asyncio.get_running_loop()
    background_task = loop.create_task(periodic_fetch())
    logger.info("Background fetch task created.")

    yield


    logger.info("Application shutdown...")

    shutdown_event.set()
    if background_task:
        try:
            await asyncio.wait_for(background_task, timeout=FETCH_INTERVAL_SECONDS + 5)
            logger.info("Background task finished.")
        except asyncio.TimeoutError:
            logger.warning("Background task did not finish in time. Cancelling.")
            background_task.cancel()
        except Exception as e:
             logger.error(f"Error during background task shutdown: {e}", exc_info=True)

    # Close Elasticsearch client
    await es_utils.close_es_client()
    logger.info("Application shutdown complete.")


# FastAPI Instance
app = FastAPI(
    title="YouTube Video Fetcher API",
    description="API to fetch and search latest YouTube videos based on a query.",
    version="1.0.0",
    lifespan=lifespan
)

# API Endpoints

@app.get("/videos", response_model=VideoListResponse)
async def get_videos(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Number of videos per page")
):
    """
    Retrieves stored videos, sorted by publishing date-time in descending order (newest first).
    """
    logger.info(f"Received request for /videos: page={page}, size={size}")
    try:
        videos, total = await es_utils.get_videos_paginated(page=page, size=size)
        return VideoListResponse(
            total=total,
            page=page,
            size=len(videos),
            videos=videos
        )
    except Exception as e:
        logger.error(f"Error processing /videos request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching videos.")


@app.get("/search", response_model=VideoListResponse)
async def search_videos_api(
    q: str = Query(..., min_length=1, description="Search query string")
):
    """
    Searches stored videos by title and description.
    Supports partial matches and typo tolerance (fuzziness).
    Results are filtered based on the provided score threshold.
    """
    logger.info(f"Received request for /search: q='{q}'")
    try:
        videos, total = await es_utils.search_videos(query=q)
        return VideoListResponse(
            total=total,
            page=1,  # no pagination
            size=len(videos),
            videos=videos
        )
    except Exception as e:
        logger.error(f"Error processing /search request for query '{q}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while searching videos.")


@app.get("/health", status_code=200)
async def health_check():
    """Basic health check endpoint."""
    es_ping = False
    try:
        client = es_utils.get_es_client()
        if client:
            es_ping = await client.ping()
    except Exception:
        pass

    return {"status": "ok", "elasticsearch_connected": es_ping}

