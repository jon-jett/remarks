import os
import json
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Default paths
DEFAULT_DOWNLOAD_PATH = os.path.join(str(Path.home()), "Movies", "remarks", "library")
DEFAULT_CONFIG_PATH = os.path.join(str(Path.home()), ".remarks", "config.json")

class OpenAISettings(BaseModel):
    """OpenAI API settings for transcription"""
    api_key: Optional[str] = None
    model: str = "whisper-1"

class DownloaderSettings(BaseModel):
    """Settings for video downloading"""
    download_path: str = DEFAULT_DOWNLOAD_PATH
    default_format: str = "best"
    cookie_file: Optional[str] = None

class TranscriberSettings(BaseModel):
    """Settings for transcription"""
    output_path: str = DEFAULT_DOWNLOAD_PATH
    language: str = "en"
    whisper_model: str = "base"
    openai: OpenAISettings = OpenAISettings()

class AppConfig(BaseModel):
    """Main application configuration"""
    downloader: DownloaderSettings = DownloaderSettings()
    transcriber: TranscriberSettings = TranscriberSettings()
    theme: str = "dark"
    version: str = "1.0.0"

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load configuration from file or create default if not exists"""
    try:
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # If config file exists, load it
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                return AppConfig.model_validate(config_data)
        
        # Otherwise create default config
        config = AppConfig()
        save_config(config, config_path)
        return config
    
    except Exception as e:
        print(f"Error loading config: {e}")
        config = AppConfig()
        return config

def save_config(config: AppConfig, config_path: str = DEFAULT_CONFIG_PATH) -> bool:
    """Save configuration to file"""
    try:
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Save config as JSON
        with open(config_path, 'w') as f:
            json.dump(config.model_dump(), f, indent=2)
        return True
    
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# Global config instance
config = load_config()

# Functions to get and update specific settings
def get_download_path() -> str:
    """Get the current download path"""
    return config.downloader.download_path

def update_download_path(path: str) -> bool:
    """Update the download path and save config"""
    config.downloader.download_path = path
    return save_config(config)

def get_cookie_file() -> Optional[str]:
    """Get the current cookie file path"""
    return config.downloader.cookie_file

def update_cookie_file(path: Optional[str]) -> bool:
    """Update the cookie file path and save config"""
    config.downloader.cookie_file = path
    return save_config(config)

def get_openai_api_key() -> Optional[str]:
    """Get the OpenAI API key"""
    return config.transcriber.openai.api_key

def update_openai_api_key(api_key: str) -> bool:
    """Update the OpenAI API key and save config"""
    config.transcriber.openai.api_key = api_key
    return save_config(config) 