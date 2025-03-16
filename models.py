from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class DownloadStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class DownloadRequest(BaseModel):
    app_id: int
    anonymous: bool = True
    username: Optional[str] = None
    password: Optional[str] = None
    steam_guard_code: Optional[str] = None
    install_dir: Optional[str] = None

class DownloadInfo(BaseModel):
    id: str
    app_id: int
    name: str = "Unknown Game"
    progress: float = 0.0
    status: DownloadStatus = DownloadStatus.QUEUED
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    available_disk_space: str
    download_speed: Optional[float] = None

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None 