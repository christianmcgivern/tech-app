"""Tool definitions and implementations for the AI-Powered Technician Workflow System."""

from typing import Callable, Dict, Any
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class Tools:
    def __init__(self):
        self.available_tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable):
        """Register a new tool."""
        if name in self.available_tools:
            logger.warning(f"Tool {name} already registered, overwriting")
        self.available_tools[name] = func
        logger.info(f"Registered tool: {name}")

    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a registered tool."""
        if name not in self.available_tools:
            logger.error(f"Tool {name} not found")
            return None
        
        try:
            result = self.available_tools[name](**kwargs)
            return result
        except Exception as e:
            logger.error(f"Failed to execute tool {name}: {e}")
            return None

    def list_tools(self) -> list:
        """List all available tools."""
        return list(self.available_tools.keys()) 