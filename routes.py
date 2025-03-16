from fastapi import APIRouter, HTTPException, Path as PathParam, Query, Depends
from typing import Dict, List, Optional
from models import DownloadRequest, DownloadInfo, SystemMetrics, APIResponse
from downloader import download_manager
from utils import get_system_metrics
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/downloads", response_model=APIResponse)
async def start_download(request: DownloadRequest) -> APIResponse:
    """Start a new download."""
    try:
        download_id = download_manager.add_to_queue(request.app_id, request)
        return APIResponse(
            success=True,
            message=f"Download for AppID {request.app_id} added to queue.",
            data={"download_id": download_id}
        )
    except Exception as e:
        logger.error(f"Error starting download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/downloads", response_model=APIResponse)
async def get_downloads() -> APIResponse:
    """Get all downloads."""
    try:
        downloads = download_manager.get_all_downloads()
        return APIResponse(
            success=True,
            message="Download information retrieved.",
            data=downloads
        )
    except Exception as e:
        logger.error(f"Error retrieving downloads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/downloads/{download_id}", response_model=APIResponse)
async def get_download(download_id: str = PathParam(...)) -> APIResponse:
    """Get download status by ID."""
    try:
        download = download_manager.get_download_status(download_id)
        if not download:
            raise HTTPException(status_code=404, detail=f"Download with ID {download_id} not found")
        
        return APIResponse(
            success=True,
            message="Download information retrieved.",
            data=download
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving download {download_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/downloads/{download_id}", response_model=APIResponse)
async def cancel_download(download_id: str = PathParam(...)) -> APIResponse:
    """Cancel a download."""
    try:
        if download_manager.cancel_download(download_id):
            return APIResponse(
                success=True,
                message=f"Download {download_id} canceled successfully."
            )
        raise HTTPException(status_code=404, detail=f"Download with ID {download_id} not found or already completed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling download {download_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system", response_model=SystemMetrics)
async def get_system_status() -> SystemMetrics:
    """Get system status information."""
    try:
        metrics = get_system_metrics()
        return SystemMetrics(**metrics)
    except Exception as e:
        logger.error(f"Error retrieving system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

