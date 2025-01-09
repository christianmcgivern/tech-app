"""Monitoring and metrics collection for the AI-Powered Technician Workflow System."""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from .logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class APIMetric:
    """Represents a single API metric measurement."""
    endpoint: str
    duration: float
    status: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class RateLimit:
    """Represents rate limit information."""
    name: str
    remaining: int
    reset_seconds: int
    timestamp: datetime = field(default_factory=datetime.now)

class MetricsCollector:
    """Collects and manages system metrics."""
    
    def __init__(self):
        self.api_metrics: List[APIMetric] = []
        self.rate_limits: Dict[str, RateLimit] = {}
        self.error_counts: Dict[str, int] = {}
        self._cleanup_interval = timedelta(hours=1)
        self._last_cleanup = datetime.now()

    def track_api_call(self, endpoint: str, duration: float, status: str = "success"):
        """
        Track an API call's performance metrics.
        
        Args:
            endpoint (str): The API endpoint called
            duration (float): Call duration in seconds
            status (str): Call status (success/error)
        """
        metric = APIMetric(endpoint=endpoint, duration=duration, status=status)
        self.api_metrics.append(metric)
        logger.debug(f"API Metric recorded: {endpoint} - {duration:.3f}s - {status}")
        self._cleanup_old_metrics()

    def update_rate_limits(self, limits: List[Dict[str, Any]]):
        """
        Update rate limit information.
        
        Args:
            limits (List[Dict[str, Any]]): List of rate limit updates
        """
        for limit in limits:
            name = limit.get("name", "unknown")
            self.rate_limits[name] = RateLimit(
                name=name,
                remaining=limit.get("remaining", 0),
                reset_seconds=limit.get("reset_seconds", 0)
            )
        logger.debug(f"Rate limits updated: {len(limits)} limits")

    def track_error(self, error_type: str):
        """
        Track error occurrences by type.
        
        Args:
            error_type (str): Type of error encountered
        """
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        logger.warning(f"Error tracked: {error_type} (count: {self.error_counts[error_type]})")

    def get_api_metrics_summary(self, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get summary of API metrics for the specified time window.
        
        Args:
            window_minutes (int): Time window in minutes
            
        Returns:
            Dict[str, Any]: Metrics summary
        """
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_metrics = [m for m in self.api_metrics if m.timestamp > cutoff]
        
        if not recent_metrics:
            return {
                "total_calls": 0,
                "avg_duration": 0.0,
                "error_rate": 0.0,
                "window_minutes": window_minutes
            }
        
        total_calls = len(recent_metrics)
        avg_duration = sum(m.duration for m in recent_metrics) / total_calls
        error_count = sum(1 for m in recent_metrics if m.status == "error")
        error_rate = (error_count / total_calls) * 100
        
        return {
            "total_calls": total_calls,
            "avg_duration": round(avg_duration, 3),
            "error_rate": round(error_rate, 2),
            "window_minutes": window_minutes
        }

    def get_rate_limit_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current rate limit status.
        
        Returns:
            Dict[str, Dict[str, Any]]: Rate limit status by limit name
        """
        return {
            name: {
                "remaining": limit.remaining,
                "reset_seconds": limit.reset_seconds,
                "last_updated": limit.timestamp.isoformat()
            }
            for name, limit in self.rate_limits.items()
        }

    def _cleanup_old_metrics(self):
        """Clean up metrics older than cleanup interval."""
        current_time = datetime.now()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
            
        cutoff = current_time - self._cleanup_interval
        self.api_metrics = [m for m in self.api_metrics if m.timestamp > cutoff]
        self._last_cleanup = current_time
        logger.debug(f"Cleaned up metrics older than {cutoff.isoformat()}") 