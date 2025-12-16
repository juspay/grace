import asyncio
import time
import litellm
from typing import List, Any, Optional, Dict
from rich.console import Console
from rich.text import Text
from rich.live import Live
from rich.markdown import Markdown
from langchain_core.messages import HumanMessage, AIMessage
from src.config import get_config

class SimpleTerminalUI:
    """Simple terminal UI with inline tool call visualization and context window"""
    
    def __init__(self):
        self.console = Console()
        self.chat_history: List[Any] = []
        self.tool_calls: List[str] = []  # Simple list of tool call messages
        self.context_window_tokens = 0
        self.max_context_tokens = self._get_model_context_window()
        self.live = None
        self.compaction_threshold = 0.8  # Compact at 80% usage
        
    def _get_model_context_window(self) -> int:
        """Get the context window size for the configured model"""
        try:
            config = get_config()
            ai_config = config.getAiConfig()
            model_name = ai_config.model_id
            
            # Get model info from LiteLLM
            model_info = litellm.get_model_info(model_name)
            
            # Try to get max tokens from model info
            if model_info and 'max_tokens' in model_info:
                return model_info['max_tokens']
            
            # Fallback to common model contexts
            model_contexts = {
                'gemini-2.5-pro': 1048576,  # 1M tokens
                'gemini-2.5-flash': 1048576,
                'claude-sonnet-4': 200000,  # 200K tokens
                'claude-sonnet-4-20250514': 200000,
                'claude-sonnet-4-5': 200000,
                'gpt-4': 128000,  # 128K tokens
                'gpt-4-turbo': 128000,
                'gpt-4o': 128000,
                'gpt-4o-mini': 128000,
                'glm-46-fp8': 32768,  # Update GLM model context
                'glm-45-fp8': 32768,
                'glm-private': 32768,
                'gemini-embedding-001': 32768,
                'text-embedding-005': 32768,
                'glm45air-lora': 32768,
                'glm-latest': 32768,
                'xyne-spaces-minimax-m2': 32768,
                'claude-haiku-4-5-20251001': 200000,
                'minimaxai/minimax-m2': 128000,
                'glm-45-air': 32768,
                'glm45air-lora': 32768,
            }
            
            # Extract base model name
            for model_key in model_contexts:
                if model_key in model_name.lower():
                    return model_contexts[model_key]
            
            # If model not found, show available models and let user choose
            self._show_model_selection_dialog(model_contexts)
            
            # Default fallback
            return 1048576  # 1M tokens
            
        except Exception as e:
            # Default fallback if anything goes wrong
            return 1048576
    
    def _show_model_selection_dialog(self, available_models: dict):
        """Show model selection dialog for invalid/unknown models"""
        self.console.print(f"\n[red]⚠️  Model Configuration Issue[/red]")
        self.console.print(f"[dim]The configured model could not be detected properly.[/dim]")
        self.console.print(f"\n[cyan]Available models and their context windows:[/cyan]")
        
        # Display available models
        for i, (model, tokens) in enumerate(available_models.items(), 1):
            tokens_m = tokens // 1000000
            tokens_k = (tokens % 1000000) // 1000
            if tokens_m > 0:
                token_str = f"{tokens_m}M"
            elif tokens_k > 0:
                token_str = f"{tokens_k}K"
            else:
                token_str = f"{tokens:,}"
            
            self.console.print(f"  [yellow]{i:2d}.[/yellow] [bold]{model}[/bold] - {token_str} tokens")
        
        self.console.print(f"\n[dim]Please update your .env file with one of these models.[/dim]")
        
    def update_context_window(self, messages: List[Any]):
        """Update context window token count and compact if necessary"""
        # More accurate token estimation based on actual model capabilities
        total_tokens = 0
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                # Estimate tokens more accurately (rough approximation)
                words = len(msg.content.split())
                words = len(msg.content.split())
                
                # Different models have different token ratios:
                if self.max_context_tokens > 900000:  # Gemini models: ~1 char = ~3-4 tokens
                    tokens_per_word = 3.5
                elif self.max_context_tokens < 200000:  # Claude/GPT models: ~1 char = ~3-4 tokens
                    tokens_per_word = 3.5
                else:
                    tokens_per_word = 1.3  # Conservative fallback
                
                msg_tokens = int(words * tokens_per_word) + 10  # Add overhead per message
        
        self.context_window_tokens = total_tokens
        
        # Compact chat history if we're at or above threshold
        threshold_tokens = int(self.max_context_tokens * self.compaction_threshold)
        if self.context_window_tokens >= threshold_tokens:
            self._compact_chat_history(threshold_tokens)
    
    def _compact_chat_history(self, target_tokens: int):
        """Smartly compact chat history to stay within token limit"""
        if len(self.chat_history) <= 2:  # Keep at least 2 messages
            return
            
        # Keep recent messages (last 10-15) and summarize older ones
        recent_messages = self.chat_history[-10:] if len(self.chat_history) > 10 else self.chat_history[-5:]
        older_messages = self.chat_history[:-len(recent_messages)] if len(self.chat_history) > 10 else []
        
        # Calculate tokens for recent messages
        recent_tokens = 0
        for msg in recent_messages:
            if hasattr(msg, 'content') and msg.content:
                words = len(msg.content.split())
                recent_tokens += int(words * 1.3) + 10
        
        # If recent messages already fit, just keep them
        if recent_tokens <= target_tokens:
            self.chat_history = recent_messages
            self.context_window_tokens = recent_tokens
            return
        
        # If even recent messages don't fit, keep fewer
        final_history = []
        current_tokens = 0
        
        for msg in reversed(recent_messages):
            if hasattr(msg, 'content') and msg.content:
                words = len(msg.content.split())
                msg_tokens = int(words * 1.3) + 10
                
                if current_tokens + msg_tokens <= target_tokens:
                    final_history.insert(0, msg)
                    current_tokens += msg_tokens
            else:
                final_history.insert(0, msg)
        
        self.chat_history = final_history
        self.context_window_tokens = current_tokens
        
    def _trim_chat_history(self, max_tokens: int):
        """Legacy method - use _compact_chat_history instead"""
        self._compact_chat_history(max_tokens)
    
    def add_tool_call(self, tool_name: str, tool_input: str):
        """Add a tool call message"""
        # Extract file path or key info from input
        input_str = str(tool_input)
        if 'file_path' in input_str:
            try:
                import json
                data = json.loads(input_str)
                file_path = data.get('file_path', 'unknown')
                tool_msg = f"{tool_name} --> {file_path}"
            except:
                tool_msg = f"{tool_name} --> {input_str[:50]}..."
        else:
            tool_msg = f"{tool_name} --> {input_str[:50]}..."
        
        self.tool_calls.append(tool_msg)
    
    def add_message(self, message: Any):
        """Add a message to chat history"""
        self.chat_history.append(message)
        self.update_context_window(self.chat_history)
    
    def start_live_display(self):
        """Start the live display"""
        if not self.live:
            self.live = Live(
                self._render_display(),
                console=self.console,
                refresh_per_second=2,
                screen=False
            )
            self.live.start()
    
    def stop_live_display(self):
        """Stop the live display"""
        if self.live:
            self.live.stop()
            self.live = None
    
    def _extract_reasoning_content(self, message) -> str | None:
        """Extract reasoning content from AI message"""
        try:
            # Import the reasoning extraction function from LangChain
            from langchain_core.messages.base import _extract_reasoning_from_additional_kwargs
            
            reasoning_block = _extract_reasoning_from_additional_kwargs(message)
            if reasoning_block and reasoning_block.get("reasoning"):
                return reasoning_block["reasoning"]
        except Exception:
            pass
        
        # Fallback: check additional_kwargs directly
        if hasattr(message, 'additional_kwargs'):
            reasoning_content = message.additional_kwargs.get("reasoning_content")
            if reasoning_content and isinstance(reasoning_content, str):
                return reasoning_content
        
        # Additional fallback: extract embedded reasoning from content
        if hasattr(message, 'content') and isinstance(message.content, str):
            reasoning_content = self._extract_embedded_reasoning(message.content)
            if reasoning_content:
                return reasoning_content
        
        return None
    
    def _extract_embedded_reasoning(self, content: str) -> str | None:
        """Extract reasoning content embedded in the main response"""
        import re
        
        # Pattern 0: Look for the specific "🤔 Thinking:" pattern
        thinking_emoji_pattern = r'🤔\s*Thinking:\s*(.*?)(?=\n\n|\nGRACE AI:|$)'
        match = re.search(thinking_emoji_pattern, content, re.DOTALL)
        if match:
            reasoning = match.group(1).strip()
            if len(reasoning) > 10:  # Even short thinking content is valuable
                return reasoning
        
        # Pattern 1: Look for "thinking:" or similar markers
        thinking_patterns = [
            r'(?:thinking|thought|reasoning):?\s*\n?(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?:i should|i need to|let me|i\'ll):?\s*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'step by step:?\s*\n?(.*?)(?=\n\n|\n[A-Z]|$)',
        ]
        
        for pattern in thinking_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                # Only return if it's substantial (more than 20 chars and contains process words)
                if len(reasoning) > 20 and any(word in reasoning.lower() for word in ['because', 'since', 'first', 'then', 'next', 'step', 'need', 'should', 'because']):
                    return reasoning
        
        # Pattern 2: Look for content between specific markers
        marker_patterns = [
            r'<thinking>(.*?)</thinking>',
            r'<reasoning>(.*?)</reasoning>',
            r'<thought>(.*?)</thought>',
        ]
        
        for pattern in marker_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                if len(reasoning) > 20:
                    return reasoning
        
        # Pattern 3: Look for sentences that explicitly state thinking process
        thinking_sentences = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if (any(phrase in line.lower() for phrase in ['i should', 'i need to', 'let me', 'i\'ll', 'first, i', 'the first step'])
                and len(line) > 30):
                thinking_sentences.append(line)
        
        if thinking_sentences:
            return ' '.join(thinking_sentences[:2])  # Return first 2 thinking sentences
        
        return None

    def _clean_reasoning_from_content(self, content: str, reasoning_content: str) -> str:
        """Remove reasoning content from the main response"""
        import re
        
        # Remove the specific "🤔 Thinking:" pattern
        thinking_emoji_pattern = r'🤔\s*Thinking:.*?(?=\n\n|\nGRACE AI:|$)'
        cleaned_content = re.sub(thinking_emoji_pattern, '', content, flags=re.DOTALL)
        
        # Remove other reasoning patterns
        patterns_to_remove = [
            r'(?:thinking|thought|reasoning):?\s*\n?.*?(?=\n\n|\n[A-Z]|$)',
            r'<thinking>.*?</thinking>',
            r'<reasoning>.*?</reasoning>',
            r'<thought>.*?</thought>',
        ]
        
        for pattern in patterns_to_remove:
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up extra whitespace and newlines
        cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)  # Remove triple newlines
        cleaned_content = cleaned_content.strip()
        
        return cleaned_content

    def _render_display(self):
        """Render the complete display"""
        content_parts = []
        
        # Show recent chat history (last few messages)
        for msg in self.chat_history[-5:]:
            if isinstance(msg, HumanMessage):
                content_parts.append(f"[bold green]You:[/bold green] {msg.content}")
            elif isinstance(msg, AIMessage):
                # Extract reasoning content first
                reasoning_content = self._extract_reasoning_content(msg)
                
                if reasoning_content:
                    # Display reasoning in light color (gray/light blue)
                    content_parts.append(f"[dim cyan]🤔 Thinking:[/dim cyan] [dim white]{reasoning_content}[/dim white]")
                    content_parts.append("")  # Empty line for separation
                
                # Display main AI response
                if hasattr(msg, 'content') and msg.content:
                    # Clean up markdown bold markers that show as ** in plain text
                    clean_content = msg.content.replace('**', '').replace('*', '')
                    content_parts.append(f"[bold blue]GRACE AI:[/bold blue] {clean_content}")
        
        # Show recent tool calls
        if self.tool_calls:
            content_parts.append("")  # Empty line for separation
            for tool_call in self.tool_calls[-3:]:  # Show last 3 tool calls
                content_parts.append(f"[bold yellow]🔧 {tool_call}[/bold yellow]")
        
        # Add context window info at the bottom
        content_parts.append("")  # Empty line for separation
        usage_percent = (self.context_window_tokens / self.max_context_tokens) * 100
        usage_color = "green" if usage_percent < 50 else "yellow" if usage_percent < 80 else "red"
        
        # Simple progress bar
        bar_width = 30
        filled = int((usage_percent / 100) * bar_width)
        empty = bar_width - filled
        progress_bar = f"[{usage_color}]{'█' * filled}[dim]{'░' * empty}[/{usage_color}]"
        
        content_parts.append(f"[dim]Context: {self.context_window_tokens:,}/{self.max_context_tokens:,} tokens ({usage_percent:.1f}%)[/dim]")
        content_parts.append(progress_bar)
        
        return "\n".join(content_parts)
    
    def refresh(self):
        """Refresh the live display"""
        if self.live:
            self.live.update(self._render_display())
    
    def show_welcome(self):
        """Display welcome message using markdown"""
        welcome_text = """
# 🚀 Grace CLI Enhanced

*AI-Powered Development Assistant with real-time tool visualization*

## Features:
- Real-time context window monitoring
- Inline tool call visualization  
- Simple, clean interface

## Available commands:
- `/exit` - End the chat session
- `/help` - Show this help message
- `/tools` - List available AI tools
- `/clear` - Clear chat history
- `/status` - Show detailed status information

## Interrupt handling:
- **Ctrl+C** - Stop AI service (when AI is thinking)
- **Double Ctrl+C** - Exit Grace CLI completely

*Type your questions or commands below to get started.*
"""
        
        self.console.print(Markdown(welcome_text))
    
    def show_tools(self, tools: List[Any]):
        """Display available tools"""
        self.console.print("\n[cyan]Available AI Tools:[/cyan]")
        for tool in tools:
            self.console.print(f"  [yellow]• {tool.name}[/yellow] - {tool.description}")
        self.console.print(f"[dim]Total tools available: {len(tools)}[/dim]\n")
    
    def show_detailed_status(self):
        """Show detailed status information"""
        usage_percent = (self.context_window_tokens / self.max_context_tokens) * 100
        
        self.console.print(f"\n[green]📊 Detailed Status:[/green]")
        self.console.print(f" Context Window: {self.context_window_tokens:,}/{self.max_context_tokens:,} tokens ({usage_percent:.1f}%)")
        self.console.print(f" Chat History: {len(self.chat_history)} messages")
        self.console.print(f" Tool Calls: {len(self.tool_calls)} total")
        
        if self.tool_calls:
            self.console.print(f"\n[dim]Recent Tool Calls:[/dim]")
            for tool_call in self.tool_calls[-5:]:
                self.console.print(f" {tool_call}")
        
        self.console.print()

# Global UI instance
ui = SimpleTerminalUI()
