
import logging
import threading
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from config import settings
from steam_handler import steam_cmd

logger = logging.getLogger(__name__)

@dataclass
class DownloadStatus:
    id: str
    appid: str
    name: str
    progress: float
    status: str
    start_time: str

class DownloadManager:
    def __init__(self):
        self.download_queue: List[Dict] = []
        self.running = False
        self.queue_thread = None

    def start(self):
        """Start the download manager."""
        if not self.running:
            self.running = True
            self.queue_thread = threading.Thread(target=self._process_queue)
            self.queue_thread.daemon = True
            self.queue_thread.start()

    def stop(self):
        """Stop the download manager."""
        self.running = False
        if self.queue_thread:
            self.queue_thread.join()

    def add_to_queue(self, appid: int, request: DownloadRequest):
        """Add a game to the download queue."""
        self.download_queue.append({"appid": appid, "request": request})
        logger.info(f"Added game {appid} to download queue")

    def _process_queue(self):
        """Process the download queue."""
        while self.running:
            if self.download_queue:
                item = self.download_queue.pop(0)
                appid = item["appid"]
                request = item["request"]

                try:
                    # Login to Steam
                    if not request.anonymous:
                        if not steam_cmd.login(request.username, request.password, request.steam_guard_code):
                            logger.error(f"Login failed for AppID {appid}")
                            continue

                    # Start download
                    if steam_cmd.download_game(appid, settings.DOWNLOAD_DIR):
                        logger.info(f"Download started for AppID {appid}")
                    else:
                        logger.error(f"Failed to start download for AppID {appid}")

                except Exception as e:
                    logger.error(f"Error downloading game {appid}: {e}")

            time.sleep(1)

