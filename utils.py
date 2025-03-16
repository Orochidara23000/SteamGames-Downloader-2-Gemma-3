import psutil
import humanize
from typing import Dict

def get_system_metrics() -> Dict:
    """Get system resource usage metrics."""
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }