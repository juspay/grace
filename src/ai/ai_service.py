from pathlib import Path

from typing import List, Optional, Tuple, Any, Union

try:
    import litellm  # type: ignore[import-untyped]
except ImportError:
    litellm = None  # type: ignore[assignment]

from src.types.config import AIConfig
from src.utils.ai_utils import combine_markdown_files
from .system.prompt_config import prompt_config
from src.config import get_config
class AIService:
    config: AIConfig
    def __init__(self, config: Union[AIConfig, None] = None):
        if litellm is None:
            raise ImportError("litellm package is required. Install with: pip install litellm")

        self.config = config or get_config().getAiConfig()
        if self.config.base_url:
            litellm.api_base = self.config.base_url
        litellm.api_key = self.config.api_key

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
                    "temperature": self.config.temperature,
                }
            if self.config.base_url:
                    completion_args["api_base"] = self.config.base_url
            response = litellm.completion(**completion_args)
            result = response.choices[0].message["content"]
            if not result or not result.strip():
                return "", False, "No content generated"
            return result, True, ""

        except Exception as e:
            return "", False, str(e)
    
    async def vision_generate(self, messages:Any, max_tokens: Optional[int] = None) -> Any:
        completion_args = {
                    "model": self.config.vision_model_id,
                    "messages": messages,
                    "api_key": self.config.api_key,
                    "temperature": 0.1,
                }
        if max_tokens is not None:
            completion_args["max_tokens"] = max_tokens

        if self.config.base_url:
            completion_args["api_base"] = self.config.base_url
        
        # Use async completion
        response = await litellm.acompletion(**completion_args)
        result = response.choices[0].message.content
        if not result or not result.strip():
            return ""
        return result


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
       
    def generate_mock_server(self, tech_spec: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        try:
            prompt = prompt_config().get_with_values("techspecMockServerPrompt", {"tech_spec": tech_spec or ""}) or ""
            messages = [
                {"role": "user", "content": prompt},
            ]
            response, success, error = self.generate(messages)
            if not success:
                return False, None, error
            
            return True, response, None

        except Exception as e:
            return False, None, str(e)
    
    def get_ai_response(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Get a simple AI response for a given prompt.
        
        Args:
            prompt: The prompt to send to the AI
            max_tokens: Maximum tokens for the response
            
        Returns:
            AI response string
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            response, success, error = self.generate(messages, max_tokens)
            
            if success:
                return response
            else:
                raise Exception(f"AI generation failed: {error}")
                
        except Exception as e:
            raise Exception(f"Failed to get AI response: {str(e)}")


def get_ai_service(config: Union[AIConfig, None] = None) -> AIService:
    """
    Get an AIService instance.
    
    Args:
        config: Optional AI configuration
        
    Returns:
        AIService instance
    """
    return AIService(config)
