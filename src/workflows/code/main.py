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

console = Console()

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
    """Display welcome message with Rich styling"""
    welcome_text = """
    Welcome to Grace CLI - Your AI-Powered Development Assistant!
    I can read and write code, run shell commands, search the web, and help with various development tasks.
    Type your questions or commands below to get started.
    """

    panel = Markdown(welcome_text)
    
    console.print(panel)
    
    console.print("\n[bold cyan]Available commands:[/bold cyan]")
    commands_table = Table(show_header=False, box=None)
    commands_table.add_column("Command", style="bold yellow")
    commands_table.add_column("Description")
    commands_table.add_row("/exit", "End the chat session")
    commands_table.add_row("/help", "Show this help message")
    commands_table.add_row("/tools", "List available AI tools")
    commands_table.add_row("/clear", "Clear chat history")
    console.print(commands_table)
    console.print()

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
    agent = create_langchain_agent()
    chat_session = []

    show_welcome()

    while True:
        try:
            user_input = await asyncio.to_thread(
                console.input, 
                "[bold green]>[/bold green] ", 
                password=False
            )

            if not user_input.strip():
                continue

            if user_input.strip().lower() == "/exit":
                console.print("\n[bold red]Goodbye! Thanks for using Grace CLI![/bold red]")
                break
            
            if user_input.strip().lower() == "/help":
                show_welcome()
                continue

            if user_input.strip().lower() == "/tools":
                show_tools()
                continue

            if user_input.strip().lower() == "/clear":
                chat_session.clear()
                console.print("[bold yellow]Chat history cleared.[/bold yellow]")
                continue

            # Show user input
            console.print()
            show_user_input(user_input)

            # Get AI response with animation
            console.print()
            response = await get_ai_response(agent, user_input, chat_session)

            chat_session.extend([
                HumanMessage(content=user_input),
                AIMessage(content=response),
            ])

            console.print()
            format_ai_response(response)
            console.print()
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold red]Goodbye! Thanks for Grace CLI![/bold red]")
            break
        except Exception as e:
            console.print(f"\n[bold red]An error occurred: {e}[/bold red]")
            console.print("[bold yellow]Please try again or use /exit to quit.[/bold yellow]")

if __name__ == "__main__":
    # Set up Rich console with some nice styling
    console.print(Rule("Grace CLI - AI-Powered Development Assistant", style="bold green"))
    asyncio.run(chat_loop())
