#!/usr/bin/env python3
"""Grace CLI Command Registry - Central registry for all grace module commands."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict


@dataclass
class CommandInfo:
    """Information about a registered command."""
    name: str
    description: str
    module_path: str
    entry_point: str
    aliases: List[str] = None
    main: str = None  # Default subcommand to use when no args provided
    examples: List[str] = None  # Usage examples
    subcommands: List[str] = None  # Valid subcommands for this command

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.examples is None:
            self.examples = []
        if self.subcommands is None:
            self.subcommands = []


class GraceRegistry:
    """Central registry for all grace commands.

    This registry allows modules to register their commands so they can be
    executed via the global 'grace' command.

    Usage in a module:
        from grace_registry import GraceRegistry

        registry = GraceRegistry()
        registry.register_command(
            name="research",
            description="Deep research with AI analysis",
            module_path="modules/DeepResearchCLI",
            entry_point="grace-research",
            aliases=["r", "deepresearch"]
        )
    """

    def __init__(self, registry_file: Optional[Path] = None):
        """Initialize the registry.

        Args:
            registry_file: Path to the registry file. If None, uses default location.
        """
        # Grace root is parent of scripts directory
        self.grace_root = Path(__file__).parent.parent.absolute()

        if registry_file is None:
            self.registry_file = self.grace_root / ".grace_registry.json"
        else:
            self.registry_file = registry_file

        self.commands: Dict[str, CommandInfo] = {}
        self._load_registry()

    def _load_registry(self):
        """Load the registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    self.commands = {
                        name: CommandInfo(**cmd_data)
                        for name, cmd_data in data.items()
                    }
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Could not load registry: {e}")
                self.commands = {}
        else:
            # Initialize with empty registry
            self.commands = {}
            self._save_registry()

    def _save_registry(self):
        """Save the registry to disk."""
        data = {name: asdict(cmd) for name, cmd in self.commands.items()}

        # Ensure directory exists
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2)

    def register_command(
        self,
        name: str,
        description: str,
        module_path: str,
        entry_point: str,
        aliases: Optional[List[str]] = None,
        main: Optional[str] = None,
        examples: Optional[List[str]] = None,
        subcommands: Optional[List[str]] = None
    ):
        """Register a new command.

        Args:
            name: Command name (e.g., "research")
            description: Command description
            module_path: Relative path to module from grace root
            entry_point: Command entry point (executable name or python module)
            aliases: List of command aliases
            main: Default subcommand to use when no args provided
            examples: Usage examples
            subcommands: Valid subcommands for this command
        """
        cmd_info = CommandInfo(
            name=name,
            description=description,
            module_path=module_path,
            entry_point=entry_point,
            aliases=aliases or [],
            main=main,
            examples=examples or [],
            subcommands=subcommands or []
        )

        self.commands[name] = cmd_info

        # Register aliases
        if aliases:
            for alias in aliases:
                self.commands[alias] = cmd_info

        self._save_registry()

    def unregister_command(self, name: str):
        """Unregister a command and its aliases.

        Args:
            name: Command name to unregister
        """
        if name in self.commands:
            cmd_info = self.commands[name]

            # Remove the main command
            del self.commands[name]

            # Remove all aliases
            for alias in cmd_info.aliases:
                if alias in self.commands:
                    del self.commands[alias]

            self._save_registry()

    def get_command(self, name: str) -> Optional[CommandInfo]:
        """Get command info by name or alias.

        Args:
            name: Command name or alias

        Returns:
            CommandInfo if found, None otherwise
        """
        return self.commands.get(name)

    def list_commands(self) -> List[CommandInfo]:
        """List all registered commands (excluding aliases).

        Returns:
            List of CommandInfo objects
        """
        # Return unique commands (filter out aliases)
        seen = set()
        unique_commands = []

        for cmd_info in self.commands.values():
            if cmd_info.name not in seen:
                seen.add(cmd_info.name)
                unique_commands.append(cmd_info)

        return unique_commands

    def clear_registry(self):
        """Clear all registered commands."""
        self.commands = {}
        self._save_registry()


if __name__ == "__main__":
    # Command-line interface for managing the registry
    import sys

    if len(sys.argv) < 2:
        print("Usage: python grace_registry.py [list|clear]")
        sys.exit(1)

    command = sys.argv[1]
    registry = GraceRegistry()

    if command == "list":
        print("\n📋 Registered Commands:")
        for cmd in registry.list_commands():
            print(f"\n  {cmd.name}")
            print(f"    Description: {cmd.description}")
            print(f"    Module: {cmd.module_path}")
            print(f"    Entry point: {cmd.entry_point}")
            if cmd.aliases:
                print(f"    Aliases: {', '.join(cmd.aliases)}")
    elif command == "clear":
        registry.clear_registry()
        print("✅ Registry cleared")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
