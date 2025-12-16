#!/usr/bin/env python3
"""
Keyboard interrupt handler for Grace CLI.
Handles ESC to stop AI service and double Ctrl+C to exit.
"""

import sys
import signal
import threading
import time
from typing import Optional, Callable
import asyncio
from rich.console import Console

class InterruptHandler:
    """Handles keyboard interrupts with custom behavior."""
    
    def __init__(self):
        self.console = Console()
        self._ctrl_c_count = 0
        self._ctrl_c_timeout = None
        self._ai_service_running = False
        self._ai_task: Optional[asyncio.Task] = None
        self._shutdown_requested = False
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
        self._exit_callback: Optional[Callable] = None
        
    def set_exit_callback(self, callback: Callable):
        """Set callback to be called when exit is requested."""
        self._exit_callback = callback
        
    def start_ai_service(self, task: asyncio.Task):
        """Mark that AI service is running."""
        self._ai_service_running = True
        self._ai_task = task
        self._shutdown_requested = False
        
    def stop_ai_service(self):
        """Stop the AI service only."""
        if self._ai_service_running and self._ai_task and not self._ai_task.done():
            self._ai_service.cancel()
            self._ai_service_running = False
            self._shutdown_requested = True
            self.console.print("\n[yellow]Interrupted service stopped. Press Enter to continue or Ctrl+C again to exit.[/yellow]")
            return True
        return False
        
    def is_ai_service_running(self) -> bool:
        """Check if AI service is currently running."""
        return self._ai_service_running and self._ai_task and not self._ai_task.done()
        
    def _handle_sigint(self, signum, frame):
        """Handle Ctrl+C (SIGINT)."""
        current_time = time.time()
        
        # Check if this is a double Ctrl+C (within 2 seconds)
        if self._ctrl_c_timeout and (current_time - self._ctrl_c_timeout) < 2.0:
            # Double Ctrl+C - exit the application
            self.console.print("\n\n[bold red]Grace CLI terminated[/bold red]")
            if self._exit_callback:
                self._exit_callback()
            else:
                sys.exit(0)
            return
            
        # Single Ctrl+C
        self._ctrl_c_timeout = current_time
        
        # If AI service is running, stop it first
        if self.is_ai_service_running():
            if self.stop_ai_service():
                return  # AI service stopped, don't propagate signal
                
        # If no AI service is running, show hint
        if not self._shutdown_requested:
            self.console.print("\n[yellow]Press Ctrl+C again [/yellow]")
        else:
            self.console.print("\n[yellow]AI service already stopped. Press Ctrl+C again to exit Grace CLI[/yellow]")
            
    def _handle_sigterm(self, signum, frame):
        """Handle termination signal."""
        self.console.print("\n[bold red]Grace CLI terminated (SIGTERM)[/bold red]")
        if self._exit_callback:
            self._exit_callback()
        else:
            sys.exit(0)
            
    def setup(self):
        """Set up signal handlers."""
        # Store original handlers
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_sigint)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_sigterm)
        
    def cleanup(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)

# Global instance
interrupt_handler = InterruptHandler()

def setup_interrupt_handler():
    """Set up the global interrupt handler."""
    interrupt_handler.setup()
    
def cleanup_interrupt_handler():
    """Clean up the global interrupt handler."""
    interrupt_handler.cleanup()
    
def get_interrupt_handler() -> InterruptHandler:
    """Get the global interrupt handler instance."""
    return interrupt_handler
