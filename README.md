# Steam Games Downloader

A robust application for downloading Steam games using SteamCMD with a web UI and API.

## Features

- Download Steam games using SteamCMD
- Web UI built with Gradio
- REST API with FastAPI
- Anonymous or authenticated Steam login
- Queue system for downloads
- System resource monitoring

## Deployment on Railway

This application is designed to be deployed on Railway. Simply connect your repository to Railway and the application will be deployed automatically.

### Railway Environment Variables

- `PORT`: The port to run the service on (provided by Railway)
- `ENABLE_GRADIO`: Set to "True" to enable the Gradio UI, "False" to use API only
- `MAX_CONCURRENT_DOWNLOADS`: Maximum number of concurrent downloads
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

## API Endpoints

- `POST /downloads`: Start a new download
- `GET /downloads`: Get all downloads
- `GET /downloads/{download_id}`: Get a specific download
- `DELETE /downloads/{download_id}`: Cancel a download
- `GET /system`: Get system metrics
- `GET /health`: Health check endpoint

## Local Development

1. Clone the repository
2. Create a `.env` file based on `.env.example`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python main.py`

## Docker

Build and run with Docker:

```bash
docker build -t steam-downloader .
docker run -p 8000:8000 -v ./data:/data steam-downloader
```

## License

MIT 