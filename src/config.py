#!/usr/bin/env python3
"""Configuration management for Grace CLI."""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from .types.config import AIConfig, ResearchConfig, TechSpecConfig, LogConfig


class Config:
    """Configuration class to manage environment variables."""
    aiConfig: AIConfig
    techSpecConfig: TechSpecConfig
    logConfig: LogConfig
    researchConfig: ResearchConfig

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration and load environment variables.

        Args:
            env_file: Path to .env file. If None, looks for .env in project root.
        """
        if env_file is None:
            project_root = Path(__file__).parent.parent
            env_file = str(project_root / ".env")

        if Path(env_file).exists():
            load_dotenv(env_file)

        self._load_config()

    def _load_config(self) -> None:
        """Load all configuration from environment variables."""
        # AI Configuration
        self.aiConfig = AIConfig(
            api_key=os.getenv("AI_API_KEY", ""),
            provider=os.getenv("AI_PROVIDER", "litellm"),
            base_url=os.getenv("AI_BASE_URL", "https://grid.juspay.net"),
            model_id=os.getenv("AI_MODEL_ID", "qwen3-coder-480b"),
            project_id=os.getenv("AI_PROJECT_ID"),
            location=os.getenv("AI_LOCATION", "us-east5"),
        )
        self.techSpecConfig = TechSpecConfig(
            output_dir=os.getenv("TECHSPEC_OUTPUT_DIR", "./output"),
            template_dir=os.getenv("TECHSPEC_TEMPLATE_DIR", "./templates"),
            temperature=float(os.getenv("TECHSPEC_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("TECHSPEC_MAX_TOKENS", "50000")),
            firecracker_api_key=os.getenv("FIRECRACKER_API_KEY"),
            use_playwright=os.getenv("USE_PLAYWRIGHT", "false").lower() == "true",
        )
        self.logConfig = LogConfig(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "grace.log"),
        )

        self.researchConfig = ResearchConfig(
            searchTool=os.getenv("SEARCH_TOOL", "searxng"),
            baseURL=os.getenv("SEARCH_BASE_URL", "https://localhost:32678"),
            formatType=os.getenv("SEARCH_FORMAT_TYPE", "markdown"),
            depth=int(os.getenv("SEARCH_DEPTH", "5")),
        )

    def getAiConfig(self) -> AIConfig:
        return self.aiConfig
    
    def getTechSpecConfig(self) -> TechSpecConfig:
        return self.techSpecConfig
    
    def getLogConfig(self) -> LogConfig:
        return self.logConfig

    def getResearchConfig(self) -> ResearchConfig:
        return self.researchConfig


_config_instance: Optional[Config] = None


def get_config(env_file: Optional[str] = None) -> Config:
    """Get or create singleton Config instance.

    Args:
        env_file: Path to .env file

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(env_file)
    return _config_instance


def reload_config(env_file: Optional[str] = None):
    """Reload configuration from environment file.

    Args:
        env_file: Path to .env file
    """
    global _config_instance
    _config_instance = Config(env_file)
    return _config_instance
