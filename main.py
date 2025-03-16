#!/usr/bin/env python3
import os
import sys
import signal
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes import router as api_routes
from interface import create_interface
from downloader import DownloadManager
from steam_handler import SteamCMD
from utils import get_system_metrics
from log_config import setup_logging

# Set up logging
logger = setup_logging(
    name="steam_downloader",
    log_file=settings.LOG_DIR / "steam_downloader.log"
)

# Initialize FastAPI
app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_routes)

# Signal handlers
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received. Cleaning up...")
    download_manager.stop()
    sys.exit(0)

# Initialize components
download_manager = DownloadManager()
steam_cmd = SteamCMD()

def run_fastapi(host: str, port: int):
    """Run the FastAPI server."""
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

def main():
    """Main application entry point."""
    try:
        # Log startup information
        logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
        logger.info(f"Base directory: {settings.BASE_DIR}")
        logger.info(f"Persistent directory: {settings.PERSISTENT_DIR}")
        logger.info(f"Download directory: {settings.DOWNLOAD_DIR}")
        
        # Create directories
        settings.create_directories()

        # Install SteamCMD if needed
        if not steam_cmd.path.exists():
            logger.info("Installing SteamCMD...")
            if not steam_cmd.install():
                raise Exception("Failed to install SteamCMD")

        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start download manager
        download_manager.start()

        # Use the PORT environment variable for the API if specified
        api_port = settings.API_PORT
        
        # Start FastAPI server
        if settings.ENABLE_GRADIO:
            # Start FastAPI in a separate thread when using Gradio
            api_thread = threading.Thread(
                target=run_fastapi, 
                args=(settings.HOST, api_port),
                daemon=True
            )
            api_thread.start()
            
            # Create and launch Gradio interface
            logger.info(f"Starting Gradio interface on {settings.HOST}:{settings.PORT}")
            interface = create_interface()
            interface.launch(
                server_name=settings.HOST,
                server_port=settings.PORT,
                prevent_thread_lock=True
            )
            
            # Keep the main thread alive
            api_thread.join()
        else:
            # Just run FastAPI directly if Gradio is disabled
            run_fastapi(settings.HOST, api_port)

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()