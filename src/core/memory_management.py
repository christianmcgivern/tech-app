"""Memory management module for handling resource cleanup and monitoring."""

import psutil
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ResourceUsage:
    """Resource usage tracking."""
    resource_type: str
    allocation_time: datetime
    last_used: datetime
    size_bytes: int
    metadata: Dict[str, Any]

class MemoryManager:
    """Memory manager for handling resource cleanup and monitoring.
    
    This class provides:
    - Memory usage monitoring
    - Resource tracking and cleanup
    - Connection pooling
    - Automatic cleanup when memory threshold is exceeded
    """
    
    def __init__(self, cleanup_threshold: float = 0.8, monitoring_interval: int = 60):
        """Initialize memory manager.
        
        Args:
            cleanup_threshold: Memory usage percentage that triggers cleanup (0.0-1.0)
            monitoring_interval: Interval in seconds between memory checks
        """
        self.cleanup_threshold = cleanup_threshold
        self.monitoring_interval = monitoring_interval
        self.resources: Dict[str, ResourceUsage] = {}
        self.total_memory_used = 0
        self._monitoring = False
        
    async def start_monitoring(self):
        """Start memory usage monitoring."""
        self._monitoring = True
        while self._monitoring:
            try:
                memory_percent = psutil.Process().memory_percent() / 100.0
                if memory_percent > self.cleanup_threshold:
                    logger.warning(f"Memory usage ({memory_percent:.1%}) exceeded threshold ({self.cleanup_threshold:.1%})")
                    await self.cleanup_resources()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in memory monitoring: {str(e)}")
                
    async def stop_monitoring(self):
        """Stop memory usage monitoring."""
        self._monitoring = False
        
    async def cleanup_resources(self):
        """Clean up unused resources."""
        logger.info("Starting resource cleanup")
        current_time = datetime.now()
        cleaned_count = 0
        cleaned_bytes = 0
        
        for resource_id, usage in list(self.resources.items()):
            if (current_time - usage.last_used).total_seconds() > 300:  # 5 minutes idle
                cleaned_bytes += usage.size_bytes
                cleaned_count += 1
                await self.release_resource(resource_id)
                
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} resources ({cleaned_bytes / 1024 / 1024:.1f} MB)")
        
    async def track_resource(self, 
                           resource_id: str, 
                           resource_type: str, 
                           size_bytes: int,
                           metadata: Optional[Dict[str, Any]] = None):
        """Track a new resource.
        
        Args:
            resource_id: Unique identifier for the resource
            resource_type: Type of resource (e.g., "websocket", "audio")
            size_bytes: Size of the resource in bytes
            metadata: Additional metadata about the resource
        """
        now = datetime.now()
        self.resources[resource_id] = ResourceUsage(
            resource_type=resource_type,
            allocation_time=now,
            last_used=now,
            size_bytes=size_bytes,
            metadata=metadata or {}
        )
        self.total_memory_used += size_bytes
        logger.debug(f"Tracking resource {resource_id} ({size_bytes / 1024:.1f} KB)")
        
    async def release_resource(self, resource_id: str):
        """Release a tracked resource.
        
        Args:
            resource_id: Unique identifier for the resource to release
        """
        if resource_id in self.resources:
            resource = self.resources[resource_id]
            self.total_memory_used -= resource.size_bytes
            del self.resources[resource_id]
            logger.debug(f"Released resource {resource_id} ({resource.size_bytes / 1024:.1f} KB)")
            
    async def update_resource_usage(self, resource_id: str):
        """Update last used timestamp for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
        """
        if resource_id in self.resources:
            self.resources[resource_id].last_used = datetime.now()
            
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics.
        
        Returns:
            Dictionary containing memory usage statistics
        """
        return {
            "total_resources": len(self.resources),
            "total_memory_used_mb": self.total_memory_used / 1024 / 1024,
            "process_memory_percent": psutil.Process().memory_percent(),
            "system_memory_percent": psutil.virtual_memory().percent
        } 