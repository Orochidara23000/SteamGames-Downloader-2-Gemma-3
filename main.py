#!/usr/bin/env python3
import os
import sys
import signal
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import gradio as gr

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

# Add root redirect
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

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

        # Set up Gradio interface
        logger.info(f"Setting up Gradio interface")
        gradio_interface = create_interface()
        
        # Mount FastAPI inside Gradio app
        app_port = settings.PORT
        app_url = f"http://localhost:{app_port}"
        logger.info(f"API URL: {app_url}")
        
        # Launch Gradio with FastAPI
        logger.info(f"Starting Gradio interface on port {settings.PORT}")
        gradio_interface.launch(
            server_name=settings.HOST,
            server_port=settings.PORT,
            prevent_thread_lock=False,  # This is important - let Gradio take over the main thread
            show_api=False,
            share=True,  # This will print a public URL if available
            favicon_path=None
        )

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()