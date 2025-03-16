from fastapi import APIRouter, HTTPException, Path as PathParam, Query, Depends, Request
from fastapi.responses import HTMLResponse
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

@router.get("/downloads/ui", response_class=HTMLResponse)
async def downloads_ui(request: Request):
    """A simple HTML UI for downloads."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Steam Downloads</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .downloads { margin: 20px 0; }
            .download { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .status-completed { color: green; }
            .status-failed { color: red; }
            .status-downloading { color: blue; }
            .status-queued { color: orange; }
            button { padding: 8px 15px; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; }
            input, select { padding: 8px; margin: 5px 0; }
            #refresh { background: #5cb85c; }
        </style>
        <script>
            function loadDownloads() {
                fetch('/downloads')
                    .then(response => response.json())
                    .then(data => {
                        const container = document.getElementById('downloadsContainer');
                        container.innerHTML = '';
                        
                        const active = data.data.active || [];
                        const history = data.data.history || [];
                        
                        if (active.length === 0 && history.length === 0) {
                            container.innerHTML = '<p>No downloads yet</p>';
                            return;
                        }
                        
                        // Active downloads
                        if (active.length > 0) {
                            const activeSection = document.createElement('div');
                            activeSection.innerHTML = '<h2>Active Downloads</h2>';
                            container.appendChild(activeSection);
                            
                            active.forEach(download => {
                                const div = document.createElement('div');
                                div.className = 'download';
                                div.innerHTML = `
                                    <h3>${download.name} (${download.app_id})</h3>
                                    <p>ID: ${download.id}</p>
                                    <p>Progress: ${download.progress}%</p>
                                    <p>Status: <span class="status-${download.status}">${download.status}</span></p>
                                    <p>Started: ${download.start_time}</p>
                                    <button onclick="cancelDownload('${download.id}')">Cancel</button>
                                `;
                                container.appendChild(div);
                            });
                        }
                        
                        // History
                        if (history.length > 0) {
                            const historySection = document.createElement('div');
                            historySection.innerHTML = '<h2>Download History</h2>';
                            container.appendChild(historySection);
                            
                            history.forEach(download => {
                                const div = document.createElement('div');
                                div.className = 'download';
                                div.innerHTML = `
                                    <h3>${download.name} (${download.app_id})</h3>
                                    <p>ID: ${download.id}</p>
                                    <p>Progress: ${download.progress}%</p>
                                    <p>Status: <span class="status-${download.status}">${download.status}</span></p>
                                    <p>Started: ${download.start_time}</p>
                                    <p>Ended: ${download.end_time || 'N/A'}</p>
                                    <p>Error: ${download.error_message || 'None'}</p>
                                `;
                                container.appendChild(div);
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching downloads:', error);
                        document.getElementById('downloadsContainer').innerHTML = 
                            '<p>Error loading downloads. Check console for details.</p>';
                    });
            }
            
            function startDownload() {
                const appId = document.getElementById('appIdInput').value;
                
                if (!appId || isNaN(parseInt(appId))) {
                    alert('Please enter a valid App ID');
                    return;
                }
                
                const data = {
                    app_id: parseInt(appId),
                    anonymous: true
                };
                
                fetch('/downloads', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Download started: ' + data.message);
                        loadDownloads();
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error starting download:', error);
                    alert('Error starting download. Check console for details.');
                });
            }
            
            function cancelDownload(id) {
                fetch('/downloads/' + id, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Download canceled');
                        loadDownloads();
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error canceling download:', error);
                    alert('Error canceling download. Check console for details.');
                });
            }
            
            // Refresh downloads every 10 seconds
            window.onload = function() {
                loadDownloads();
                setInterval(loadDownloads, 10000);
            }
        </script>
    </head>
    <body>
        <h1>Steam Games Downloader</h1>
        
        <div class="download-form">
            <h2>Start a New Download</h2>
            <div>
                <input type="text" id="appIdInput" placeholder="Steam App ID" />
                <button onclick="startDownload()">Download</button>
            </div>
        </div>
        
        <div class="downloads">
            <div class="header">
                <h2>Downloads</h2>
                <button id="refresh" onclick="loadDownloads()">Refresh</button>
            </div>
            <div id="downloadsContainer" class="downloads-container">
                Loading...
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

