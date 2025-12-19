#!/usr/bin/env python3
"""
Grace Test Workflow - Integrated test execution and analysis
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from .ai.ai_service import AIService


class GraceTestWorkflow:
    """Integrated workflow for testing and analyzing payment connectors"""

    def __init__(self):
        self.ai_service = AIService()
        self.current_dir = Path.cwd()

    def find_test_directory(self) -> Path:
        """Find where the test files are located"""
        test_dirs = [
            self.current_dir / "src" / "grpc-tester",
            self.current_dir,
            self.current_dir / "grpc-tester",
        ]

        for td in test_dirs:
            if (td / "run_grpc_tests.py").exists():
                return td

        raise FileNotFoundError("Cannot find run_grpc_tests.py")

    def find_connector_code(self, connector_name: str) -> List[Path]:
        """Find connector implementation files"""
        connector_files = []

        search_dirs = [
            self.current_dir,
            self.current_dir.parent,
            self.current_dir.parent / "connector-service",
            Path.home() / "workspace" / "hyperswitch"
        ]

        for search_dir in search_dirs:
            patterns = [
                f"**/*{connector_name}*.rs",
                f"**/*{connector_name}*.py",
                f"**/connectors/{connector_name}/**/*"
            ]

            for pattern in patterns:
                connector_files.extend(search_dir.glob(pattern))

        return [f for f in connector_files if f.is_file() and not f.is_symlink()]

    async def generate_execute_tests(self, env_file: str = ".env.grpc", test_set: str = None) -> Dict[str, Any]:
        """Generate and execute gRPC tests"""
        test_dir = self.find_test_directory()

        # Check if env file exists
        # If env_file is relative, check from test_dir
        if not Path(env_file).is_absolute():
            env_path = test_dir / env_file
            if not env_path.exists():
                # Also check parent directory
                parent_env = test_dir.parent / env_file
                if parent_env.exists():
                    env_path = parent_env
                else:
                    raise FileNotFoundError(f"Environment file not found: {env_file}. Searched in: {test_dir} and {test_dir.parent}")
        else:
            env_path = Path(env_file)
            if not env_path.exists():
                raise FileNotFoundError(f"Environment file not found: {env_file}")

        # Build command
        cmd = [sys.executable, "run_grpc_tests.py", "--env", str(env_path)]
        if test_set:
            cmd.extend(["--test-set", test_set])

        # Execute tests
        result = subprocess.run(cmd, cwd=test_dir, capture_output=True, text=True)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Find existing result files
        result_files = []
        potential_dirs = [
            Path("./output/grpc-results"),
            test_dir / "output" / "grpc-results",
            test_dir / "grpc_test_results",
            test_dir / "output"
        ]

        for directory in potential_dirs:
            if directory.exists():
                result_files.extend(directory.glob("test_results_*.json"))
                result_files.extend(directory.glob("grpc_test_log_*.txt"))

        # Sort by modification time
        result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "result_files": result_files[:5],
            "test_dir": str(test_dir)
        }

    async def analyze_test_results(self, result_files: List[Path], connector_name: str = None) -> Dict[str, Any]:
        """Analyze test results with Claude"""

        analysis_prompt = """You are analyzing gRPC test results for a payment connector. Please provide:

1. **Test Summary**: What was tested and overall success rate
2. **Critical Issues**: Any blocking errors found
3. **Root Causes**: Why tests failed (authentication, configuration, etc.)
4. **Specific Fixes**: Exact code/parameter changes needed
5. **Connector-Specific Insights**: Focus on {} implementation patterns

Be actionable and specific."""

        analyses = []

        for result_file in result_files[:3]:
            try:
                with open(result_file, 'r') as f:
                    content = f.read()

                if len(content) > 80000:
                    content = content[:40000] + "\n\n...[TRUNCATED]...\n\n" + content[-40000:]

                messages = [
                    {"role": "system", "content": analysis_prompt.format(connector_name or "unknown")},
                    {"role": "user", "content": f"Analyzing: {result_file.name}\n\n{content}"}
                ]

                response, success, error = self.ai_service.generate(messages)
                if not success:
                    raise Exception(f"AI generation failed: {error}")
                analyses.append({
                    "file": str(result_file),
                    "analysis": response
                })

            except Exception as e:
                analyses.append({
                    "file": str(result_file),
                    "error": str(e)
                })

        return analyses

    async def analyze_connector_code(self, connector_name: str, code_files: List[Path]) -> Dict[str, Any]:
        """Analyze and potentially fix connector implementation code"""
        if not code_files:
            return {"error": f"No code files found for connector: {connector_name}"}

        code_files_to_fix = []
        total_content_size = 0

        # Find relevant files .rs files for the connector
        for code_file in code_files:
            if connector_name.lower() in str(code_file).lower() and str(code_file).endswith('.rs'):
                if len(code_file.read_text(encoding='utf-8', errors='ignore')) < 50000:
                    code_files_to_fix.append(code_file)

        if not code_files_to_fix:
            return {"error": f"No suitable .rs files found for connector: {connector_name}"}

        # Ask Claude to analyze and provide fixes
        fix_prompt = """You are fixing payment connector code for {} after test failures.

Based on the test results showing "Invalid connector: Matching variant not found", you need to:

1. **IDENTIFY THE PROBLEM**: Look for issues in:
   - Connector name/identifier matching
   - gRPC service implementation
   - Error handling
   - Module definitions

2. **PROVIDE FIXES**: For each issue found:
   - Show exact code to replace (with line numbers if possible)
   - Show the corrected code
   - Explain why this fix works

3. **FORMAT YOUR RESPONSE**:
   For each file that needs fixing, output in this format:

   ```diff
   // File: path/to/file.rs
   // Lines X-Y: Description of change
   - old_code
   + new_code
   ```

   Use proper Rust syntax and maintain consistency with existing code style.

IMPORTANT: Look specifically for:
- How connector variants are defined/matched
- enum or struct definitions that should include "{}"
- Service registration or routing issues
- Any hardcoded connector names that don't match

Focus on making the connector recognizable to the gRPC server as "{}". """

        fixes = []

        for code_file in code_files_to_fix[:5]:  # Limit to 5 files
            try:
                content = code_file.read_text(encoding='utf-8', errors='ignore')

                messages = [
                    {"role": "system", "content": fix_prompt.format(connector_name, connector_name)},
                    {"role": "user", "content": f"File to analyze and fix: {code_file}\n\n```rust\n{content}\n```\n\n\nThe gRPC server error was: 'Invalid connector: Matching variant not found'.\n\nPlease provide specific code fixes to resolve this."}
                ]

                response, success, error = self.ai_service.generate(messages)
                if not success:
                    raise Exception(f"AI generation failed: {error}")

                # Try to apply the fixes
                if "```diff" in response:
                    applied_fixes = await self.apply_fixes(code_file, response)
                    fixes.append({
                        "file": str(code_file),
                        "fixes": response,
                        "applied": applied_fixes,
                        "success": len(applied_fixes) > 0
                    })
                else:
                    fixes.append({
                        "file": str(code_file),
                        "analysis": response,
                        "applied": [],
                        "success": False
                    })

            except Exception as e:
                fixes.append({
                    "file": str(code_file),
                    "error": str(e),
                    "applied": [],
                    "success": False
                })

        return fixes

    async def apply_fixes(self, file_path: Path, diff_response: str) -> List[Dict]:
        """Apply code fixes from Claude's diff response"""
        applied = []

        try:
            # Read current file content
            lines = file_path.read_text(encoding='utf-8').split('\n')

            # Extract and apply diffs
            import re

            # Find all diff blocks
            diff_blocks = re.findall(r'```diff\n(.*?)\n```', diff_response, re.DOTALL)

            for diff_block in diff_blocks:
                lines_patched = 0

                # Simple diff parsing (basic implementation)
                for line in diff_block.split('\n'):
                    if line.startswith('- '):
                        # This is a removal - marked for replacement
                        lines_patched += 1
                    elif line.startswith('+ '):
                        # This is an addition
                        lines_patched += 1

                if lines_patched > 0:
                    # For now, just log that we would apply the fix
                    # In a real implementation, you'd parse and apply the actual changes
                    applied.append({
                        "file": str(file_path),
                        "status": "Would apply fixes",
                        "lines_affected": lines_patched
                    })

        except Exception as e:
            applied.append({
                "file": str(file_path),
                "error": f"Failed to apply fixes: {str(e)}"
            })

        return applied

    def get_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        lang_map = {
            '.rs': 'rust',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go'
        }
        return lang_map.get(ext, 'text')

    async def run_full_workflow(self, connector_name: str, env_file: str = ".env.grpc",
                               test_set: str = None, output_dir: str = None) -> Dict[str, Any]:
        """Run the complete workflow: test execution + analysis"""

        results = {
            "connector_name": connector_name,
            "timestamp": datetime.now().isoformat(),
            "workflow_steps": {}
        }

        # Step 1: Generate and execute tests
        print("🚀 Step 1: Running gRPC tests...")
        test_results = await self.generate_execute_tests(env_file, test_set)
        results["workflow_steps"]["test_execution"] = test_results

        # Step 2: Analyze test results
        print("🤖 Step 2: Analyzing test results with Claude...")
        if test_results["result_files"]:
            test_analysis = await self.analyze_test_results(test_results["result_files"], connector_name)
            results["workflow_steps"]["test_analysis"] = test_analysis
        else:
            results["workflow_steps"]["test_analysis"] = {"error": "No test result files found"}

        # Step 3: Find and analyze connector code
        print("🔍 Step 3: Analyzing connector implementation...")
        code_files = self.find_connector_code(connector_name)

        if code_files:
            print(f"Found {len(code_files)} code files for {connector_name}")
            code_analysis = await self.analyze_connector_code(connector_name, code_files)
            results["workflow_steps"]["code_analysis"] = code_analysis
        else:
            results["workflow_steps"]["code_analysis"] = {"info": f"No code files found for {connector_name}"}

        # Step 4: Generate summary report
        print("📋 Step 4: Generating summary report...")
        summary = await self.generate_summary_report(results)
        results["workflow_steps"]["summary"] = summary

        # Save results
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path("./output/grpc-results")

        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        json_file = output_path / f"grace_test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # Save markdown report
        md_file = output_path / f"grace_test_report_{timestamp}.md"
        with open(md_file, 'w') as f:
            f.write(summary.get("report_markdown", "# No report generated"))

        results["output_files"] = {
            "json": str(json_file),
            "markdown": str(md_file)
        }

        print(f"\n✅ Workflow complete!")
        print(f"📊 Report: {md_file}")
        print(f"📄 Data: {json_file}")

        return results

    async def generate_summary_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive summary report"""

        test_exec = results["workflow_steps"].get("test_execution", {})
        test_analysis = results["workflow_steps"].get("test_analysis", [])
        code_analysis = results["workflow_steps"].get("code_analysis", [])

        report = f"""# Grace Test Analysis Report

**Connector:** {results['connector_name']}
**Timestamp:** {results['timestamp']}
**Test Status:** {'✅ PASSED' if test_exec.get('success') else '❌ FAILED'}

---

## 📊 Test Execution Summary

- **Status:** {'PASSED' if test_exec.get('success') else 'FAILED'}
- **Return Code:** {test_exec.get('return_code', 'N/A')}

"""

        return {
            "report_markdown": report,
            "test_passed": test_exec.get("success", False),
            "has_code_issues": len(code_analysis) > 0 and any("analysis" in c for c in code_analysis)
        }


async def run_workflow(args: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for workflow execution"""
    workflow = GraceTestWorkflow()

    return await workflow.run_full_workflow(
        connector_name=args.get("connector_name", "unknown"),
        env_file=args.get("env_file", ".env.grpc"),
        test_set=args.get("test_set"),
        output_dir=args.get("output_dir")
    )