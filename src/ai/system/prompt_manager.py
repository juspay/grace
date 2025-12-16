"""Enhanced Prompt Manager for Grace Code with Promcode Integration.

This module provides advanced prompt management capabilities including:
- Multi-source prompt loading
- Prompt inheritance and overriding
- Context-aware prompt selection
- Dynamic prompt reloading
- Prompt validation and testing
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptSource(Enum):
    """Enumeration of prompt sources."""
    DEFAULT = "default"
    PROMCODE = "promcode"
    USER = "user"
    SYSTEM = "system"

@dataclass
class PromptMetadata:
    """Metadata for prompt configuration."""
    version: str = "1.0.0"
    created: str = ""
    description: str = ""
    author: str = ""
    source: PromptSource = PromptSource.DEFAULT
    last_loaded: Optional[datetime] = None
    file_path: Optional[Path] = None
    compatibility: Dict[str, str] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)

@dataclass
class PromptEntry:
    """A single prompt entry with metadata."""
    name: str
    content: str
    metadata: PromptMetadata
    source: PromptSource
    priority: int = 0  # Higher priority overrides lower priority

class PromptManager:
    """Enhanced prompt manager with multi-source support and advanced features."""
    
    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        """Initialize the prompt manager.
        
        Args:
            base_dir: Base directory for prompt files. Defaults to system directory.
        """
        if base_dir is None:
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)
        
        self._prompts: Dict[str, PromptEntry] = {}
        self._sources: Dict[PromptSource, Dict[str, Any]] = {}
        self._metadata: Dict[PromptSource, PromptMetadata] = {}
        self._loaded_files: Dict[Path, datetime] = {}
        
        # Default prompt files configuration
        self._prompt_files = {
            PromptSource.DEFAULT: "prompts.yaml",
            PromptSource.PROMCODE: "../../Promcode-prompts.yaml",  # Root level
            PromptSource.SYSTEM: "code-prompts.yaml",
        }
        
        # Load all available prompt sources
        self._load_all_sources()
    
    def _load_all_sources(self) -> None:
        """Load prompts from all available sources."""
        # Load in priority order (lower priority first, so higher priority overrides)
        sources_by_priority = [
            (PromptSource.DEFAULT, 1),
            (PromptSource.SYSTEM, 2),
            (PromptSource.PROMCODE, 3),  # Highest priority
            (PromptSource.USER, 4),  # User overrides everything
        ]
        
        for source, priority in sources_by_priority:
            try:
                self._load_source(source, priority)
            except Exception as e:
                logger.warning(f"Failed to load {source.value} prompts: {e}")
    
    def _load_source(self, source: PromptSource, priority: int) -> None:
        """Load prompts from a specific source.
        
        Args:
            source: The prompt source to load
            priority: Priority level for prompt resolution
        """
        if source not in self._prompt_files:
            return
        
        file_path = self._resolve_file_path(source)
        if not file_path or not file_path.exists():
            if source == PromptSource.PROMCODE:
                logger.info(f"Promcode prompts file not found at {file_path}, skipping")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Extract metadata if present
            metadata_dict = data.pop('metadata', {})
            metadata = PromptMetadata(
                version=metadata_dict.get('version', '1.0.0'),
                created=metadata_dict.get('created', ''),
                description=metadata_dict.get('description', ''),
                author=metadata_dict.get('author', ''),
                source=source,
                last_loaded=datetime.now(),
                file_path=file_path,
                compatibility=metadata_dict.get('compatibility', {}),
                features=metadata_dict.get('features', [])
            )
            
            self._sources[source] = data
            self._metadata[source] = metadata
            self._loaded_files[file_path] = datetime.now()
            
            # Load individual prompts with priority
            for prompt_name, prompt_content in data.items():
                if isinstance(prompt_content, str):
                    prompt_entry = PromptEntry(
                        name=prompt_name,
                        content=prompt_content,
                        metadata=metadata,
                        source=source,
                        priority=priority
                    )
                    
                    # Override if higher priority or doesn't exist
                    if (prompt_name not in self._prompts or 
                        self._prompts[prompt_name].priority <= priority):
                        self._prompts[prompt_name] = prompt_entry
            
            logger.info(f"Loaded {len(data)} prompts from {source.value} ({file_path})")
            
        except Exception as e:
            logger.error(f"Error loading prompts from {file_path}: {e}")
            raise
    
    def _resolve_file_path(self, source: PromptSource) -> Optional[Path]:
        """Resolve the file path for a given source.
        
        Args:
            source: The prompt source
            
        Returns:
            Resolved file path or None if not found
        """
        if source not in self._prompt_files:
            return None
        
        file_name = self._prompt_files[source]
        
        # Try multiple resolution strategies
        candidates = [
            self.base_dir / file_name,  # Relative to base dir
            Path(file_name),  # Absolute or relative to current dir
            Path.cwd() / file_name,  # Relative to current working directory
        ]
        
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.exists():
                return resolved
        
        return None
    
    def get(self, prompt_name: str, **kwargs: Any) -> str:
        """Get a prompt with optional formatting.
        
        Args:
            prompt_name: Name of the prompt to retrieve
            **kwargs: Variables for prompt formatting
            
        Returns:
            Formatted prompt string
            
        Raises:
            KeyError: If prompt not found
        """
        if prompt_name not in self._prompts:
            raise KeyError(f"Prompt '{prompt_name}' not found")
        
        prompt_entry = self._prompts[prompt_name]
        content = prompt_entry.content
        
        if kwargs:
            try:
                return content.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format variable in prompt '{prompt_name}': {e}")
                return content
        
        return content
    
    def get_enhanced(self, tool_name: str, fallback_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Get an enhanced prompt for a specific tool.
        
        This method looks for enhanced prompts first, then falls back to standard prompts.
        
        Args:
            tool_name: Name of the tool (e.g., 'fileRead', 'grep')
            fallback_prompt: Fallback prompt if enhanced version not found
            **kwargs: Variables for prompt formatting
            
        Returns:
            Enhanced or fallback prompt string
        """
        # Try enhanced version first
        enhanced_name = f"enhanced{tool_name.capitalize()}"
        if enhanced_name in self._prompts:
            return self.get(enhanced_name, **kwargs)
        
        # Try standard version
        if tool_name in self._prompts:
            return self.get(tool_name, **kwargs)
        
        # Use fallback if provided
        if fallback_prompt:
            if kwargs:
                try:
                    return fallback_prompt.format(**kwargs)
                except KeyError:
                    return fallback_prompt
            return fallback_prompt
        
        # Last resort: return a generic prompt
        return f"Execute {tool_name} operation with enhanced analysis and reporting."
    
    def get_with_values(self, prompt_name: str, values: Dict[str, str]) -> str:
        """Get a prompt with variable substitution.
        
        Args:
            prompt_name: Name of the prompt
            values: Dictionary of variable substitutions
            
        Returns:
            Prompt with substituted values
        """
        prompt = self.get(prompt_name)
        
        for key, value in values.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        
        return prompt
    
    def list_prompts(self, source: Optional[PromptSource] = None) -> List[str]:
        """List available prompts, optionally filtered by source.
        
        Args:
            source: Optional source filter
            
        Returns:
            List of prompt names
        """
        if source is None:
            return list(self._prompts.keys())
        
        return [
            name for name, entry in self._prompts.items()
            if entry.source == source
        ]
    
    def get_prompt_info(self, prompt_name: str) -> Optional[PromptEntry]:
        """Get detailed information about a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            PromptEntry with metadata or None if not found
        """
        return self._prompts.get(prompt_name)
    
    def get_source_metadata(self, source: PromptSource) -> Optional[PromptMetadata]:
        """Get metadata for a specific source.
        
        Args:
            source: The prompt source
            
        Returns:
            Metadata for the source or None if not found
        """
        return self._metadata.get(source)
    
    def reload_source(self, source: PromptSource) -> bool:
        """Reload prompts from a specific source.
        
        Args:
            source: The source to reload
            
        Returns:
            True if successfully reloaded, False otherwise
        """
        try:
            # Remove existing prompts from this source
            to_remove = [
                name for name, entry in self._prompts.items()
                if entry.source == source
            ]
            for name in to_remove:
                del self._prompts[name]
            
            # Reload the source
            priority = {
                PromptSource.DEFAULT: 1,
                PromptSource.SYSTEM: 2,
                PromptSource.PROMCODE: 3,
                PromptSource.USER: 4,
            }.get(source, 1)
            
            self._load_source(source, priority)
            
            # Reload all other sources to restore proper priority order
            self._load_all_sources()
            
            logger.info(f"Successfully reloaded {source.value} prompts")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload {source.value} prompts: {e}")
            return False
    
    def reload_all(self) -> bool:
        """Reload all prompt sources.
        
        Returns:
            True if all sources reloaded successfully, False otherwise
        """
        try:
            self._prompts.clear()
            self._sources.clear()
            self._metadata.clear()
            self._loaded_files.clear()
            
            self._load_all_sources()
            
            logger.info("Successfully reloaded all prompt sources")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload all prompts: {e}")
            return False
    
    def validate_prompts(self) -> Dict[str, List[str]]:
        """Validate all loaded prompts for common issues.
        
        Returns:
            Dictionary mapping prompt names to list of issues found
        """
        issues = {}
        
        for name, entry in self._prompts.items():
            prompt_issues = []
            content = entry.content
            
            # Check for empty content
            if not content or not content.strip():
                prompt_issues.append("Empty or whitespace-only content")
            
            # Check for unclosed format variables
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                prompt_issues.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
            
            # Check for very short prompts (might be incomplete)
            if len(content.strip()) < 20:
                prompt_issues.append("Very short content (might be incomplete)")
            
            # Check for very long prompts (might need splitting)
            if len(content) > 10000:
                prompt_issues.append("Very long content (consider splitting)")
            
            if prompt_issues:
                issues[name] = prompt_issues
        
        return issues
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded prompts.
        
        Returns:
            Dictionary with various statistics
        """
        stats = {
            "total_prompts": len(self._prompts),
            "sources_loaded": len(self._sources),
            "prompts_by_source": {},
            "total_content_length": 0,
            "average_prompt_length": 0,
            "loaded_files": list(str(path) for path in self._loaded_files.keys()),
            "last_reload": max(self._loaded_files.values()) if self._loaded_files else None
        }
        
        # Calculate per-source statistics
        for source in PromptSource:
            source_prompts = [entry for entry in self._prompts.values() if entry.source == source]
            stats["prompts_by_source"][source.value] = len(source_prompts)
        
        # Calculate content statistics
        total_length = sum(len(entry.content) for entry in self._prompts.values())
        stats["total_content_length"] = total_length
        
        if self._prompts:
            stats["average_prompt_length"] = total_length // len(self._prompts)
        
        return stats

# Global instance for easy access
_prompt_manager_instance: Optional[PromptManager] = None

def get_prompt_manager(base_dir: Optional[Union[str, Path]] = None) -> PromptManager:
    """Get the global prompt manager instance.
    
    Args:
        base_dir: Base directory for prompt files (only used on first call)
        
    Returns:
        Global PromptManager instance
    """
    global _prompt_manager_instance
    
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager(base_dir)
    
    return _prompt_manager_instance

def reset_prompt_manager() -> None:
    """Reset the global prompt manager instance.
    
    Useful for testing or when configuration changes.
    """
    global _prompt_manager_instance
    _prompt_manager_instance = None
