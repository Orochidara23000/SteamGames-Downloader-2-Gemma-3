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

def run_fastapi():
    """Run the FastAPI server."""
    uvicorn.run(
        app,
        host=settings.HOST,
        port=int(settings.PORT) + 1,  # Use a different port for the API
        log_level="info"
    )

def main():
    """Main application entry point."""
    try:
        # Create directories
        settings.create_directories()

        # Install SteamCMD if needed
        if not steam_cmd.path.exists():
            logger.info("Installing SteamCMD...")
            if not steam_cmd.install():
                raise Exception("Failed to install SteamCMD")

        # Start download manager
        download_manager.start()

        # Start FastAPI in a separate thread
        api_thread = threading.Thread(target=run_fastapi, daemon=True)
        api_thread.start()

        # Create and launch Gradio interface
        interface = create_interface()
        interface.launch(
            server_name=settings.HOST,
            server_port=settings.PORT,
            share=True,
            prevent_thread_lock=True
        )

        # Keep the main thread alive
        api_thread.join()

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()