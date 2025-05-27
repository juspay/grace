"""LiteLLM client for AI-powered tech spec generation."""

from pathlib import Path
from typing import List, Optional, Tuple
import datetime

try:
    import litellm
except ImportError:
    litellm = None

from .config import LiteLLMConfig, PromptConfig


class LLMClient:
    """Client for interacting with LLM providers via LiteLLM."""
    
    def __init__(self, config: LiteLLMConfig):
        """Initialize the LLM client."""
        if litellm is None:
            raise ImportError("litellm package is required. Install with: pip install litellm")
        
        self.config = config
        
        # Set global LiteLLM configuration like your pattern
        if config.base_url:
            litellm.api_base = config.base_url
        
        litellm.api_key = config.api_key
    
    def generate_tech_spec(
        self, 
        markdown_files: List[Path], 
        prompt_config: PromptConfig
    ) -> Tuple[bool, str, str]:
        """
        Generate a technical specification from markdown documentation.
        
        Args:
            markdown_files: List of paths to markdown files
            prompt_config: Prompt configuration
            
        Returns:
            Tuple of (success: bool, tech_spec: str, error_message: str)
        """
        try:
            # Read and combine markdown content
            combined_content = self._combine_markdown_files(markdown_files)
            
            if not combined_content.strip():
                return False, "", "No content found in markdown files"
            
            # Prepare the prompt
            prompt = prompt_config.template.format(content=combined_content)
            
            # Prepare completion arguments (following your pattern)
            completion_args = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "api_key": self.config.api_key
            }
            
            # Add custom base URL if specified (for proxy setups)
            if self.config.base_url:
                completion_args["api_base"] = self.config.base_url
            
            # Add custom headers if specified (for proxy setups)
            if self.config.custom_headers:
                completion_args["extra_headers"] = self.config.custom_headers
            
            # Generate response using LiteLLM
            response = litellm.completion(**completion_args)
            
            tech_spec = response.choices[0].message.content
            
            if not tech_spec or not tech_spec.strip():
                return False, "", "Empty response from LLM"
            
            return True, tech_spec, ""
            
        except Exception as e:
            return False, "", f"LLM generation error: {str(e)}"
    
    def _combine_markdown_files(self, markdown_files: List[Path]) -> str:
        """Combine multiple markdown files into a single content string."""
        combined_content = []
        
        for file_path in markdown_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    combined_content.append(f"## Content from {file_path.name}\n\n{content}\n\n")
            except Exception as e:
                combined_content.append(f"## Error reading {file_path.name}\n\nError: {str(e)}\n\n")
        
        return "\n".join(combined_content)
    
    def save_tech_spec(self, tech_spec: str, output_dir: Path) -> Path:
        """Save the generated tech spec to a file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tech_spec_{timestamp}.md"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Technical Specification\n\n")
            f.write(f"**Generated:** {datetime.datetime.now().isoformat()}\n\n")
            f.write("---\n\n")
            f.write(tech_spec)
        
        return filepath
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the LLM connection and authentication.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Test with a simple prompt
            test_prompt = "Hello! Please respond with 'LLM connection successful' if you can receive this message."
            
            # Prepare test completion arguments (same as main completion)
            completion_args = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": test_prompt}],
                "temperature": 0.1,
                "max_tokens": 50,
                "api_key": self.config.api_key
            }
            
            # Add custom base URL if specified (for proxy setups)
            if self.config.base_url:
                completion_args["api_base"] = self.config.base_url
            
            # Add custom headers if specified (for proxy setups)
            if self.config.custom_headers:
                completion_args["extra_headers"] = self.config.custom_headers
            
            response = litellm.completion(**completion_args)
            
            response_text = response.choices[0].message.content
            
            if response_text:
                base_msg = f"LLM connection successful. Model: {self.config.model}"
                if self.config.base_url:
                    base_msg += f" (via proxy: {self.config.base_url})"
                return True, base_msg
            else:
                return False, "Empty response from LLM"
                
        except Exception as e:
            return False, f"LLM connection test failed: {str(e)}"
    
    def estimate_token_usage(self, markdown_files: List[Path]) -> dict:
        """Estimate token usage for processing the given files."""
        try:
            combined_content = self._combine_markdown_files(markdown_files)
            
            # Rough estimation: 1 token ≈ 4 characters for English text
            estimated_input_tokens = len(combined_content) // 4
            estimated_total_tokens = estimated_input_tokens + self.config.max_tokens
            
            return {
                "estimated_input_tokens": estimated_input_tokens,
                "max_output_tokens": self.config.max_tokens,
                "estimated_total_tokens": estimated_total_tokens,
                "model": self.config.model
            }
        except Exception as e:
            return {"error": str(e)}