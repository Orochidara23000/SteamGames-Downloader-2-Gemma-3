import gradio as gr
from typing import Dict, List, Optional, Any
import requests
import logging
import json
import os
from models import DownloadRequest

logger = logging.getLogger(__name__)

def create_interface() -> gr.Blocks:
    """Create the Gradio interface."""
    from config import settings
    
    # Use base path for API requests
    api_url = ""  # Empty because we're making relative requests
    
    with gr.Blocks(title="Steam Games Downloader") as interface:
        gr.Markdown("# Steam Games Downloader")

        with gr.Tab("Download Games"):
            with gr.Row():
                game_input = gr.Textbox(label="Game ID or Steam Store URL")
                anonymous_login = gr.Checkbox(label="Anonymous Login", value=True)

            with gr.Group(visible=False) as login_group:
                username = gr.Textbox(label="Steam Username")
                password = gr.Textbox(label="Steam Password", type="password")
                steam_guard = gr.Textbox(label="Steam Guard Code (if required)")

            with gr.Row():
                download_btn = gr.Button("Download Now")
                refresh_btn = gr.Button("Refresh Status")

            status = gr.Textbox(label="Download Status", lines=5)
            
        with gr.Tab("Downloads"):
            downloads_table = gr.Dataframe(
                headers=["ID", "Game", "Progress", "Status", "Start Time", "End Time"],
                datatype=["str", "str", "number", "str", "str", "str"],
                label="Downloads"
            )
        
        with gr.Tab("System"):
            system_info = gr.JSON(label="System Information")
            refresh_system_btn = gr.Button("Refresh System Info")
            
        with gr.Tab("API Access"):
            gr.Markdown(f"### API Documentation")
            gr.Markdown(f"Access the API documentation at [/docs](/docs)")
            gr.Markdown(f"### API Endpoints")
            gr.Markdown(f"- POST /downloads - Start a download")
            gr.Markdown(f"- GET /downloads - List all downloads")
            gr.Markdown(f"- GET /downloads/{{id}} - Get a specific download")
            gr.Markdown(f"- DELETE /downloads/{{id}} - Cancel a download")
            gr.Markdown(f"- GET /system - Get system metrics")
            gr.Markdown(f"- GET /health - Health check")

        def toggle_login(anonymous: bool) -> Dict:
            return {"visible": not anonymous}

        def extract_app_id(input_text: str) -> int:
            """Extract app ID from input text."""
            # Try parsing as integer
            try:
                return int(input_text)
            except ValueError:
                pass
                
            # Try extracting from URL
            if "store.steampowered.com/app/" in input_text:
                try:
                    app_id = input_text.split("/app/")[1].split("/")[0]
                    return int(app_id)
                except (IndexError, ValueError):
                    pass
                    
            # Default to 0 (invalid)
            return 0

        def start_download(
            input_text: str,
            anonymous: bool,
            username: Optional[str],
            password: Optional[str],
            steam_guard: Optional[str]
        ) -> str:
            try:
                app_id = extract_app_id(input_text)
                if app_id <= 0:
                    return "Invalid Game ID or URL. Please enter a valid Steam AppID or Steam Store URL."

                request = DownloadRequest(
                    app_id=app_id,
                    anonymous=anonymous,
                    username=username if not anonymous else None,
                    password=password if not anonymous else None,
                    steam_guard_code=steam_guard if not anonymous else None
                )

                # Make API request to start download
                response = requests.post(
                    f"{api_url}/downloads",
                    json=request.dict()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    download_id = data["data"]["download_id"]
                    return f"Download started for AppID {app_id}.\nDownload ID: {download_id}\nCheck the Downloads tab for status."
                else:
                    return f"Failed to start download: {response.text}"

            except Exception as e:
                logger.error(f"UI error in start_download: {e}")
                return f"Error: {str(e)}"

        def get_downloads() -> List[List]:
            """Get all downloads for the table."""
            try:
                response = requests.get(f"{api_url}/downloads")
                if response.status_code != 200:
                    return []
                    
                data = response.json()
                active = data["data"]["active"]
                history = data["data"]["history"]
                
                # Combine and format for table
                all_downloads = []
                for download in active + history:
                    end_time = download.get("end_time", "")
                    all_downloads.append([
                        download["id"],
                        download["name"],
                        download["progress"],
                        download["status"],
                        download["start_time"],
                        end_time
                    ])
                    
                return all_downloads
                
            except Exception as e:
                logger.error(f"UI error in get_downloads: {e}")
                return []

        def get_system_info() -> Dict:
            """Get system information."""
            try:
                response = requests.get(f"{api_url}/system")
                if response.status_code == 200:
                    return response.json()
                return {"error": "Failed to get system info"}
            except Exception as e:
                logger.error(f"UI error in get_system_info: {e}")
                return {"error": str(e)}

        # Connect events
        anonymous_login.change(toggle_login, anonymous_login, login_group)
        download_btn.click(
            start_download,
            [game_input, anonymous_login, username, password, steam_guard],
            status
        )
        refresh_btn.click(get_downloads, outputs=downloads_table)
        refresh_system_btn.click(get_system_info, outputs=system_info)
        
        # Initial data load
        interface.load(get_downloads, outputs=downloads_table)
        interface.load(get_system_info, outputs=system_info)

    return interface
