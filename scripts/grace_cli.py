#!/usr/bin/env python3
"""Grace CLI - Global command executor for all grace modules."""

import sys
import subprocess
from pathlib import Path
from typing import List
import shutil

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from grace_registry import GraceRegistry


console = Console()


class GraceCLI:
    """Grace CLI application."""

    def __init__(self):
        """Initialize Grace CLI."""
        self.registry = GraceRegistry()
        self.grace_root = Path(__file__).parent.parent.absolute()

    def execute_command(self, command_name: str, args: List[str]) -> int:
        """Execute a registered command with smart subcommand handling."""
        cmd_info = self.registry.get_command(command_name)
        if not cmd_info:
            console.print(f"[red]Error:[/red] Unknown command '{command_name}'")
            console.print("\nRun [cyan]grace --help[/cyan] to see available commands")
            return 1

        entry_point = cmd_info.entry_point

        # Smart subcommand handling
        processed_args = self._process_args(args, cmd_info)

        # Handle bash/shell commands
        if entry_point in ['bash', 'sh', 'zsh']:
            script_path = processed_args[0] if processed_args else cmd_info.main
            remaining_args = processed_args[1:] if len(processed_args) > 1 else []

            if not script_path.startswith('/'):
                script_path = str(self.grace_root / script_path)

            try:
                result = subprocess.run([entry_point, script_path] + remaining_args, cwd=self.grace_root)
                return result.returncode
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
                return 1

        # Execute regular commands
        try:
            result = subprocess.run([entry_point] + processed_args)
            return result.returncode
        except FileNotFoundError:
            module_path = self.grace_root / cmd_info.module_path

            if not module_path.exists():
                console.print(f"[red]Error:[/red] Command '{entry_point}' not found")
                console.print(f"\nTo install: cd {cmd_info.module_path} && ./setup.sh")
            else:
                console.print(f"[yellow]Warning:[/yellow] Module exists but '{entry_point}' not in PATH")
                console.print(f"\nTo install: cd {cmd_info.module_path} && pip install -e .")
            return 1
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return 1

    def _process_args(self, args: List[str], cmd_info) -> List[str]:
        """Process arguments with smart subcommand handling.

        Logic:
        1. If no args and main subcommand exists, use main
        2. If first arg is a valid subcommand, pass it through
        3. If first arg is not a valid subcommand, prepend main (if exists) and pass arg as parameter

        Examples:
            grace research             -> grace-research research
            grace research config      -> grace-research config
            grace research "worldpay"  -> grace-research research "worldpay"
        """
        # No args provided
        if not args:
            if cmd_info.main:
                return [cmd_info.main]
            return []

        # Check if first arg is a valid subcommand
        first_arg = args[0]

        # If it's a valid subcommand, pass everything through
        if cmd_info.subcommands and first_arg in cmd_info.subcommands:
            return args

        # If it's not a valid subcommand and we have a main subcommand, prepend main
        if cmd_info.main and cmd_info.subcommands:
            # First arg is not a subcommand, so treat it as a parameter
            return [cmd_info.main] + args

        # No subcommands defined or no main, pass through as-is
        return args

    def _check_command_status(self, cmd) -> str:
        """Check if command is installed."""
        try:
            if shutil.which(cmd.entry_point):
                return "✅ Installed"
            module_path = self.grace_root / cmd.module_path
            return "✅ Installed" if module_path.exists() else "❌ Not installed"
        except:
            module_path = self.grace_root / cmd.module_path
            return "✅ Installed" if module_path.exists() else "❌ Not installed"

    def list_commands(self):
        """Display all registered commands."""
        commands = self.registry.list_commands()

        if not commands:
            console.print("[yellow]No commands registered.[/yellow]")
            console.print("\nRun [cyan]grace init[/cyan] to register built-in commands")
            return

        # Create table
        table = Table(title="Grace Available Commands", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="green", no_wrap=True)
        table.add_column("Aliases", style="yellow")
        table.add_column("Description", style="white")
        table.add_column("Status", style="blue")

        for cmd in commands:
            table.add_row(
                cmd.name,
                ", ".join(cmd.aliases) if cmd.aliases else "-",
                cmd.description,
                self._check_command_status(cmd)
            )

        console.print(table)

        # Show examples
        console.print("\n[cyan]Usage Examples:[/cyan]")
        shown = False
        for cmd in commands[:3]:
            if cmd.examples:
                for example in cmd.examples[:2]:
                    console.print(f"  {example}")
                    shown = True

        if not shown:
            console.print("  grace <command> --help")
            console.print("  grace info <command>")


class GraceGroup(click.Group):
    """Custom Click group that handles unknown commands."""

    def get_command(self, ctx, cmd_name):
        """Override to check registry for unknown commands."""
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        grace_cli = GraceCLI()
        if grace_cli.registry.get_command(cmd_name):
            @click.command(name=cmd_name, context_settings=dict(
                ignore_unknown_options=True,
                allow_extra_args=True,
                allow_interspersed_args=False,
            ))
            @click.pass_context
            @click.argument('subargs', nargs=-1, type=click.UNPROCESSED)
            def dynamic_command(ctx, subargs):
                """Execute registered grace command."""
                all_args = list(subargs) + ctx.args
                exit_code = grace_cli.execute_command(cmd_name, all_args)
                sys.exit(exit_code)

            return dynamic_command

        return None


@click.command(cls=GraceGroup, invoke_without_command=True)
@click.pass_context
@click.option('--version', is_flag=True, help='Show version information')
def cli(ctx, version):
    """Grace CLI - Global command executor for all grace modules.

    Run 'grace <command> --help' for command-specific help.
    """
    if version:
        console.print("[cyan]Grace CLI[/cyan] version 1.0.0")
        ctx.exit()

    if ctx.invoked_subcommand is None:
        # Show help
        click.echo(ctx.get_help())

        # Show examples from registered commands
        registry = GraceRegistry()
        commands = registry.list_commands()

        if commands:
            console.print("\n[cyan bold]Examples:[/cyan bold]")
            shown = 0
            for cmd in commands:
                if cmd.examples:
                    for example in cmd.examples[:2]:  # Max 2 examples per command
                        console.print(f"  {example}")
                        shown += 1
                        if shown >= 6:  # Max 6 total examples
                            break
                if shown >= 6:
                    break

            if shown == 0:
                console.print("  grace list        # List all commands")
                console.print("  grace init        # Initialize registry")
                console.print("  grace reload      # Reload registry from commands.json")

        console.print("")


@cli.command(name='list')
def list_commands():
    """List all registered grace commands."""
    GraceCLI().list_commands()


@cli.command(name='init')
def init_registry():
    """Initialize the command registry with built-in commands."""
    grace_root = Path(__file__).parent.parent.absolute()
    script_path = grace_root / "scripts" / "register_commands.py"
    result = subprocess.run([sys.executable, str(script_path)])

    if result.returncode == 0:
        console.print("[green]✅ Command registry initialized![/green]")
        console.print("\nRun [cyan]grace list[/cyan] to see available commands")
    else:
        console.print("[red]❌ Failed to initialize registry[/red]")


@cli.command(name='register')
@click.argument('name')
@click.argument('description')
@click.argument('module_path')
@click.argument('entry_point')
@click.option('--aliases', '-a', multiple=True, help='Command aliases')
def register_command(name, description, module_path, entry_point, aliases):
    """Register a new command manually."""
    GraceRegistry().register_command(
        name=name,
        description=description,
        module_path=module_path,
        entry_point=entry_point,
        aliases=list(aliases) if aliases else []
    )
    console.print(f"[green]✅ Command '{name}' registered successfully![/green]")


@cli.command(name='unregister')
@click.argument('name')
def unregister_command(name):
    """Unregister a command."""
    GraceRegistry().unregister_command(name)
    console.print(f"[green]✅ Command '{name}' unregistered![/green]")


@cli.command(name='clear')
@click.confirmation_option(prompt='Are you sure you want to clear all commands?')
def clear_registry():
    """Clear all registered commands."""
    GraceRegistry().clear_registry()
    console.print("[green]✅ Registry cleared![/green]")


@cli.command(name='reload')
def reload_registry():
    """Reload the command registry from commands.json."""
    grace_root = Path(__file__).parent.parent.absolute()
    script_path = grace_root / "scripts" / "register_commands.py"

    console.print("[cyan]Reloading command registry from commands.json...[/cyan]")

    # Clear existing registry
    GraceRegistry().clear_registry()

    # Reload from commands.json
    result = subprocess.run([sys.executable, str(script_path)])

    if result.returncode == 0:
        console.print("[green]✅ Command registry reloaded successfully![/green]")
        console.print("\nRun [cyan]grace list[/cyan] to see updated commands")
    else:
        console.print("[red]❌ Failed to reload registry[/red]")


@cli.command(name='info')
@click.argument('command_name')
def command_info(command_name):
    """Show detailed information about a command."""
    registry = GraceRegistry()
    cmd_info = registry.get_command(command_name)

    if not cmd_info:
        console.print(f"[red]Error:[/red] Command '{command_name}' not found")
        return

    grace_root = Path(__file__).parent.parent.absolute()
    module_path = grace_root / cmd_info.module_path

    info_text = f"""[cyan]Name:[/cyan] {cmd_info.name}
[cyan]Description:[/cyan] {cmd_info.description}
[cyan]Module Path:[/cyan] {cmd_info.module_path}
[cyan]Entry Point:[/cyan] {cmd_info.entry_point}
[cyan]Main Subcommand:[/cyan] {cmd_info.main if cmd_info.main else 'None'}
[cyan]Aliases:[/cyan] {', '.join(cmd_info.aliases) if cmd_info.aliases else 'None'}
[cyan]Subcommands:[/cyan] {', '.join(cmd_info.subcommands) if cmd_info.subcommands else 'None'}
[cyan]Status:[/cyan] {'✅ Installed' if module_path.exists() else '❌ Not installed'}
[cyan]Full Path:[/cyan] {module_path}
"""

    if cmd_info.examples:
        info_text += "\n[cyan]Examples:[/cyan]\n"
        for example in cmd_info.examples:
            info_text += f"  • {example}\n"

    console.print(Panel(info_text, title=f"Command Info: {cmd_info.name}", border_style="cyan"))


def main():
    """Main entry point for Grace CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
