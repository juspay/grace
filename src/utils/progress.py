"""
Progress tracking and visibility utilities for GRACE workflows
"""

import time
import threading
import signal
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime


class ProgressTracker:
    """Enhanced progress tracker with detailed visibility and interrupt handling"""
    
    def __init__(self, total_steps: int = 0, show_details: bool = True):
        self.total_steps = total_steps
        self.current_step = 0
        self.show_details = show_details
        self.start_time = time.time()
        self.step_times: List[float] = []
        self.current_operation = ""
        self.detailed_info: Dict[str, Any] = {}
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.spinner_index = 0
        self.spinner_thread: Optional[threading.Thread] = None
        self.spinning = False
        self.show_detailed = False
        
        # Set up interrupt handler for detailed view
        signal.signal(signal.SIGINT, self._interrupt_handler)
    
    def start_step(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """Start a new step with operation description"""
        self.current_step += 1
        self.current_operation = operation
        self.detailed_info = details or {}
        step_start_time = time.time()
        self.step_times.append(step_start_time)
        
        if self.show_details:
            elapsed = step_start_time - self.start_time
            progress_bar = self._get_progress_bar()
            
            print(f"\n{progress_bar}")
            print(f"📍 Step {self.current_step}/{self.total_steps}: {operation}")
            print(f"⏱️  Elapsed: {self._format_time(elapsed)}")
            
            if details:
                for key, value in details.items():
                    print(f"   📋 {key}: {value}")
    
    def update_details(self, key: str, value: Any):
        """Update detailed information for current step"""
        self.detailed_info[key] = value
        if self.show_details and self.show_detailed:
            print(f"   📋 {key}: {value}")
    
    def start_spinner(self, message: str = "Processing..."):
        """Start a spinner for long-running operations"""
        if self.show_details:
            print(f"\n🔄 {message}")
            self.spinning = True
            self.spinner_thread = threading.Thread(target=self._spinner_animation)
            self.spinner_thread.daemon = True
            self.spinner_thread.start()
    
    def stop_spinner(self, result_message: str = "Complete"):
        """Stop the spinner and show result"""
        self.spinning = False
        if self.spinner_thread:
            self.spinner_thread.join(timeout=0.1)
        
        if self.show_details:
            print(f"\r✅ {result_message}                    ")
    
    def complete_step(self, result: str = "✅ Complete"):
        """Complete the current step"""
        if self.step_times:
            step_duration = time.time() - self.step_times[-1]
            total_elapsed = time.time() - self.start_time
            
            if self.show_details:
                print(f"   ⏱️  Step time: {self._format_time(step_duration)}")
                print(f"   🎯 {result}")
                
                # Show ETA if we have multiple steps
                if self.total_steps > 1 and self.current_step < self.total_steps:
                    avg_step_time = total_elapsed / self.current_step
                    remaining_steps = self.total_steps - self.current_step
                    eta = remaining_steps * avg_step_time
                    print(f"   📈 ETA: {self._format_time(eta)}")
    
    def show_summary(self):
        """Show final summary"""
        total_time = time.time() - self.start_time
        
        if self.show_details:
            print(f"\n{'='*60}")
            print(f"📊 Workflow Summary")
            print(f"{'='*60}")
            print(f"Total Steps: {self.current_step}/{self.total_steps}")
            print(f"Total Time: {self._format_time(total_time)}")
            print(f"Average Step Time: {self._format_time(total_time / max(self.current_step, 1))}")
            print(f"✅ Workflow completed at {datetime.now().strftime('%H:%M:%S')}")
            print()
    
    def _get_progress_bar(self, width: int = 40) -> str:
        """Generate a visual progress bar"""
        if self.total_steps == 0:
            return "🔄 Processing..."
        
        progress = self.current_step / self.total_steps
        filled = int(width * progress)
        bar = "█" * filled + "░" * (width - filled)
        percentage = progress * 100
        
        return f"[{bar}] {percentage:5.1f}% ({self.current_step}/{self.total_steps})"
    
    def _format_time(self, seconds: float) -> str:
        """Format time duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.1f}s"
    
    def _spinner_animation(self):
        """Run spinner animation in background thread"""
        while self.spinning:
            char = self.spinner_chars[self.spinner_index % len(self.spinner_chars)]
            print(f"\r{char} Processing...", end="", flush=True)
            self.spinner_index += 1
            time.sleep(0.1)
    
    def _interrupt_handler(self, signum, frame):
        """Handle Ctrl+C to show detailed progress"""
        self.show_detailed = not self.show_detailed
        
        if self.show_detailed:
            print(f"\n\n{'='*60}")
            print(f"🔍 DETAILED PROGRESS VIEW")
            print(f"{'='*60}")
            print(f"Current Operation: {self.current_operation}")
            print(f"Step: {self.current_step}/{self.total_steps}")
            
            elapsed = time.time() - self.start_time
            print(f"Total Elapsed: {self._format_time(elapsed)}")
            
            if self.step_times:
                current_step_time = time.time() - self.step_times[-1]
                print(f"Current Step Time: {self._format_time(current_step_time)}")
            
            print(f"\nDetailed Information:")
            for key, value in self.detailed_info.items():
                print(f"  • {key}: {value}")
            
            print(f"\n💡 Press Ctrl+C again to hide detailed view")
            print(f"{'='*60}\n")
        else:
            print(f"\n📋 Detailed view hidden. Press Ctrl+C to show again.\n")


class AIProgressTracker:
    """Specialized progress tracker for AI operations"""
    
    def __init__(self, operation_name: str, show_details: bool = True):
        self.operation_name = operation_name
        self.show_details = show_details
        self.start_time = time.time()
        self.requests_made = 0
        self.tokens_used = 0
        self.current_prompt = ""
        self.spinner_active = False
        
    def start_ai_request(self, prompt_preview: str = "", max_length: int = 100):
        """Start tracking an AI request"""
        self.requests_made += 1
        self.current_prompt = prompt_preview[:max_length] + "..." if len(prompt_preview) > max_length else prompt_preview
        
        if self.show_details:
            print(f"\n🤖 AI Request #{self.requests_made} - {self.operation_name}")
            print(f"📝 Prompt: {self.current_prompt}")
            print(f"⏳ Waiting for response...", end="", flush=True)
            
        self._start_spinner()
    
    def complete_ai_request(self, response_preview: str = "", tokens: int = 0):
        """Complete tracking of an AI request"""
        self._stop_spinner()
        self.tokens_used += tokens
        
        elapsed = time.time() - self.start_time
        
        if self.show_details:
            print(f"\r✅ Response received in {elapsed:.1f}s")
            if response_preview:
                preview = response_preview[:100] + "..." if len(response_preview) > 100 else response_preview
                print(f"💬 Response: {preview}")
            if tokens > 0:
                print(f"🔢 Tokens used: {tokens}")
            print(f"📊 Total requests: {self.requests_made}, Total tokens: {self.tokens_used}")
    
    def _start_spinner(self):
        """Start AI processing spinner"""
        self.spinner_active = True
        threading.Thread(target=self._ai_spinner, daemon=True).start()
    
    def _stop_spinner(self):
        """Stop AI processing spinner"""
        self.spinner_active = False
    
    def _ai_spinner(self):
        """AI-specific spinner animation"""
        ai_chars = "🧠💭🤔💡🔍✨"
        index = 0
        while self.spinner_active:
            char = ai_chars[index % len(ai_chars)]
            print(f"\r{char} Claude is thinking...", end="", flush=True)
            index += 1
            time.sleep(0.3)


def create_workflow_progress(total_steps: int, verbose: bool = True) -> ProgressTracker:
    """Create a workflow progress tracker"""
    return ProgressTracker(total_steps=total_steps, show_details=verbose)


def create_ai_progress(operation_name: str, verbose: bool = True) -> AIProgressTracker:
    """Create an AI operation progress tracker"""
    return AIProgressTracker(operation_name=operation_name, show_details=verbose)