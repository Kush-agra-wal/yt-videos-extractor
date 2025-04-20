import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)
YOUTUBE_API_KEYS_STR: Optional[str] = os.getenv('YOUTUBE_API_KEYS')
SEARCH_QUERY: str = os.getenv('SEARCH_QUERY', "cricket")


_fetch_interval_str = os.getenv('FETCH_INTERVAL_SECONDS', "10")
try:
    FETCH_INTERVAL_SECONDS: int = int(_fetch_interval_str)
except ValueError:
    logger.warning(f"Invalid FETCH_INTERVAL_SECONDS value '{_fetch_interval_str}'. Using default 10.")
    FETCH_INTERVAL_SECONDS: int = 10

ELASTICSEARCH_HOST: str = os.getenv('ELASTICSEARCH_HOST', "http://localhost:9200")
ELASTICSEARCH_INDEX: str = os.getenv('ELASTICSEARCH_INDEX', "youtube_videos")

_default_page_size_str = os.getenv('DEFAULT_PAGE_SIZE', "10")
try:
    DEFAULT_PAGE_SIZE: int = int(_default_page_size_str)
except ValueError:
    logger.warning(f"Invalid DEFAULT_PAGE_SIZE value '{_default_page_size_str}'. Using default 10.")
    DEFAULT_PAGE_SIZE: int = 10

_max_page_size_str = os.getenv('MAX_PAGE_SIZE', "50")
try:
    MAX_PAGE_SIZE: int = int(_max_page_size_str)
except ValueError:
    logger.warning(f"Invalid MAX_PAGE_SIZE value '{_max_page_size_str}'. Using default 50.")
    MAX_PAGE_SIZE: int = 50


YOUTUBE_API_KEYS: List[str] = []
if YOUTUBE_API_KEYS_STR:
    YOUTUBE_API_KEYS = [key.strip() for key in YOUTUBE_API_KEYS_STR.split(',') if key.strip()]




if __name__ == "__main__":
    if not YOUTUBE_API_KEYS:
        logger.error("CRITICAL: YOUTUBE_API_KEYS environment variable is not set or is empty. YouTube fetching will fail.")
        print("\nWarning: No YouTube API keys found!")