"""LiteLLM client for AI-powered tech spec generation."""

from pathlib import Path

from typing import List, Optional, Tuple, Any
import datetime

try:
    import litellm  # type: ignore[import-untyped]
except ImportError:
    litellm = None  # type: ignore[assignment]

from src.types.config import AIConfig
from src.utils.ai_utils import combine_markdown_files
from .system.prompt_config import prompt_config

class AIService:
    config: AIConfig
    def __init__(self, config: AIConfig):
        if litellm is None:
            raise ImportError("litellm package is required. Install with: pip install litellm")

        self.config = config
        if config.base_url:
            litellm.api_base = config.base_url
        litellm.api_key = config.api_key

    def generate(self, messages: Any,  max_tokens: Optional[int] = None) -> Tuple[str, bool, str]:
        try:
            # Use config max_tokens if not provided
            if max_tokens is None:
                max_tokens = self.config.max_tokens

            completion_args = {
                    "model": self.config.model_id,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "api_key": self.config.api_key,
                    "temperature": 0.3,
                }
            if self.config.base_url:
                    completion_args["api_base"] = self.config.base_url
            response = litellm.completion(**completion_args)
            result = response.choices[0].message["content"]
            if not result or not result.strip():
                return "", False, "No content generated"
            return result, True, ""

        except Exception as e:
            raise RuntimeError(f"Error generating text: {str(e)}")
    
    def generate_tech_spec(self, markdown_files: List[Path], prompt: str) -> Tuple[bool, Optional[str], Optional[str]]:
        
        try:
            combined_content : List[str] = combine_markdown_files(markdown_files)
            if not combined_content or len(combined_content) == 0:
                return False, "", "No content found in markdown files"
            prompt = prompt_config().get_with_values("techspecPrompt", {"content": "check in user message"}) or ""
            messages = [{"role": "user", "content": content} for content in combined_content]
            messages.insert(0, {"role": "system", "content": prompt})

            tech_spec, success, error = self.generate(messages)
            if not success:
                return False, None, error
            
            return True, tech_spec, None

        except Exception as e:
            return False, None, str(e)

    def get_file_name(self, urls: List[str], connector: bool = True, base_name: str = "tech_spec.md") -> str:
        try:
            prompt = prompt_config().get_with_values("techspecFileNamePrompt", {"urls": ", ".join(urls),
                "isConnectorAvailable" :  "give the name like this connectorName/connectorName" if connector else ""}) or "" 
            name = self.generate([{"role": "user", "content": prompt}], max_tokens=10)
            return name[0].strip().replace(" ", "_") + ".md"
        except Exception as e:
            return base_name
       
        