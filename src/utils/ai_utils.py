from typing import List, Dict, Any
from pathlib import Path

from src.types.config import AIConfig

def estimate_tokens(text: str) -> int:
    # Rough estimation: 1 token ≈ 4 characters for English text
    return len(text) // 4

def combine_markdown_files(markdown_files: List[Path], sendAsString: bool = False) -> str | List[str]:
    combined_content: List[str] = []
    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                combined_content.append(f"## Content from {file_path.name}\n\n{content}\n\n")
        except Exception as e:
            combined_content.append(f"## Error reading {file_path.name}\n\nError: {str(e)}\n\n")
    if sendAsString:
        return "\n".join(combined_content)
    return combined_content

def estimate_token_usage(markdown_files: List[Path], config: AIConfig) -> Dict[str, Any]:
    try:
        combined_content = combine_markdown_files(markdown_files, sendAsString=True)
        estimated_input_tokens = estimate_tokens(combined_content)
        estimated_total_tokens = estimated_input_tokens + config.max_tokens
        return {
            "estimated_input_tokens": estimated_input_tokens,
            "max_output_tokens": config.max_tokens,
            "estimated_total_tokens": estimated_total_tokens,
            "model": config.model_id
        }
    except Exception as e:
        return {"error": str(e)}


