import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from .prompt_manager import get_prompt_manager, PromptManager
import logging

logger = logging.getLogger(__name__)

class PromptConfig:
    """Enhanced PromptConfig with Promcode integration and backward compatibility."""

    def __init__(self, config_path: Optional[str] = None, promptfile: Optional[str] = "prompts.yaml", 
                 use_enhanced: bool = True):
        """Initialize PromptConfig with optional enhanced features.
        
        Args:
            config_path: Path to specific config file
            promptfile: Name of the prompt file
            use_enhanced: Whether to use enhanced prompt manager features
        """
        self.use_enhanced = use_enhanced
        
        if config_path is None:
            # Default to prompts.yaml in the same directory
            self.config_path: Path = Path(__file__).parent / promptfile
        else:
            self.config_path = Path(config_path)

        self._prompts: Dict[str, Any] = {}
        self._prompt_manager: Optional[PromptManager] = None
        
        if use_enhanced:
            try:
                self._prompt_manager = get_prompt_manager(Path(__file__).parent)
                logger.info("Enhanced prompt manager initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced prompt manager: {e}")
                logger.info("Falling back to legacy prompt loading")
                self.use_enhanced = False
        
        if not self.use_enhanced:
            self._load_prompts()

    def _load_prompts(self) -> None:
        """Legacy prompt loading method for backward compatibility."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._prompts = yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompts configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")

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
        if self.use_enhanced and self._prompt_manager:
            try:
                return self._prompt_manager.get(prompt_name, **kwargs)
            except KeyError:
                # Try enhanced version if available
                try:
                    return self._prompt_manager.get_enhanced(prompt_name, **kwargs)
                except KeyError:
                    pass
                # Fall back to legacy if enhanced fails
                logger.debug(f"Enhanced prompt '{prompt_name}' not found, trying legacy")
        
        # Legacy fallback
        if prompt_name not in self._prompts:
            raise KeyError(f"Prompt '{prompt_name}' not found in configuration")

        prompt = self._prompts[prompt_name]

        if kwargs:
            return str(prompt.format(**kwargs))
        return str(prompt)
    
    def get_enhanced(self, tool_name: str, fallback_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Get an enhanced prompt for a specific tool.
        
        This method provides access to enhanced prompts from Promcode-prompts.yaml.
        
        Args:
            tool_name: Name of the tool (e.g., 'fileRead', 'grep')
            fallback_prompt: Fallback prompt if enhanced version not found
            **kwargs: Variables for prompt formatting
            
        Returns:
            Enhanced or fallback prompt string
        """
        if self.use_enhanced and self._prompt_manager:
            return self._prompt_manager.get_enhanced(tool_name, fallback_prompt, **kwargs)
        
        # Legacy fallback
        if fallback_prompt:
            if kwargs:
                try:
                    return fallback_prompt.format(**kwargs)
                except KeyError:
                    return fallback_prompt
            return fallback_prompt
        
        return f"Execute {tool_name} operation."

    def get_with_values(self, prompt_name: str, values: Dict[str, str]) -> str:
        """Get a prompt with variable substitution.
        
        Args:
            prompt_name: Name of the prompt
            values: Dictionary of variable substitutions
            
        Returns:
            Prompt with substituted values
        """
        if self.use_enhanced and self._prompt_manager:
            try:
                return self._prompt_manager.get_with_values(prompt_name, values)
            except KeyError:
                pass
        
        # Legacy fallback
        prompt = self.get(prompt_name)

        for key, value in values.items():
            prompt = prompt.replace(f"{{{key}}}", value)
        return prompt

    def get_all(self) -> Dict[str, Any]:
        """Get all available prompts.
        
        Returns:
            Dictionary of all prompts
        """
        if self.use_enhanced and self._prompt_manager:
            # Return all prompts from enhanced manager
            result = {}
            for prompt_name in self._prompt_manager.list_prompts():
                try:
                    result[prompt_name] = self._prompt_manager.get(prompt_name)
                except Exception as e:
                    logger.warning(f"Failed to get prompt '{prompt_name}': {e}")
            return result
        
        # Legacy fallback
        return self._prompts.copy()

    def reload(self) -> None:
        """Reload prompts from sources."""
        if self.use_enhanced and self._prompt_manager:
            success = self._prompt_manager.reload_all()
            if not success:
                logger.warning("Enhanced prompt reload failed, falling back to legacy")
                self.use_enhanced = False
                self._load_prompts()
        else:
            self._load_prompts()

    @property
    def prompt_names(self) -> List[str]:
        """Get list of available prompt names.
        
        Returns:
            List of prompt names
        """
        if self.use_enhanced and self._prompt_manager:
            return self._prompt_manager.list_prompts()
        
        return list(self._prompts.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded prompts.
        
        Returns:
            Dictionary with prompt statistics
        """
        if self.use_enhanced and self._prompt_manager:
            return self._prompt_manager.get_statistics()
        
        # Legacy statistics
        return {
            "total_prompts": len(self._prompts),
            "sources_loaded": 1,
            "prompts_by_source": {"legacy": len(self._prompts)},
            "enhanced_features": False
        }
    
    def validate_prompts(self) -> Dict[str, List[str]]:
        """Validate loaded prompts for issues.
        
        Returns:
            Dictionary mapping prompt names to list of issues
        """
        if self.use_enhanced and self._prompt_manager:
            return self._prompt_manager.validate_prompts()
        
        # Basic legacy validation
        issues = {}
        for name, content in self._prompts.items():
            prompt_issues = []
            if not content or not str(content).strip():
                prompt_issues.append("Empty or whitespace-only content")
            if prompt_issues:
                issues[name] = prompt_issues
        
        return issues


_prompt_config_instance: Optional[PromptConfig] = None


def prompt_config(config_path: Optional[str] = None, promptfile: Optional[str] = "prompts.yaml") -> PromptConfig:
    global _prompt_config_instance

    if _prompt_config_instance is None:
        _prompt_config_instance = PromptConfig(config_path, promptfile)

    return _prompt_config_instance
