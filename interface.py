
import gradio as gr
from typing import Dict, Optional
from models import DownloadRequest
from downloader import download_manager
from steam_handler import steam_cmd

def create_interface() -> gr.Blocks:
    """Create the Gradio interface."""
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

            status = gr.Textbox(label="Download Status")

        def toggle_login(anonymous: bool) -> Dict:
            return {"visible": not anonymous}

        def start_download(
            input_text: str,
            anonymous: bool,
            username: Optional[str],
            password: Optional[str],
            steam_guard: Optional[str]
        ):
            try:
                game_id = int(input_text)  # Assuming input is an integer AppID
            except ValueError:
                return "Invalid Game ID. Please enter a number."

            request = DownloadRequest(
                app_id=game_id,
                anonymous=anonymous,
                username=username if not anonymous else None,
                password=password if not anonymous else None,
                steam_guard_code=steam_guard if not anonymous else None
            )

            download_manager.add_to_queue(game_id, request)

            return "Download started. Check the Downloads tab for status."

        anonymous_login.change(toggle_login, anonymous_login, login_group)
        download_btn.click(
            start_download,
            [game_input, anonymous_login, username, password, steam_guard],
            status
        )

    return interface
