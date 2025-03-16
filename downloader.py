import logging
import threading
import time
import queue
import concurrent.futures
from typing import Dict, List, Optional, Any
from datetime import datetime
from models import DownloadRequest, DownloadInfo, DownloadStatus
from utils import generate_download_id, get_steam_app_info

logger = logging.getLogger(__name__)

class DownloadManager:
    def __init__(self, config=None):
        from config import settings as default_settings
        from steam_handler import steam_cmd as default_steam_cmd
        
        self.settings = config or default_settings
        self.steam_cmd = default_steam_cmd
        
        self.download_queue = queue.Queue()
        self.active_downloads: Dict[str, DownloadInfo] = {}
        self.download_history: List[DownloadInfo] = []
        self.running = False
        self.queue_thread = None
        self.lock = threading.RLock()
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.settings.MAX_CONCURRENT_DOWNLOADS
        )
        self.futures = {}

    def start(self):
        """Start the download manager."""
        with self.lock:
            if not self.running:
                self.running = True
                self.queue_thread = threading.Thread(target=self._process_queue)
                self.queue_thread.daemon = True
                self.queue_thread.start()
                logger.info("Download manager started")

    def stop(self):
        """Stop the download manager."""
        with self.lock:
            if self.running:
                self.running = False
                logger.info("Stopping download manager...")
                
                # Cancel all active downloads
                for download_id, future in list(self.futures.items()):
                    if not future.done():
                        future.cancel()
                
                # Wait for queue thread to finish
                if self.queue_thread and self.queue_thread.is_alive():
                    self.queue_thread.join(timeout=5)
                
                # Shutdown executor
                self.executor.shutdown(wait=False)
                logger.info("Download manager stopped")

    def add_to_queue(self, app_id: int, request: DownloadRequest) -> str:
        """Add a game to the download queue and return download ID."""
        download_id = generate_download_id()
        
        # Get game info from Steam API
        game_info = get_steam_app_info(app_id)
        game_name = game_info.get("name", "Unknown Game") if game_info else "Unknown Game"
        
        download_info = DownloadInfo(
            id=download_id,
            app_id=app_id,
            name=game_name,
            status=DownloadStatus.QUEUED,
            start_time=datetime.now()
        )
        
        with self.lock:
            self.download_queue.put((download_id, request, download_info))
            logger.info(f"Added game {app_id} ({game_name}) to download queue")
            
        return download_id

    def get_download_status(self, download_id: str) -> Optional[DownloadInfo]:
        """Get the status of a download."""
        with self.lock:
            # Check active downloads
            if download_id in self.active_downloads:
                return self.active_downloads[download_id]
                
            # Check download history
            for download in self.download_history:
                if download.id == download_id:
                    return download
                    
        return None

    def get_all_downloads(self) -> Dict[str, List[DownloadInfo]]:
        """Get all downloads (active and history)."""
        with self.lock:
            return {
                "active": list(self.active_downloads.values()),
                "history": self.download_history
            }

    def cancel_download(self, download_id: str) -> bool:
        """Cancel a download."""
        with self.lock:
            # Check if download is active
            if download_id in self.active_downloads:
                if download_id in self.futures:
                    self.futures[download_id].cancel()
                
                download = self.active_downloads[download_id]
                download.status = DownloadStatus.CANCELED
                download.end_time = datetime.now()
                
                # Move to history
                self.download_history.insert(0, download)
                if len(self.download_history) > self.settings.MAX_HISTORY_SIZE:
                    self.download_history.pop()
                    
                # Remove from active
                del self.active_downloads[download_id]
                if download_id in self.futures:
                    del self.futures[download_id]
                
                logger.info(f"Download {download_id} ({download.name}) canceled")
                return True
                
        return False

    def _process_queue(self):
        """Process the download queue."""
        while self.running:
            try:
                # Get next download from queue if we have capacity
                if not self.download_queue.empty() and len(self.active_downloads) < self.settings.MAX_CONCURRENT_DOWNLOADS:
                    download_id, request, download_info = self.download_queue.get(block=False)
                    
                    with self.lock:
                        # Update status to downloading
                        download_info.status = DownloadStatus.DOWNLOADING
                        self.active_downloads[download_id] = download_info
                    
                    # Start download in thread pool
                    future = self.executor.submit(self._download_game, download_id, request)
                    
                    with self.lock:
                        self.futures[download_id] = future
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Error in download queue processing: {e}")
                
            time.sleep(1)

    def _download_game(self, download_id: str, request: DownloadRequest) -> None:
        """Download a game."""
        app_id = request.app_id
        success = False
        error_message = None
        
        try:
            # Determine install directory
            install_dir = self.settings.DOWNLOAD_DIR / str(app_id)
            if request.install_dir:
                install_dir = Path(request.install_dir)
                
            # Login to Steam if needed
            if not request.anonymous:
                if not self.steam_cmd.login(request.username, request.password, request.steam_guard_code):
                    raise Exception("Steam login failed")
                    
            # Start download
            success = self.steam_cmd.download_game(app_id, install_dir)
            if not success:
                raise Exception("Steam download failed")
                
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Error downloading game {app_id}: {e}")
            
        # Update download info
        with self.lock:
            if download_id in self.active_downloads:
                download = self.active_downloads[download_id]
                download.end_time = datetime.now()
                download.status = DownloadStatus.COMPLETED if success else DownloadStatus.FAILED
                download.progress = 100.0 if success else download.progress
                download.error_message = error_message
                
                # Move to history
                self.download_history.insert(0, download)
                if len(self.download_history) > self.settings.MAX_HISTORY_SIZE:
                    self.download_history.pop()
                    
                # Remove from active
                del self.active_downloads[download_id]
                if download_id in self.futures:
                    del self.futures[download_id]

# Create global instance
download_manager = DownloadManager()

