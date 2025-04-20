import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from elasticsearch import AsyncElasticsearch, NotFoundError, RequestError

from .config import ELASTICSEARCH_HOST, ELASTICSEARCH_INDEX
from .pydantic_models import Video

logger = logging.getLogger(__name__)

# Global Elasticsearch client instance
es_client: Optional[AsyncElasticsearch] = None

def get_es_client():
    global es_client
    if es_client is None:
        logger.info(f"Initializing Elasticsearch client for host: {ELASTICSEARCH_HOST}")
        es_client = AsyncElasticsearch(hosts=[ELASTICSEARCH_HOST],basic_auth=("elastic", "12345678"))
        logger.info("Elasticsearch client initialized.")
    return es_client

async def close_es_client():
    """Closes the Elasticsearch client connection."""
    global es_client
    if es_client:
        logger.info("Closing Elasticsearch client connection.")
        await es_client.close()
        es_client = None

async def ensure_index_exists():
    """Creates the Elasticsearch index with the correct mapping if it doesn't exist."""
    client = get_es_client()
    index_name = ELASTICSEARCH_INDEX
    try:
        if not await client.indices.exists(index=index_name):
            logger.info(f"Index '{index_name}' not found. Creating...")
            mapping = {
                "properties": {
                    "video_id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "standard"},
                    "description": {"type": "text", "analyzer": "standard"},
                    "published_at": {"type": "date"},
                    "thumbnails": {"type": "text"},
                    "indexed_at": {"type": "date"}
                }
            }

            await client.indices.create(index=index_name, mappings=mapping)
            logger.info(f"Index '{index_name}' created successfully.")
        else:
            logger.info(f"Index '{index_name}' already exists.")
    except RequestError as e:
        logger.error(f"Failed to create or check index '{index_name}': {e.info}", exc_info=True)
        # Depending on the error, you might want to raise it or handle differently
        if 'resource_already_exists_exception' not in str(e): # Ignore if it already exists concurrently
             raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during index check/creation: {e}", exc_info=True)
        raise

async def index_video(video: Video):
    """Indexes or updates a single video document in Elasticsearch."""
    client = get_es_client()
    index_name = ELASTICSEARCH_INDEX
    try:
        # Use video_id as the document ID for automatic updates (upsert)
        await client.index(
            index=index_name,
            id=video.video_id,
            document=video.model_dump(mode='json') # Use model_dump for Pydantic v2+
        )
        # logger.debug(f"Successfully indexed video ID: {video.video_id}")
    except Exception as e:
        logger.error(f"Failed to index video ID {video.video_id}: {e}", exc_info=True)

async def get_latest_video_timestamp() -> Optional[datetime]:
    """Fetches the 'published_at' timestamp of the most recent video in the index."""
    client = get_es_client()
    index_name = ELASTICSEARCH_INDEX
    try:
        # Check if index exists first to avoid error on empty index
        if not await client.indices.exists(index=index_name):
             logger.warning(f"Index '{index_name}' does not exist yet. Cannot get latest timestamp.")
             return None

        resp = await client.search(
            index=index_name,
            size=1,
            sort=[{"published_at": "desc"}],
            _source=["published_at"] # Only fetch the required field
        )
        hits = resp.get('hits', {}).get('hits', [])
        if hits:
            timestamp_str = hits[0]['_source']['published_at']
            try:
                # Let Pydantic handle parsing, including timezone awareness
                return Video.model_validate({'published_at': timestamp_str}).published_at
            except Exception as parse_err:
                 logger.error(f"Failed to parse timestamp '{timestamp_str}': {parse_err}")
                 return None # Or handle error appropriately
        else:
            logger.info(f"No videos found in index '{index_name}'. Returning None for timestamp.")
            return None
    except NotFoundError:
         logger.warning(f"Index '{index_name}' not found when querying for latest timestamp.")
         return None
    except Exception as e:
        logger.error(f"Error fetching latest video timestamp: {e}", exc_info=True)
        return None # Don't block fetching if this fails

async def get_videos_paginated(page: int, size: int) -> Tuple[List[Video], int]:
    """Retrieves stored videos, sorted by published_at descending, with pagination."""
    client = get_es_client()
    index_name = ELASTICSEARCH_INDEX
    if page < 1: page = 1
    from_ = (page - 1) * size

    try:
        resp = await client.search(
            index=index_name,
            size=size,
            from_=from_,
            sort=[{"published_at": "desc"}],
            track_total_hits=True # Ensure total count is accurate
        )
        total_hits = resp['hits']['total']['value']
        videos = [Video.model_validate(hit['_source']) for hit in resp['hits']['hits']]
        return videos, total_hits
    except NotFoundError:
        logger.warning(f"Index '{index_name}' not found during paginated fetch.")
        return [], 0
    except Exception as e:
        logger.error(f"Error fetching paginated videos: {e}", exc_info=True)
        return [], 0 # Return empty on error

async def search_videos(query: str) -> Tuple[List[Video], int]:
    """Searches videos by title and description using a multi_match query, ignoring pagination."""
    client = get_es_client()
    index_name = ELASTICSEARCH_INDEX

    # Set a large size to get all the results
    size = 10000  # You can adjust this as needed (max size Elasticsearch can return in a single request)
    
    search_query = {
        "multi_match": {
            "query": query,
            "fields": ["title", "description"],
            "type": "best_fields",  # Or "phrase_prefix" for better partial matches from start
            "fuzziness": "AUTO"  # Allows for some typos
        }
    }

    try:
        resp = await client.search(
            index=index_name,
            query=search_query,
            size=size,
            track_total_hits=True  # Tracks the total number of hits
        )

        # Extract total hits and videos
        total_hits = resp['hits']['total']['value']
        videos = [Video.model_validate(hit['_source']) for hit in resp['hits']['hits']]
        return videos, total_hits

    except NotFoundError:
        logger.warning(f"Index '{index_name}' not found during search.")
        return [], 0
    except Exception as e:
        logger.error(f"Error searching videos for query '{query}': {e}", exc_info=True)
        return [], 0  # Return empty on error
