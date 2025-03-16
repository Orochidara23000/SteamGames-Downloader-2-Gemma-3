import psutil
import humanize
import uuid
import time
import requests
from typing import Dict, Any, Optional
from pathlib import Path

def get_system_metrics() -> Dict[str, Any]:
    """Get system resource usage metrics."""
    try:
        # Get disk info for download directory
        from config import settings
        
        # Use root directory if download directory doesn't exist
        disk_path = '/' if not settings.DOWNLOAD_DIR.exists() else settings.DOWNLOAD_DIR
        
        disk_usage = psutil.disk_usage(disk_path)
        available_space = humanize.naturalsize(disk_usage.free)
        
        return {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": disk_usage.percent,
            "available_disk_space": available_space
        }
    except Exception as e:
        # Fall back to default values if there's an error
        return {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "available_disk_space": "Unknown"
        }

def generate_download_id() -> str:
    """Generate a unique ID for downloads."""
    return str(uuid.uuid4())

def download_file(url: str, path: Path, chunk_size: int = 8192) -> bool:
    """
    Download a file from a URL to a path with progress tracking.
    
    Args:
        url: The URL to download from
        path: The path to save the file to
        chunk_size: The chunk size for downloading
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
            
            return True
    except Exception:
        # If the download fails, delete the partial file
        if path.exists():
            path.unlink()
        return False

def get_steam_app_info(app_id: int) -> Optional[Dict[str, Any]]:
    """
    Get information about a Steam app from the Steam Store API.
    
    Args:
        app_id: The Steam App ID
    
    Returns:
        Optional[Dict[str, Any]]: App information or None if not found
    """
    try:
        from config import settings
        
        url = f"{settings.STEAM_API_URL}/appdetails?appids={app_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get(str(app_id), {}).get('success', False):
            return data[str(app_id)]['data']
        return None
    except Exception:
        return None