"""Tests for configuration management."""

import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from api_doc_processor.config import Config, load_config, create_sample_config


def test_load_valid_config():
    """Test loading a valid configuration."""
    config_data = {
        "firecrawl": {"api_key": "test-firecrawl-key"},
        "litellm": {
            "api_key": "test-llm-key",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 4000
        }
    }
    
    with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = Path(f.name)
    
    try:
        config = load_config(config_path)
        assert config.firecrawl.api_key == "test-firecrawl-key"
        assert config.litellm.api_key == "test-llm-key"
        assert config.litellm.model == "gpt-3.5-turbo"
        assert config.litellm.temperature == 0.7
        assert config.litellm.max_tokens == 4000
    finally:
        config_path.unlink()


def test_load_config_missing_file():
    """Test loading configuration from non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("non-existent-config.json"))


def test_load_config_invalid_json():
    """Test loading configuration with invalid JSON."""
    with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content")
        config_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_create_sample_config():
    """Test creating a sample configuration file."""
    with NamedTemporaryFile(suffix='.json', delete=False) as f:
        config_path = Path(f.name)
    
    config_path.unlink()  # Remove the file so we can test creation
    
    try:
        create_sample_config(config_path)
        assert config_path.exists()
        
        with open(config_path) as f:
            config_data = json.load(f)
        
        assert "firecrawl" in config_data
        assert "litellm" in config_data
        assert "prompt" in config_data
        assert "api_key" in config_data["firecrawl"]
        assert "api_key" in config_data["litellm"]
    finally:
        if config_path.exists():
            config_path.unlink()