#!/usr/bin/env python3
import os
import sys
import signal
import uvicorn
import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict

# Import project modules
from config import settings
from routes import router as api_routes
from log_config import setup_logging
from downloader import download_manager
from steam_handler import steam_cmd
from interface import create_interface

# Set up logging
logger = setup_logging(
    name="steam_downloader",
    log_file=settings.LOG_DIR / "steam_downloader.log",
    log_level=settings.LOG_LEVEL
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

# Root endpoint for health checks
@app.get("/")
async def root() -> Dict[str, str]:
    return {"status": "healthy"}

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}

# Create Gradio interface and mount at /ui
if settings.ENABLE_GRADIO:
    logger.info("Setting up Gradio interface")
    gradio_app = create_interface()
    # Mount Gradio app at /ui path
    app = gr.mount_gradio_app(app, gradio_app, path="/ui")
    logger.info(f"Gradio UI will be available at: http://{settings.HOST}:{settings.PORT}/ui/")

# Signal handlers
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received. Cleaning up...")
    download_manager.stop()
    sys.exit(0)

def main():
    """Main application entry point."""
    try:
        # Log startup information
        logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
        logger.info(f"Base directory: {settings.BASE_DIR}")
        logger.info(f"Persistent directory: {settings.PERSISTENT_DIR}")
        logger.info(f"Download directory: {settings.DOWNLOAD_DIR}")
        logger.info(f"Port: {settings.PORT}")
        
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

        # Get Railway URL if available
        railway_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        if railway_url:
            logger.info(f"Railway Public URL: https://{railway_url}")
            if settings.ENABLE_GRADIO:
                logger.info(f"Gradio UI available at: https://{railway_url}/ui/")
        
        # Run the API server
        logger.info(f"Starting API server on {settings.HOST}:{settings.PORT}")
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            log_level="info"
        )

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()