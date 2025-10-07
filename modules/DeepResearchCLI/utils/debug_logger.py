"""Debug logging utility."""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, List


class DebugLogger:
    """Debug logger for tracking research operations."""

    _instance: Optional['DebugLogger'] = None

    def __init__(self):
        """Initialize debug logger."""
        self.is_debug_enabled = os.getenv('IS_DEBUG', 'false').lower() == 'true'
        self.debug_log_file = os.getenv('DEBUG_LOG_FILE', './search_query_time.log')
        self.log_stream: Optional[Any] = None

        if self.is_debug_enabled:
            self._initialize_log_stream()

    @classmethod
    def get_instance(cls) -> 'DebugLogger':
        """Get singleton instance of DebugLogger."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_log_stream(self):
        """Initialize log file stream."""
        try:
            # Ensure directory exists
            log_path = Path(self.debug_log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Open log file in append mode
            self.log_stream = open(self.debug_log_file, 'a', encoding='utf-8')

            # Add session separator
            self._write_to_stream('\n' + '=' * 80 + '\n')
            self._write_to_stream(f'DEBUG SESSION STARTED: {datetime.now().isoformat()}\n')
            self._write_to_stream('=' * 80 + '\n\n')
        except Exception as e:
            print(f'Failed to initialize debug log stream: {e}')
            self.is_debug_enabled = False

    def _write_to_stream(self, message: str):
        """Write message to log stream."""
        if self.log_stream and not self.log_stream.closed:
            self.log_stream.write(message)
            self.log_stream.flush()

    def log_search_query(self, query: str, start_time: int):
        """Log search query start."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        message = f'[{timestamp}] SEARCH_QUERY_START: "{query}"\n'
        self._write_to_stream(message)

    def log_search_result(self, query: str, results: List[Any], duration: int):
        """Log search query results."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        message = f'[{timestamp}] SEARCH_QUERY_END: "{query}" | Results: {len(results)} | Duration: {duration}ms\n'
        self._write_to_stream(message)

        for index, result in enumerate(results):
            self._write_to_stream(
                f'  {index + 1}. {result.title} ({result.url}) - Score: {result.score}\n'
            )
        self._write_to_stream('\n')

    def log_page_fetch(self, url: str, start_time: int):
        """Log page fetch start."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        message = f'[{timestamp}] PAGE_FETCH_START: {url}\n'
        self._write_to_stream(message)

    def log_page_fetch_result(
        self,
        url: str,
        success: bool,
        duration: int,
        content_length: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log page fetch result."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        status = 'SUCCESS' if success else 'FAILED'
        message = f'[{timestamp}] PAGE_FETCH_END: {url} | Status: {status} | Duration: {duration}ms'

        if success and content_length is not None:
            self._write_to_stream(f'{message} | Content: {content_length} chars\n')
        elif not success and error:
            self._write_to_stream(f'{message} | Error: {error}\n')
        else:
            self._write_to_stream(f'{message}\n')

    def log_ai_call(self, operation: str, input_length: int, start_time: int):
        """Log AI call start."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        message = f'[{timestamp}] AI_CALL_START: {operation} | Input: {input_length} chars\n'
        self._write_to_stream(message)

    def log_ai_call_result(
        self,
        operation: str,
        success: bool,
        duration: int,
        tokens_used: Optional[int] = None,
        output_length: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log AI call result."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        status = 'SUCCESS' if success else 'FAILED'
        message = f'[{timestamp}] AI_CALL_END: {operation} | Status: {status} | Duration: {duration}ms'

        if success:
            if tokens_used is not None:
                message += f' | Tokens: {tokens_used}'
            if output_length is not None:
                message += f' | Output: {output_length} chars'
        elif error:
            message += f' | Error: {error}'

        self._write_to_stream(f'{message}\n')

    def log_depth_transition(self, from_depth: int, to_depth: int, links_found: int):
        """Log depth transition."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        message = f'[{timestamp}] DEPTH_TRANSITION: {from_depth} → {to_depth} | Links: {links_found}\n'
        self._write_to_stream(message)

    def log_session_summary(
        self,
        session_id: str,
        total_pages: int,
        max_depth: int,
        duration: int,
        status: str
    ):
        """Log session summary."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        message = f'\n[{timestamp}] SESSION_SUMMARY: {session_id}\n'
        self._write_to_stream(message)
        self._write_to_stream(f'  Status: {status}\n')
        self._write_to_stream(f'  Duration: {duration}ms ({duration / 1000:.2f}s)\n')
        self._write_to_stream(f'  Pages Processed: {total_pages}\n')
        self._write_to_stream(f'  Max Depth: {max_depth}\n')
        self._write_to_stream('=' * 50 + '\n\n')

    def log_user_action(self, action: str, data: Optional[Any] = None):
        """Log user action."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        message = f'[{timestamp}] USER_ACTION: {action}'
        if data:
            message += f' | Data: {data}'
        self._write_to_stream(f'{message}\n')

    def log_error(self, context: str, error: Exception):
        """Log error with context."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        error_message = str(error)

        self._write_to_stream(f'[{timestamp}] ERROR: {context} | {error_message}\n')
        if hasattr(error, '__traceback__'):
            import traceback
            stack_trace = ''.join(traceback.format_tb(error.__traceback__))
            self._write_to_stream(f'Stack Trace:\n{stack_trace}\n')
        self._write_to_stream('\n')

    def log(self, message: str):
        """Generic log message."""
        if not self.is_debug_enabled:
            return

        timestamp = datetime.now().isoformat()
        self._write_to_stream(f'[{timestamp}] {message}\n')

    def close(self):
        """Close log stream."""
        if self.log_stream and not self.log_stream.closed:
            timestamp = datetime.now().isoformat()
            self._write_to_stream(f'\n[{timestamp}] DEBUG SESSION ENDED\n')
            self._write_to_stream('=' * 80 + '\n\n')
            self.log_stream.close()
            self.log_stream = None

    def is_enabled(self) -> bool:
        """Check if debug logging is enabled."""
        return self.is_debug_enabled

    def get_log_file_path(self) -> str:
        """Get log file path."""
        return self.debug_log_file
