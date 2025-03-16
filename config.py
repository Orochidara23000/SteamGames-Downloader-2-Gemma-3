import os
import tempfile
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Steam Games Downloader"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Railway-friendly paths
    # Use /tmp for non-persistent storage in Railway
    BASE_DIR: Path = Path(os.getenv("BASE_DIR", tempfile.gettempdir()))
    # For persistent storage, use RAILWAY_VOLUME_MOUNT if available
    PERSISTENT_DIR: Path = Path(os.getenv("RAILWAY_VOLUME_MOUNT", os.getenv("PERSISTENT_DIR", "/data")))
    
    # Derived paths
    STEAMCMD_DIR: Path = Path(os.getenv("STEAMCMD_DIR", BASE_DIR / "steamcmd"))
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", PERSISTENT_DIR / "logs"))
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", PERSISTENT_DIR / "downloads"))

    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Download Settings
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "1"))
    MAX_HISTORY_SIZE: int = int(os.getenv("MAX_HISTORY_SIZE", "50"))
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "3600"))  # 1 hour

    # Steam API
    STEAM_API_URL: str = os.getenv("STEAM_API_URL", "https://store.steampowered.com/api")
    STEAM_GUARD_REQUIRED: bool = os.getenv("STEAM_GUARD_REQUIRED", "False").lower() == "true"
    STEAM_USERNAME: Optional[str] = os.getenv("STEAM_USERNAME")

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.STEAMCMD_DIR, self.LOG_DIR, self.DOWNLOAD_DIR]:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                print(f"Warning: No permission to create directory {directory}. Using temporary directory instead.")
                # Fall back to temp directory if permissions are an issue
                if directory == self.STEAMCMD_DIR:
                    self.STEAMCMD_DIR = Path(tempfile.gettempdir()) / "steamcmd"
                    self.STEAMCMD_DIR.mkdir(parents=True, exist_ok=True)

    def get_steamcmd_path(self) -> Path:
        """Get the path to SteamCMD executable based on platform."""
        if os.name == 'nt':  # Windows
            return self.STEAMCMD_DIR / "steamcmd.exe"
        return self.STEAMCMD_DIR / "steamcmd.sh"

# Create global settings instance
settings = Settings()

