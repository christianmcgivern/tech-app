"""Configuration management for the AI-Powered Technician Workflow System."""

import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from .logging import setup_logger

logger = setup_logger(__name__)

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

def validate_config_schema(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration schema.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary to validate
        
    Returns:
        bool: True if valid, raises ConfigValidationError if invalid
    """
    required_fields = {
        "websocket": ["url", "model", "ping_interval", "ping_timeout"],
        "audio": ["sample_rate", "channels", "chunk_size"],
        "logging": ["format", "date_format"],
        "technician": ["max_active_orders", "location_update_interval"]
    }
    
    for section, fields in required_fields.items():
        if section not in config:
            raise ConfigValidationError(f"Missing required section: {section}")
        for field in fields:
            if field not in config[section]:
                raise ConfigValidationError(f"Missing required field '{field}' in section '{section}'")
    return True

class APIKeyManager:
    """Manages secure API key handling."""
    
    @staticmethod
    def get_api_key(validate: bool = True) -> Optional[str]:
        """
        Retrieve the API key securely from environment variables.
        
        Args:
            validate (bool): Whether to validate the API key format
            
        Returns:
            Optional[str]: The API key if found and valid, None if validation is disabled
            
        Raises:
            ValueError: If API key is not found or invalid when validation is enabled
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not validate:
            return api_key

        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key not found")
        
        if not api_key.startswith(("sk-", "org-")):
            logger.error("Invalid API key format")
            raise ValueError("Invalid API key format")
            
        return api_key

def load_config(validate_api_key: bool = True) -> Dict[str, Any]:
    """
    Load configuration from config.json and environment variables.
    
    Args:
        validate_api_key (bool): Whether to validate the OpenAI API key
        
    Returns:
        Dict[str, Any]: The configuration dictionary
        
    Raises:
        ConfigValidationError: If configuration validation fails
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file is invalid JSON
    """
    load_dotenv()
    
    try:
        if validate_api_key:
            APIKeyManager.get_api_key(validate=True)
        
        # Use absolute path relative to this file
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.json")
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
            
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Validate configuration schema
        validate_config_schema(config)
        
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise 