#!/usr/bin/env python3
"""Easy command registration helper for grace modules.

This file provides a simple way for modules to register themselves
with the grace CLI system.

Usage:
    1. Import this module in your module's setup script
    2. Call register_module() with your module details
    3. The command will be automatically available via 'grace <command>'

Example:
    from grace.scripts.register_commands import register_module

    register_module(
        name="research",
        description="Deep research with AI analysis",
        module_path="modules/DeepResearchCLI",
        entry_point="grace-research",
        aliases=["r", "dr"]
    )
"""

import sys
from pathlib import Path
from typing import List, Optional

# Add grace root to path
grace_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(grace_root / "scripts"))

from grace_registry import GraceRegistry


def register_module(
    name: str,
    description: str,
    module_path: str,
    entry_point: str,
    aliases: Optional[List[str]] = None,
    main: Optional[str] = None,
    examples: Optional[List[str]] = None,
    verbose: bool = True
):
    """Register a module with the grace CLI.

    Args:
        name: Command name (e.g., "research")
        description: Command description
        module_path: Relative path from grace root (e.g., "modules/DeepResearchCLI")
        entry_point: Command entry point (e.g., "grace-research")
        aliases: Optional list of command aliases
        main: Default subcommand to use when no args provided
        examples: Usage examples
        verbose: Print status messages
    """
    try:
        registry = GraceRegistry()
        registry.register_command(
            name=name,
            description=description,
            module_path=module_path,
            entry_point=entry_point,
            aliases=aliases,
            main=main,
            examples=examples
        )

        if verbose:
            print(f"✅ Registered command: {name}")
            if aliases:
                print(f"   Aliases: {', '.join(aliases)}")

        return True

    except Exception as e:
        if verbose:
            print(f"❌ Failed to register command '{name}': {e}")
        return False


def unregister_module(name: str, verbose: bool = True):
    """Unregister a module from the grace CLI.

    Args:
        name: Command name to unregister
        verbose: Print status messages
    """
    try:
        registry = GraceRegistry()
        registry.unregister_command(name)

        if verbose:
            print(f"✅ Unregistered command: {name}")

        return True

    except Exception as e:
        if verbose:
            print(f"❌ Failed to unregister command '{name}': {e}")
        return False


def is_registered(name: str) -> bool:
    """Check if a command is registered.

    Args:
        name: Command name to check

    Returns:
        True if command is registered, False otherwise
    """
    registry = GraceRegistry()
    return registry.get_command(name) is not None


# Load commands from commands.json
def load_commands_from_config():
    """Load command definitions from commands.json."""
    import json

    config_file = grace_root / "commands.json"

    if not config_file.exists():
        print(f"⚠️  Warning: {config_file} not found")
        return []

    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
            return data.get('commands', [])
    except Exception as e:
        print(f"❌ Error loading commands.json: {e}")
        return []


# Load modules from commands.json
BUILTIN_MODULES = load_commands_from_config()


def register_all_builtin_modules(verbose: bool = True):
    """Register all built-in grace modules.

    Args:
        verbose: Print status messages

    Returns:
        Number of successfully registered modules
    """
    success_count = 0

    if verbose:
        print("\n📦 Registering built-in grace modules...")

    for module in BUILTIN_MODULES:
        if register_module(**module, verbose=verbose):
            success_count += 1

    if verbose:
        print(f"\n✅ Registered {success_count}/{len(BUILTIN_MODULES)} modules")

    return success_count


if __name__ == "__main__":
    # When run directly, register all built-in modules
    import argparse

    parser = argparse.ArgumentParser(description="Register grace module commands")
    parser.add_argument(
        "--unregister",
        metavar="NAME",
        help="Unregister a command"
    )
    parser.add_argument(
        "--check",
        metavar="NAME",
        help="Check if a command is registered"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output messages"
    )

    args = parser.parse_args()

    if args.unregister:
        unregister_module(args.unregister, verbose=not args.quiet)
    elif args.check:
        if is_registered(args.check):
            print(f"✅ Command '{args.check}' is registered")
            sys.exit(0)
        else:
            print(f"❌ Command '{args.check}' is not registered")
            sys.exit(1)
    else:
        # Register all built-in modules
        register_all_builtin_modules(verbose=not args.quiet)
