#!/usr/bin/env python3
"""Standalone entry point for Deep Research CLI.

This file allows running the CLI directly without module syntax:
    python run_cli.py research "your query"

For module-based execution, use:
    python -m deep_research_cli research "your query"
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so imports work
module_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(module_dir))
os.chdir(module_dir)

def main():
    """Main entry point for the CLI."""
    # Import after path is set
    from cli import main as cli_main
    cli_main()

if __name__ == '__main__':
    main()
