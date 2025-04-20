# YouTube Video Fetcher API

This application fetches YouTube videos based on a search query, stores them in Elasticsearch, and provides an API to retrieve and search these videos.
*   periodically runs search query on youtube api (with multiple api keys rotating)
*   saves new search reasults (after last published index) in elasticsearch
*   /videos to get paginated output of saved videos
*   /search takes query and does fuzzysearch on title+description to give top matching results



## Prerequisites

*   Python 3.8+
*   pip
*   An Elasticsearch instance (v8.18.0) accessible from the application.
*   Docker and Docker Compose (Optional).

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r ../requirements.txt
    ```
    *(Note: Assuming you are running this from within the `app` directory, otherwise adjust the path to `requirements.txt`)*

4.  **Configure Environment Variables:**
    *   Copy the sample environment file from the root directory:
        ```bash
        cp ../.env.sample .env
        ```
        *(Note: This creates the `.env` file inside the `app` directory. The application currently looks for `.env` in the parent directory (`../.env`). Ensure the `.env` file is placed in the project root, one level above `app/`)*
    *   Edit the `.env` file in the project root directory and provide the necessary values:
        *   `YOUTUBE_API_KEYS`: A comma-separated list of your YouTube Data API v3 keys.
        *   `ELASTICSEARCH_HOST`: The URL of your Elasticsearch instance (e.g., `http://localhost:9200`).
        *   `SEARCH_QUERY`: The default query to search for videos (e.g., `cricket`).
        *   Adjust `FETCH_INTERVAL_SECONDS`, `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`, `ELASTICSEARCH_INDEX` if needed.

## Running the Server

Ensure your Elasticsearch instance is running and accessible.

From the project root directory (one level above `app/`), run the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

*   `--reload`: Enables auto-reloading for development.
*   `--host 0.0.0.0`: Makes the server accessible on your network.
*   `--port 8000`: Specifies the port to run on.

The server will start, connect to Elasticsearch, ensure the index exists, and begin fetching videos in the background.

### Alternative: Running with Docker Compose

If you have Docker and Docker Compose installed, you can run the application and an Elasticsearch instance together using the `docker-compose.yml` file located in the project root directory (one level above `app/`).

1.  **Ensure `.env` file is configured:** Make sure you have created and configured the `.env` file in the project root directory as described in the Setup section. The `ELASTICSEARCH_HOST` in the `.env` file should typically be set to `http://elasticsearch:9200` when using Docker Compose, as this is the service name defined in `docker-compose.yml`.

2.  **Run Docker Compose:** From the project root directory (where `docker-compose.yml` is located), run:
    ```bash
    docker-compose up -d --build
    ```
    *   `--build`: Forces Docker to rebuild the application image if changes were made.
    *   `-d`: Runs the containers in detached mode (in the background).

This command will build the FastAPI application image (if it doesn't exist or `--build` is used), start the application container, and start an Elasticsearch container. The application will be accessible at `http://localhost:8000`.

To stop the containers:
```bash
docker-compose down
```

## API Endpoints

The API documentation is available interactively via Swagger UI at `http://localhost:8000/docs` or ReDoc at `http://localhost:8000/redoc` when the server is running.

### 1. Get Videos

Retrieves stored videos, sorted by publishing date-time in descending order.

*   **URL:** `/videos`
*   **Method:** `GET`
*   **Query Parameters:**
    *   `page` (int, optional, default: 1): Page number.
    *   `size` (int, optional, default: 10, max: 50): Number of videos per page.
*   **Example (`curl`):**
    ```bash
    curl "http://localhost:8000/videos?page=1&size=5"
    ```
*   **Sample Output:**
    ```json
    {
      "total": 130,
      "page": 1,
      "size": 5,
      "videos": [
        {
          "video_id": "OksCa4HF88w",
          "title": "ipl 2025 mi win match #shorts #shortsfeed",
          "description": "",
          "published_at": "2025-04-20T20:57:56Z",
          "thumbnails": "https://i.ytimg.com/vi/OksCa4HF88w/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:58:23.629350Z"
        },
        {
          "video_id": "7-7vD7ImG20",
          "title": "IPL 2025: CSK v MI: क्या MI के खिलाफ हार के बाद CSK के लिए बंद हुए प्लेऑफ के दरवाजे? Highlights",
          "description": "This Video is about IPL 2025 Match Between Mumbai Indians (MI) vs Chennai Super Kings (CSK). Discuss About the Highlights ...",
          "published_at": "2025-04-20T20:56:40Z",
          "thumbnails": "https://i.ytimg.com/vi/7-7vD7ImG20/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:56:57.070298Z"
        },
        {
          "video_id": "FSjLFjfO8bU",
          "title": "#kkr vs #gt dream 11 #team#dream11 #ipl #ipl2025",
          "description": "dream11 team #ipl.",
          "published_at": "2025-04-20T20:54:39Z",
          "thumbnails": "https://i.ytimg.com/vi/FSjLFjfO8bU/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:55:25.834824Z"
        },
        {
          "video_id": "hG8BArk420g",
          "title": "🔴Live:Chennai vs Mumbai 36th Match Live | Tata IPL 2025 | CSK VS MI | Live Cricket",
          "description": "Live:Chennai vs Mumbai 36th Match Live | Tata IPL 2025 | CSK VS MI | Live Cricket Note : This is not real cricket, This is a ...",
          "published_at": "2025-04-20T20:54:09Z",
          "thumbnails": "https://i.ytimg.com/vi/hG8BArk420g/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:54:40.143215Z"
        },
        {
          "video_id": "wU2WFeW-Hhg",
          "title": "ipl 2025 #short #ipl2025",
          "description": "",
          "published_at": "2025-04-20T20:53:49Z",
          "thumbnails": "https://i.ytimg.com/vi/wU2WFeW-Hhg/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:54:40.143197Z"
        }
      ]
    }
    ```

### 2. Search Videos

Searches stored videos by title and description.

*   **URL:** `/search`
*   **Method:** `GET`
*   **Query Parameters:**
    *   `q` (string, required): The search query string.
*   **Example (`curl`):**
    ```bash
    curl "http://localhost:8000/search?q=highlights"
    ```
*   **Sample Output (for `q=highlights`):**
    ```json
    {
      "total": 11,
      "page": 1,
      "size": 11,
      "videos": [
        {
          "video_id": "ZlRnuFxOFLI",
          "title": "#mivscsk #fullmatch #highlights #today #rohitsharma 🔥🔥highlight#ipl #2025 #shortvideos #youtubeshort",
          "description": "",
          "published_at": "2025-04-20T18:59:24Z",
          "thumbnails": "https://i.ytimg.com/vi/ZlRnuFxOFLI/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:48:00.539390Z"
        },
        {
          "video_id": "B8o1BWIrXVA",
          "title": "MI vs CSK IPL 2025 Highlights, MI vs CSK Today IPL Match Full Highlights, CSK vs MI Highlights 2025",
          "description": "IPL2025 #MIvCSK #CSKvMI MI vs CSK IPL 2025 Highlights, MI vs CSK Today IPL Match Full Highlights, CSK vs MI Highlights ...",
          "published_at": "2025-04-20T20:07:48Z",
          "thumbnails": "https://i.ytimg.com/vi/B8o1BWIrXVA/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:48:00.539247Z"
        },
        {
          "video_id": "hRfSPvluOlU",
          "title": "CSK Vs MI Match Highlights IPL 2025 | #youtubeshorts #cricketkumbh #shortsfeed",
          "description": "CSK Vs MI Match Highlights IPL 2025 | #youtubeshorts #cricketkumbh #shortsfeed csk vs mi match ipl 2025 csk vs mi highlights ...",
          "published_at": "2025-04-20T20:45:01Z",
          "thumbnails": "https://i.ytimg.com/vi/hRfSPvluOlU/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:48:46.442640Z"
        },
        {
          "video_id": "qO0Uoxqlxsw",
          "title": "Mumbai Indians Vs Chennai Super Kings IPL Match 38 Full Highlights 2025 | MI VS CSK",
          "description": "Mumbai Indians Vs Chennai Super Kings IPL Match 38 Full Highlights 2025 | MI VS CSK #highlights #mivscsk #ipl2025 mi vs csk ...",
          "published_at": "2025-04-20T17:17:06Z",
          "thumbnails": "https://i.ytimg.com/vi/qO0Uoxqlxsw/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:47:14.572925Z"
        },
        {
          "video_id": "JUF3keYeUuc",
          "title": "Rohit-SKY का तूफान, CSK ढेर | MI vs CSK Highlights | IPL 2025 #shortsviral",
          "description": "मुंबई इंडियंस ने दिखाया पुराना जलवा! रोहित शर्मा और सूर्यकुमार ...",
          "published_at": "2025-04-20T20:52:32Z",
          "thumbnails": "https://i.ytimg.com/vi/JUF3keYeUuc/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:54:40.143250Z"
        },
        {
          "video_id": "mZhXJyrGsQM",
          "title": "घर में ढेर बाहर शेर  || IPL MATCH RCB VS PBKS HIGHLIGHTS 2025 #rcbvspbks#iplmatch2025",
          "description": "घर में ढेर बाहर शेर || IPL MATCH RCB VS PBKS HIGHLIGHTS 2025 #rcbvspbks#iplmatch2025 ...",
          "published_at": "2025-04-20T20:18:29Z",
          "thumbnails": "https://i.ytimg.com/vi/mZhXJyrGsQM/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:48:00.539239Z"
        },
        {
          "video_id": "rkGzH247P5k",
          "title": "ipl 2025 rcb vs pbks highlights #shorts #ipl #ipl2025 #rcbvspbks #pbksvsrcb #pbks #rcb #csk #mi",
          "description": "",
          "published_at": "2025-04-20T21:00:27Z",
          "thumbnails": "https://i.ytimg.com/vi/rkGzH247P5k/mqdefault.jpg",
          "indexed_at": "2025-04-20T21:00:40.452185Z"
        },
        {
          "video_id": "JPop8m7qF4k",
          "title": "Rohit Sharma best ining in ipl 2025 #ipl2025 #ipl #t20 #tilak #rohit #sharma #highlights #cricket#ms",
          "description": "Rohit Sharma best ining in ipl 2025 #ipl2025 #ipl #t20 #tilak #rohit #sharma #highlights #cricket#ms ind vs pak #indvspak #ipl ...",
          "published_at": "2025-04-20T20:49:53Z",
          "thumbnails": "https://i.ytimg.com/vi/JPop8m7qF4k/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:51:03.352281Z"
        },
        {
          "video_id": "7-7vD7ImG20",
          "title": "IPL 2025: CSK v MI: क्या MI के खिलाफ हार के बाद CSK के लिए बंद हुए प्लेऑफ के दरवाजे? Highlights",
          "description": "This Video is about IPL 2025 Match Between Mumbai Indians (MI) vs Chennai Super Kings (CSK). Discuss About the Highlights ...",
          "published_at": "2025-04-20T20:56:40Z",
          "thumbnails": "https://i.ytimg.com/vi/7-7vD7ImG20/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:56:57.070298Z"
        },
        {
          "video_id": "98f6VPVlUWI",
          "title": "MI Ne Haraya CSK Ko ki Bejati 😱🔥|News Sports|#ipl #csk #mi #rohitsharma #dhoni",
          "description": "MI Ne Haraya CSK Ko ki Bejati |News Sports|#ipl #csk #mi #rohitsharma #dhoni ipl 2025,ipl 2025 highlights,ipl 2025 news,ipl ...",
          "published_at": "2025-04-20T19:20:01Z",
          "thumbnails": "https://i.ytimg.com/vi/98f6VPVlUWI/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:48:00.539301Z"
        },
        {
          "video_id": "sgHVZQpvbto",
          "title": "MI vs CSK Highlights Score IPL 2025: मुंबई में आया 'हिटमैन' का तूफान, चेन्नई को 9 विकेट से दी मात",
          "description": "",
          "published_at": "2025-04-20T20:44:50Z",
          "thumbnails": "https://i.ytimg.com/vi/sgHVZQpvbto/mqdefault.jpg",
          "indexed_at": "2025-04-20T20:48:46.442646Z"
        }
      ]
    }
    ```
