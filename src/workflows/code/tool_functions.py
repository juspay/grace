import re
import json
import subprocess
from pathlib import Path
from typing import Dict
from .tools import *

background_processes: Dict[str, subprocess.Popen] = {}

def agent(input: AgentInput):
    """Create a specialized agent for a specific task"""
    return f"Agent for {input.subagent_type}: {input.description[:100]}..."

def bash(input: BashInput):
    """Execute a bash command"""
    try:
        if isinstance(input, dict):
            command = input.get('command')
            timeout = input.get('timeout')
            run_in_background = input.get('run_in_background', False)
            dangerously_disable_sandbox = input.get('dangerouslyDisableSandbox', False)
        else:
            command = input.command
            timeout = input.timeout
            run_in_background = input.run_in_background
            dangerously_disable_sandbox = input.dangerouslyDisableSandbox
        
        kwargs = {
            'shell': True,
            'capture_output': True,
            'text': True,
            'timeout': timeout / 1000 if timeout else None
        }
        
        result = subprocess.run(command, **kwargs)
        
        if run_in_background:
            bash_id = f"bash_{len(background_processes)}"
            background_processes[bash_id] = result
            return {"bash_id": bash_id, "started": True}
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out", "timeout": timeout}
    except Exception as e:
        return {"error": str(e)}

def bash_output(input: BashOutputInput):
    """Get output from a background bash process"""
    if input.bash_id not in background_processes:
        return {"error": f"Background process {input.bash_id} not found"}
    
    process = background_processes[input.bash_id]
    if isinstance(process, subprocess.CompletedProcess):
        output = {
            "stdout": process.stdout,
            "stderr": process.stderr,
            "returncode": process.returncode
        }
        if input.filter:
            lines = output["stdout"].split('\n')
            filtered_lines = [line for line in lines if re.search(input.filter, line)]
            output["stdout"] = '\n'.join(filtered_lines)
        return output
    else:
        return {"error": "Process still running"}

def exit_plan_mode(input: ExitPlanModeInput):
    """Exit plan mode and execute the plan"""
    return {"plan_accepted": True, "plan": input.plan}

def file_read(input: FileReadInput):
    """Read contents of a file"""
    try:
        path = Path(input.file_path)
        if not path.exists():
            return {"error": f"File not found: {input.file_path}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start = input.offset or 0
        end = start + input.limit if input.limit else len(lines)
        
        content_lines = lines[start:end]
        content = ''.join(content_lines)
        
        return {
            "content": content,
            "total_lines": len(lines),
            "lines_read": len(content_lines),
            "file_path": str(path.absolute())
        }
    except Exception as e:
        return {"error": str(e)}

def file_write(input: FileWriteInput):
    """Write content to a file"""
    try:
        if isinstance(input, dict):
            file_path = input.get('file_path')
            content = input.get('content')
        else:
            file_path = input.file_path
            content = input.content
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "file_path": str(path.absolute()),
            "bytes_written": len(content.encode('utf-8'))
        }
    except Exception as e:
        return {"error": str(e)}

def file_edit(input: FileEditInput):
    """Edit a file by replacing old_string with new_string"""
    try:
        path = Path(input.file_path)
        if not path.exists():
            return {"error": f"File not found: {input.file_path}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if input.replace_all:
            new_content = content.replace(input.old_string, input.new_string)
        else:
            new_content = content.replace(input.old_string, input.new_string, 1)
        
        if new_content == content:
            return {"error": "Old string not found in file"}
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "success": True,
            "replacements": new_content.count(input.new_string),
            "file_path": str(path.absolute())
        }
    except Exception as e:
        return {"error": str(e)}

def glob(input: GlobInput):
    """Find files matching a pattern"""
    try:
        search_path = Path(input.path) if input.path else Path.cwd()
        pattern = input.pattern
        
        matches = list(search_path.rglob(pattern))
        
        result_files = []
        for match in matches:
            if match.is_file():
                result_files.append({
                    "path": str(match),
                    "relative_path": str(match.relative_to(search_path)),
                    "size": match.stat().st_size,
                    "modified": match.stat().st_mtime
                })
        
        return {
            "pattern": pattern,
            "search_path": str(search_path),
            "matches": result_files,
            "count": len(result_files)
        }
    except Exception as e:
        return {"error": str(e)}

def grep(input: GrepInput):
    """Search for patterns in files"""
    try:
        search_path = Path(input.path) if input.path else Path.cwd()
        
        flags = re.IGNORECASE if input.i else 0
        if input.multiline:
            flags |= re.MULTILINE
        
        pattern = re.compile(input.pattern, flags)
        results = []
        
        if input.glob:
            files = list(search_path.rglob(input.glob))
        else:
            files = list(search_path.rglob('*'))
        
        for file_path in files:
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if pattern.search(line):
                            matches = []
                            for match in pattern.finditer(line):
                                matches.append({
                                    "start": match.start(),
                                    "end": match.end(),
                                    "matched_text": match.group()
                                })
                            
                            result_line = {
                                "file": str(file_path),
                                "line_number": line_num,
                                "line_content": line.rstrip(),
                                "matches": matches
                            }
                            results.append(result_line)
                except Exception:
                    continue  # Skip files that can't be read
        
        if input.head_limit:
            results = results[:input.head_limit]
        
        return {
            "pattern": input.pattern,
            "search_path": str(search_path),
            "matches": results,
            "count": len(results)
        }
    except Exception as e:
        return {"error": str(e)}

def kill_shell(input: KillShellInput):
    """Kill a background shell process"""
    try:
        if input.shell_id in background_processes:
            del background_processes[input.shell_id]
            return {"success": True, "killed": input.shell_id}
        else:
            return {"error": f"Process {input.shell_id} not found"}
    except Exception as e:
        return {"error": str(e)}

def list_mcp_resources(input: ListMcpResourcesInput):
    """List available MCP resources"""
    # Placeholder implementation
    return {
        "resources": [],
        "server": input.server,
        "message": "MCP functionality not yet implemented"
    }

def mcp(input: McpInput):
    """Execute MCP command"""
    # Placeholder implementation
    return {
        "message": "MCP functionality not yet implemented"
    }

def notebook_edit(input: NotebookEditInput):
    """Edit a Jupyter notebook"""
    try:
        import json
        
        path = Path(input.notebook_path)
        if not path.exists():
            return {"error": f"Notebook not found: {input.notebook_path}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        if input.edit_mode == "replace" and input.cell_id:
            for i, cell in enumerate(notebook['cells']):
                if cell.get('id') == input.cell_id:
                    notebook['cells'][i]['source'] = input.new_source
                    if input.cell_type:
                        notebook['cells'][i]['cell_type'] = input.cell_type
                    break
        elif input.edit_mode == "insert":
            new_cell = {
                "cell_type": input.cell_type or "code",
                "source": input.new_source,
                "metadata": {},
                "outputs": []
            }
            if input.cell_id:
                for i, cell in enumerate(notebook['cells']):
                    if cell.get('id') == input.cell_id:
                        notebook['cells'].insert(i + 1, new_cell)
                        break
            else:
                notebook['cells'].append(new_cell)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2)
        
        return {
            "success": True,
            "notebook_path": str(path.absolute()),
            "total_cells": len(notebook['cells'])
        }
    except ImportError:
        return {"error": "json module not available"}
    except Exception as e:
        return {"error": str(e)}

def read_mcp_resource(input: ReadMcpResourceInput):
    """Read an MCP resource"""
    # Placeholder implementation
    return {
        "message": "MCP functionality not yet implemented",
        "server": input.server,
        "uri": input.uri
    }

def todo_write(input: TodoWriteInput):
    """Write todo list"""
    try:
        todo_text = "# TODO List\n\n"
        for i, todo in enumerate(input.todos, 1):
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄", 
                "completed": "✅"
            }.get(todo.status, "📝")
            
            todo_text += f"{i}. {status_emoji} {todo.content}\n"
        
        todo_file = Path.cwd() / "todo.md"
        with open(todo_file, 'w', encoding='utf-8') as f:
            f.write(todo_text)
        
        return {
            "success": True,
            "file_path": str(todo_file),
            "total_todos": len(input.todos),
            "completed": sum(1 for todo in input.todos if todo.status == "completed")
        }
    except Exception as e:
        return {"error": str(e)}

def web_fetch(input: WebFetchInput):
    """Fetch content from a URL using BrowserService"""
    import asyncio
    from src.tools.browser.BrowserService import BrowserService
    
    async def fetch_with_browser():
        browser_service = BrowserService()
        try:
            await browser_service.start()
            
            # Navigate to the URL
            success = await browser_service.navigate_to(input.url)
            if not success:
                return {"error": f"Failed to navigate to {input.url}"}
            
            # Wait for page to load
            await browser_service.wait_for_load()
            
            # Get page content
            content = await browser_service.get_markdown_content()
            
            # Get page info for status information
            page_info = await browser_service.get_page_info()
            
            # Truncate content if too long
            # max_content_length = 10000
            # if len(content) > max_content_length:
            #     truncated_content = content[:max_content_length]
            #     message = f"Content truncated to {max_content_length} characters"
            # else:
            #     truncated_content = content
            #     message = "Content loaded successfully"
            
            return {
                "url": input.url,
                "status_code": 200,  # BrowserService doesn't give status codes, assume success if navigation worked
                "content_length": len(content),
                "content": content,
                "message": "content loaded successfully",
                "page_title": page_info.get("title", ""),
                "prompt": input.prompt  # Include the prompt in response for context
            }
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            await browser_service.close()
    
    try:
        # Run the async function in the current event loop or create a new one
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, we need to run it in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, fetch_with_browser())
                return future.result()
        except RuntimeError:
            # No event loop running, we can use asyncio.run directly
            return asyncio.run(fetch_with_browser())
            
    except Exception as e:
        return {"error": f"Browser service error: {str(e)}"}

def web_search(input: WebSearchInput):
    """Perform web search"""
    return {
        "query": input.query,
        "results": [],
        "message": "Web search functionality not yet implemented"
    }

def ask_user_question(input: AskUserQuestionInput):
    """Ask the user a question"""
    return {
        "questions": [
            {
                "question": q.question,
                "header": q.header,
                "options": [
                    {"label": opt.label, "description": opt.description}
                    for opt in q.options
                ],
                "multi_select": q.multiSelect
            }
            for q in input.questions
        ],
        "message": "Please review these questions and provide answers"
    }
