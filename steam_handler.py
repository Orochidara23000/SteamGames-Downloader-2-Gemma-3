import os
import subprocess
import logging
import requests
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Optional, List
import tarfile
import zipfile
from utils import download_file

logger = logging.getLogger(__name__)

class SteamCMD:
    def __init__(self, config=None):
        from config import settings as default_settings
        self.settings = config or default_settings
        self.path = self.settings.get_steamcmd_path()

    def install(self) -> bool:
        """Install SteamCMD."""
        try:
            if os.name == "nt":
                return self._install_windows()
            return self._install_unix()
        except Exception as e:
            logger.error(f"Failed to install SteamCMD: {e}")
            return False

    def _install_windows(self) -> bool:
        """Install SteamCMD on Windows."""
        try:
            url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
            temp_dir = Path(tempfile.mkdtemp())
            zip_path = temp_dir / "steamcmd.zip"
            
            logger.info(f"Downloading SteamCMD from {url}")
            if not download_file(url, zip_path):
                logger.error("Failed to download SteamCMD")
                return False
                
            logger.info(f"Extracting SteamCMD to {self.settings.STEAMCMD_DIR}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                self.settings.STEAMCMD_DIR.mkdir(parents=True, exist_ok=True)
                zip_ref.extractall(self.settings.STEAMCMD_DIR)
                
            logger.info("SteamCMD installation completed")
            # Clean up temp dir
            shutil.rmtree(temp_dir)
            return True
            
        except Exception as e:
            logger.error(f"SteamCMD Windows installation failed: {e}")
            return False

    def _install_unix(self) -> bool:
        """Install SteamCMD on Unix-like systems."""
        try:
            url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
            temp_dir = Path(tempfile.mkdtemp())
            tar_path = temp_dir / "steamcmd_linux.tar.gz"
            
            logger.info(f"Downloading SteamCMD from {url}")
            if not download_file(url, tar_path):
                logger.error("Failed to download SteamCMD")
                return False
                
            logger.info(f"Extracting SteamCMD to {self.settings.STEAMCMD_DIR}")
            self.settings.STEAMCMD_DIR.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tar_path) as tar:
                tar.extractall(path=self.settings.STEAMCMD_DIR)
                
            # Make steamcmd.sh executable
            steamcmd_path = self.settings.STEAMCMD_DIR / "steamcmd.sh"
            steamcmd_path.chmod(steamcmd_path.stat().st_mode | 0o111)  # Add executable bit
            
            logger.info("SteamCMD installation completed")
            # Clean up temp dir
            shutil.rmtree(temp_dir)
            return True
            
        except Exception as e:
            logger.error(f"SteamCMD Unix installation failed: {e}")
            return False

    def login(self, username: Optional[str] = None, password: Optional[str] = None, 
              steam_guard_code: Optional[str] = None) -> bool:
        """Login to Steam."""
        try:
            cmd: List[str] = [str(self.path)]

            if username and password:
                cmd.extend(["+login", username, password])
                if steam_guard_code:
                    cmd.append(steam_guard_code)
            else:
                cmd.append("+login anonymous")

            cmd.append("+quit")

            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if "Login Failure" in result.stdout:
                logger.error(f"Steam login failed: {result.stdout}")
                return False
                
            return True

        except subprocess.TimeoutExpired:
            logger.error("Steam login timed out")
            return False
        except Exception as e:
            logger.error(f"Steam login failed: {e}")
            return False

    def download_game(self, app_id: int, install_dir: Path) -> bool:
        """Download a Steam game."""
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                str(self.path),
                "+force_install_dir", str(install_dir),
                "+app_update", str(app_id),
                "validate",  # Add validate to ensure complete download
                "+quit"
            ]

            logger.info(f"Starting download for AppID {app_id} to {install_dir}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=self.settings.DOWNLOAD_TIMEOUT
            )
            
            # Check for success in output
            if "Success! App '{}' fully installed.".format(app_id) in result.stdout:
                logger.info(f"Download completed for AppID {app_id}")
                return True
                
            # If we didn't see the success message but there was no explicit error
            if "ERROR" not in result.stdout and "Failed" not in result.stdout:
                logger.info(f"Download likely succeeded for AppID {app_id}")
                return True
                
            logger.error(f"Download failed for AppID {app_id}: {result.stdout}")
            return False

        except subprocess.TimeoutExpired:
            logger.error(f"Download timed out for AppID {app_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to download AppID {app_id}: {e}")
            return False

# Create global instance
steam_cmd = SteamCMD()

