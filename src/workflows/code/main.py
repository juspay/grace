import asyncio
from typing import List, Any
from langchain_core.messages import HumanMessage, AIMessage
from .agent import create_langchain_agent_with_model_validation, tools as available_tools
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.rule import Rule
from src.config import get_config
from .ui import ui
from .tool_wrapper import wrap_tool_functions
from . import tool_functions
from src.utils.interrupt_handler import setup_interrupt_handler, cleanup_interrupt_handler, get_interrupt_handler

console = Console()
# Wrap tool functions with visualization
wrapped_tool_functions = wrap_tool_functions(tool_functions)

# Check if debug mode is enabled
DEBUG = get_config().getLogConfig().debug

# Suppress verbose LangChain output if not in debug mode
if not DEBUG:
    import logging
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langchain_community").setLevel(logging.WARNING)
    import sys
    # Suppress LangChain's verbose output
    class SuppressOutput:
        def write(self, text):
            if '[updates]' not in text and '[values]' not in text:
                sys.stdout.write(text)
        def flush(self):
            pass
    
    # This will suppress the debug output during agent execution
    import contextlib
    import io

def show_welcome():
    """Display welcome message using enhanced UI"""
    ui.show_welcome()

def show_tools():
    """List available AI tools"""
    console.print("\n[bold cyan]Available AI Tools:[/bold cyan]")
    tools_table = Table(show_header=True, box=None)
    tools_table.add_column("Tool", style="bold yellow")
    tools_table.add_column("Description")
    
    for tool in available_tools:
        tools_table.add_row(tool.name, tool.description)
    
    console.print(tools_table)
    console.print(f"[dim]Total tools available: {len(available_tools)}[/dim]")
    console.print()

async def get_ai_response(agent, user_input: str, chat_session: List[Any]) -> str:
    spinner = Spinner("dots", text="[bold cyan]Thinking...[/bold cyan]")
    with Live(spinner, refresh_per_second=10, console=console):
        try:
            # Prepare messages for LangChain agent
            messages = []
            for msg in chat_session:
                messages.append(msg)
            
            # Add current user message
            messages.append(HumanMessage(content=user_input))
            
            # Invoke the LangChain agent
            result = await agent.ainvoke({"messages": messages})
            
            # Extract the response content
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict):
                    return last_message.get("content", str(last_message))
            
            return str(result) if result else "No response received"
            
        except Exception as e:
            if DEBUG:
                console.print(f"[dim red]DEBUG: Error in AI response: {e}[/dim red]")
            return f"Error: {str(e)}"


def create_langchain_agent():
    """Create LangChain agent instance"""
    return create_langchain_agent_with_model_validation()

def format_ai_response(response: str) -> None:
    """Format and display AI response with Rich styling"""
    
    # Simple AI response without borders, just styled title
    console.print(f"[bold blue]GRACE AI:[/bold blue]")
    console.print(Markdown(response))

def show_user_input(user_input: str) -> None:
    """Display user input with simple styling"""
    console.print(f"[bold green]You:[/bold green] {user_input}")

async def chat_loop():
    # Set up interrupt handler
    setup_interrupt_handler()
    interrupt_handler = get_interrupt_handler()
    
    agent = create_langchain_agent()
    
    # Initialize UI
    ui.chat_history = []  # Start with empty chat history
    show_welcome()
    
    # Show interrupt handling instructions
    console.print("[dim]💡 Press Ctrl+C to stop AI service, double Ctrl+C to exit Grace CLI[/dim]")
    console.print()
    
    # Start the live display
    ui.start_live_display()
    
    def exit_grace():
        """Exit Grace CLI gracefully."""
        ui.stop_live_display()
        console.print("\n[bold red]Goodbye! Thanks for using Grace Code![/bold red]")
        cleanup_interrupt_handler()

    # Set exit callback
    interrupt_handler.set_exit_callback(exit_grace)

    try:
        while True:
            try:
                # Stop live display temporarily for input
                ui.stop_live_display()
                
                user_input = await asyncio.to_thread(
                    console.input, 
                    "[bold green]>[/bold green] ", 
                    password=False
                )

                if not user_input.strip():
                    # Restart live display if no input
                    ui.start_live_display()
                    continue

                # Handle commands
                if user_input.strip().lower() == "/exit":
                    ui.stop_live_display()
                    console.print("\n[bold red]Goodbye! Thanks for using Grace CLI![/bold red]")
                    break
                
                if user_input.strip().lower() == "/help":
                    show_welcome()
                    ui.start_live_display()
                    continue

                if user_input.strip().lower() == "/tools":
                    show_tools()
                    ui.start_live_display()
                    continue

                if user_input.strip().lower() == "/clear":
                    ui.chat_history.clear()
                    ui.tool_calls.clear()
                    console.print("[bold yellow]Chat history cleared.[/bold yellow]")
                    ui.start_live_display()
                    continue
                
                if user_input.strip().lower() == "/status":
                    ui.stop_live_display()
                    ui.show_detailed_status()
                    ui.start_live_display()
                    continue

                # Add user message to UI
                user_msg = HumanMessage(content=user_input)
                ui.add_message(user_msg)
                
                # Restart live display for processing
                ui.start_live_display()

                # Create AI response task
                async def get_ai_response_task():
                    """Get AI response with interrupt handling."""
                    try:
                        # Use the UI's managed chat history (already trimmed)
                        messages = list(ui.chat_history)
                        
                        # Invoke the LangChain agent
                        result = await agent.ainvoke({"messages": messages})
                        
                        # Extract the response content
                        response_content = ""
                        reasoning_content = None
                        
                        if result and "messages" in result:
                            last_message = result["messages"][-1]
                            
                            # Extract reasoning content if available
                            if isinstance(last_message, AIMessage):
                                try:
                                    from langchain_core.messages.base import _extract_reasoning_from_additional_kwargs
                                    reasoning_block = _extract_reasoning_from_additional_kwargs(last_message)
                                    if reasoning_block and reasoning_block.get("reasoning"):
                                        reasoning_content = reasoning_block["reasoning"]
                                except Exception:
                                    pass
                            
                            # Get the main response content
                            if hasattr(last_message, 'content'):
                                response_content = last_message.content
                            elif isinstance(last_message, dict):
                                response_content = last_message.get("content", str(last_message))
                        
                        return response_content or str(result) if result else "No response received", reasoning_content
                        
                    except asyncio.CancelledError:
                        return "[yellow]🛑 AI response cancelled by user[/yellow]", None
                    except Exception as e:
                        if DEBUG:
                            console.print(f"[dim red]DEBUG: Error in AI response: {e}[/dim red]")
                        return f"Error: {str(e)}", None

                # Start AI response task
                ai_task = asyncio.create_task(get_ai_response_task())
                interrupt_handler.start_ai_service(ai_task)

                # Get AI response with spinner
                spinner = Spinner("dots", text="[bold cyan]AI is thinking...[/bold cyan]")
                with Live(spinner, refresh_per_second=10, console=console):
                    try:
                        response_content, reasoning_content = await ai_task
                    except asyncio.CancelledError:
                        response_content = "[yellow]🛑 AI response cancelled by user[/yellow]"
                        reasoning_content = None
                    finally:
                        interrupt_handler._ai_service_running = False

                # Add AI response to UI with reasoning preserved in additional_kwargs
                if reasoning_content:
                    # Clean the reasoning content from the main response
                    cleaned_response = ui._clean_reasoning_from_content(response_content, reasoning_content)
                    ai_msg = AIMessage(content=cleaned_response)
                    ai_msg.additional_kwargs["reasoning_content"] = reasoning_content
                else:
                    ai_msg = AIMessage(content=response_content)
                
                ui.add_message(ai_msg)
                
                # Refresh the display
                ui.refresh()
                
            except (KeyboardInterrupt, EOFError):
                ui.stop_live_display()
                console.print("\n[bold red]Goodbye! Thanks for using Grace CLI![/bold red]")
                break
                
    except Exception as e:
        ui.stop_live_display()
        console.print(f"\n[bold red]An error occurred: {e}[/bold red]")
        console.print("[bold yellow]Please try again or use /exit to quit.[/bold yellow]")
    finally:
        # Ensure live display is stopped and cleanup
        ui.stop_live_display()
        cleanup_interrupt_handler()

if __name__ == "__main__":
    # Set up Rich console with some nice styling
    console.print(Rule("Grace CLI - AI-Powered Development Assistant", style="bold green"))
    asyncio.run(chat_loop())
