
from fastapi import APIRouter, HTTPException
from typing import Dict
from models import DownloadRequest
from downloader import download_manager
from utils import get_system_metrics

router = APIRouter()

@router.post("/downloads", response_model=Dict[str, str])
async def start_download(request: DownloadRequest) -> Dict[str, str]:
    """Start a new download."""
    try:
        download_manager.add_to_queue(request.app_id, request)
        return {"message": f"Download for AppID {request.app_id} added to queue."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system", response_model=Dict[str, float])
async def get_system_status() -> Dict[str, float]:
    """Get system status information."""
    metrics = get_system_metrics()
    return {
        "cpu_usage": metrics["cpu_usage"],
        "memory_usage": metrics["memory_usage"],
        "disk_usage": metrics["disk_usage"]
    }

