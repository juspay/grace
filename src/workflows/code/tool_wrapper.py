import functools
import json
import asyncio
from typing import Any, Callable, Dict
from .ui import ui
from src.ai.system.prompt_config import PromptConfig
from rich.console import Console
import logging

logger = logging.getLogger(__name__)
console = Console()

class EnhancedToolCallWrapper:
    """Enhanced wrapper with Promcode integration for tool calls"""
    
    def __init__(self):
        """Initialize with enhanced prompt configuration."""
        try:
            self.prompt_config = PromptConfig(promptfile="code-prompts.yaml", use_enhanced=True)
            self.enhanced_available = True
            logger.info("Enhanced tool wrapper initialized with Promcode integration")
        except Exception as e:
            logger.warning(f"Failed to initialize enhanced prompts: {e}")
            self.enhanced_available = False
    
    def get_tool_prompt(self, tool_name: str) -> str:
        """Get enhanced prompt for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Enhanced prompt or default message
        """
        if not self.enhanced_available:
            return f"Executing {tool_name} with standard configuration"
        
        try:
            # Get enhanced prompt for the tool
            enhanced_prompt = self.prompt_config.get_enhanced(
                tool_name,
                fallback_prompt=f"Execute {tool_name} operation with enhanced analysis"
            )
            return enhanced_prompt
        except Exception as e:
            logger.debug(f"Failed to get enhanced prompt for {tool_name}: {e}")
            return f"Execute {tool_name} operation"
    
    def format_tool_display(self, tool_name: str, tool_input: str) -> str:
        """Format tool call for enhanced display.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input parameters
            
        Returns:
            Formatted display string
        """
        # Map tool names to emojis for better visualization
        tool_emojis = {
            'file_read': '📖',
            'file_write': '📝', 
            'file_edit': '✏️',
            'grep': '🔍',
            'glob': '📁',
            'bash': '⚡',
            'web_search': '🌐',
            'web_fetch': '📥',
            'agent': '🤖',
            'ask_user_question': '❓'
        }
        
        emoji = tool_emojis.get(tool_name, '🔧')
        
        if self.enhanced_available:
            return f"{emoji} Enhanced {tool_name.replace('_', ' ').title()}"
        else:
            return f"{emoji} {tool_name.replace('_', ' ').title()}"
    
    def wrap_tool_function(self, tool_name: str, tool_func: Callable) -> Callable:
        """Wrap a tool function with enhanced visualization and prompting"""
        
        @functools.wraps(tool_func)
        def wrapper(*args, **kwargs):
            # Extract the input for display
            tool_input = ""
            if args:
                tool_input = str(args[0])
            elif kwargs:
                tool_input = str(kwargs)
            
            # Get enhanced display format
            display_name = self.format_tool_display(tool_name, tool_input)
            
            # Add tool call message with enhanced formatting
            ui.add_tool_call(display_name, tool_input)
            ui.refresh()
            
            # Log enhanced prompt usage if available
            if self.enhanced_available:
                try:
                    prompt_info = self.get_tool_prompt(tool_name)
                    logger.debug(f"Using enhanced prompt for {tool_name}")
                except Exception as e:
                    logger.debug(f"Enhanced prompt not available for {tool_name}: {e}")
            
            # Execute the actual tool function
            return tool_func(*args, **kwargs)
        
        return wrapper

    def wrap_async_tool_function(self, tool_name: str, tool_func: Callable) -> Callable:
        """Wrap an async tool function with enhanced visualization and prompting"""
        
        @functools.wraps(tool_func)
        async def async_wrapper(*args, **kwargs):
            # Extract the input for display
            tool_input = ""
            if args:
                tool_input = str(args[0])
            elif kwargs:
                tool_input = str(kwargs)
            
            # Get enhanced display format
            display_name = self.format_tool_display(tool_name, tool_input)
            
            # Add tool call message with enhanced formatting
            ui.add_tool_call(display_name, tool_input)
            ui.refresh()
            
            # Log enhanced prompt usage if available
            if self.enhanced_available:
                try:
                    prompt_info = self.get_tool_prompt(tool_name)
                    logger.debug(f"Using enhanced prompt for {tool_name}")
                except Exception as e:
                    logger.debug(f"Enhanced prompt not available for {tool_name}: {e}")
            
            # Execute the actual tool function
            return await tool_func(*args, **kwargs)
        
        return async_wrapper

# Legacy wrapper for backward compatibility
class ToolCallWrapper:
    """Legacy wrapper for backward compatibility"""
    
    @staticmethod
    def wrap_tool_function(tool_name: str, tool_func: Callable) -> Callable:
        """Legacy wrap method - delegates to enhanced wrapper"""
        enhanced_wrapper = EnhancedToolCallWrapper()
        return enhanced_wrapper.wrap_tool_function(tool_name, tool_func)
    
    @staticmethod
    def wrap_async_tool_function(tool_name: str, tool_func: Callable) -> Callable:
        """Legacy async wrap method - delegates to enhanced wrapper"""
        enhanced_wrapper = EnhancedToolCallWrapper()
        return enhanced_wrapper.wrap_async_tool_function(tool_name, tool_func)

def wrap_tool_functions(tool_functions_module):
    """Wrap all tool functions in a module with enhanced visualization and Promcode integration"""
    
    wrapped_functions = {}
    enhanced_wrapper = EnhancedToolCallWrapper()
    
    # List of function names to wrap
    function_names = [
        'agent', 'bash', 'bash_output', 'exit_plan_mode', 'file_edit',
        'file_read', 'file_write', 'glob', 'grep', 'kill_shell',
        'list_mcp_resources', 'mcp', 'notebook_edit', 'read_mcp_resource',
        'todo_write', 'web_fetch', 'web_search', 'ask_user_question'
    ]
    
    for func_name in function_names:
        if hasattr(tool_functions_module, func_name):
            func = getattr(tool_functions_module, func_name)
            
            # Check if it's async
            if asyncio.iscoroutinefunction(func):
                wrapped_func = enhanced_wrapper.wrap_async_tool_function(func_name, func)
            else:
                wrapped_func = enhanced_wrapper.wrap_tool_function(func_name, func)
            
            wrapped_functions[func_name] = wrapped_func
    
    logger.info(f"Wrapped {len(wrapped_functions)} tool functions with enhanced Promcode integration")
    return wrapped_functions
