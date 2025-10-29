"""
Test Execution Node
Executes generated tests headlessly or interactively
"""

import json
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from ..states.postman_state import PostmanWorkflowState, TestStructure


def execute_tests(state: PostmanWorkflowState) -> PostmanWorkflowState:
    """
    Execute generated test structures.
    
    Args:
        state: Current workflow state with generated tests
        
    Returns:
        Updated state with execution results
    """
    try:
        test_structures = state.get("test_structures", [])
        test_files = state.get("test_files", {})
        
        if not test_structures or not test_files:
            state["warnings"] = state.get("warnings", []) + ["No test structures or files found to execute"]
            return state
        
        if state.get("verbose", False):
            print(f"🚀 Executing {len(test_structures)} tests...")
        
        # Write test files to disk
        output_dir = state.get("output_dir", Path("."))
        test_dir = output_dir / "generated_tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        write_test_files(test_files, test_dir, state)
        
        # Execute tests
        execution_results = []
        if state.get("headless", False):
            execution_results = execute_headless(test_structures, test_dir, state)
        else:
            execution_results = execute_interactive(test_structures, test_dir, state)
        
        # Aggregate results
        test_results = aggregate_results(execution_results, state)
        
        state["execution_results"] = execution_results
        state["test_results"] = test_results
        
        # Update final output
        state["final_output"] = {
            "success": test_results["overall_success"],
            "collection_name": state.get("collection_info", {}).get("name", "Unknown"),
            "total_tests": len(test_structures),
            "passed_tests": test_results["passed_count"],
            "failed_tests": test_results["failed_count"],
            "success_rate": test_results["success_rate"],
            "total_time": test_results["total_time"],
            "test_directory": str(test_dir),
            "detailed_results": execution_results
        }
        
        state["success"] = test_results["overall_success"]
        
        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["execution_success"] = test_results["overall_success"]
        
        if state.get("verbose", False):
            print_execution_summary(test_results, state)
        
        return state
        
    except Exception as e:
        error_msg = f"Failed to execute tests: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        state["error"] = error_msg
        state["success"] = False
        if state.get("verbose", False):
            print(f"❌ {error_msg}")
        return state


def write_test_files(test_files: Dict[str, str], test_dir: Path, state: PostmanWorkflowState):
    """
    Write test files to disk.
    
    Args:
        test_files: Dictionary of filename -> content
        test_dir: Directory to write files to
        state: Current workflow state
    """
    if state.get("verbose", False):
        print(f"📝 Writing {len(test_files)} test files to {test_dir}")
    
    for filename, content in test_files.items():
        file_path = test_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if state.get("verbose", False):
            print(f"  ✓ {filename}")
    
    # Create __init__.py for Python module
    init_file = test_dir / "__init__.py"
    with open(init_file, 'w') as f:
        f.write("# Generated test package\\n")


def execute_headless(test_structures: List[TestStructure], test_dir: Path, state: PostmanWorkflowState) -> List[Dict[str, Any]]:
    """
    Execute tests in headless mode.
    
    Args:
        test_structures: List of test structures to execute
        test_dir: Directory containing test files
        state: Current workflow state
        
    Returns:
        List of execution results
    """
    results = []
    
    if state.get("verbose", False):
        print("🤖 Running in headless mode...")
    
    # Change to test directory
    original_cwd = Path.cwd()
    
    try:
        # Execute test runner
        runner_file = test_dir / "test_runner.py"
        if runner_file.exists():
            cmd = [sys.executable, str(runner_file), "--headless"]
            
            if state.get("verbose", False):
                print(f"⚡ Executing: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(cmd, cwd=test_dir, capture_output=True, text=True)
            end_time = time.time()
            
            # Parse results
            if result.returncode == 0:
                try:
                    # Try to parse JSON output
                    output_lines = result.stdout.strip().split('\\n')
                    json_output = None
                    
                    # Look for JSON in output
                    for line in output_lines:
                        if line.strip().startswith('{'):
                            try:
                                json_output = json.loads(line.strip())
                                break
                            except json.JSONDecodeError:
                                continue
                    
                    if json_output:
                        results.append({
                            "type": "test_runner",
                            "success": True,
                            "output": json_output,
                            "execution_time": end_time - start_time
                        })
                    else:
                        results.append({
                            "type": "test_runner",
                            "success": True,
                            "output": {"stdout": result.stdout, "stderr": result.stderr},
                            "execution_time": end_time - start_time
                        })
                        
                except Exception as e:
                    results.append({
                        "type": "test_runner",
                        "success": False,
                        "error": f"Failed to parse output: {str(e)}",
                        "raw_output": result.stdout,
                        "execution_time": end_time - start_time
                    })
            else:
                results.append({
                    "type": "test_runner", 
                    "success": False,
                    "error": f"Test runner failed with code {result.returncode}",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": end_time - start_time
                })
        else:
            # Fallback: execute individual tests
            results = execute_individual_tests_headless(test_structures, test_dir, state)
            
    finally:
        # Restore original directory
        if original_cwd != Path.cwd():
            # Only change back if we actually changed
            pass
    
    return results


def execute_interactive(test_structures: List[TestStructure], test_dir: Path, state: PostmanWorkflowState) -> List[Dict[str, Any]]:
    """
    Execute tests in interactive mode.
    
    Args:
        test_structures: List of test structures to execute
        test_dir: Directory containing test files
        state: Current workflow state
        
    Returns:
        List of execution results
    """
    results = []
    
    print("🎯 Running in interactive mode...")
    print(f"📁 Test directory: {test_dir}")
    print()
    
    # Ask user if they want to run tests now
    run_now = input("Do you want to run the tests now? (y/n): ").strip().lower()
    
    if run_now in ['y', 'yes']:
        # Execute test runner
        runner_file = test_dir / "test_runner.py"
        
        if runner_file.exists():
            print(f"⚡ Executing test runner...")
            print()
            
            cmd = [sys.executable, str(runner_file)]
            
            try:
                start_time = time.time()
                result = subprocess.run(cmd, cwd=test_dir)
                end_time = time.time()
                
                success = result.returncode == 0
                results.append({
                    "type": "test_runner",
                    "success": success,
                    "return_code": result.returncode,
                    "execution_time": end_time - start_time
                })
                
                if success:
                    print()
                    print("✅ Test execution completed successfully!")
                else:
                    print()
                    print(f"❌ Test execution failed with return code {result.returncode}")
                    
            except Exception as e:
                results.append({
                    "type": "test_runner",
                    "success": False,
                    "error": str(e)
                })
                print(f"❌ Failed to execute tests: {str(e)}")
        else:
            print("❌ Test runner file not found")
            results.append({
                "type": "test_runner",
                "success": False,
                "error": "Test runner file not found"
            })
    else:
        print("⏭️  Test execution skipped by user")
        print()
        print("To run tests later:")
        print(f"1. cd {test_dir}")
        print("2. python test_runner.py")
        print()
        print("To run in headless mode:")
        print("python test_runner.py --headless")
        
        results.append({
            "type": "user_skipped",
            "success": True,
            "message": "Test execution skipped by user choice"
        })
    
    return results


def execute_individual_tests_headless(test_structures: List[TestStructure], test_dir: Path, state: PostmanWorkflowState) -> List[Dict[str, Any]]:
    """
    Execute individual test files in headless mode as fallback.
    
    Args:
        test_structures: List of test structures to execute
        test_dir: Directory containing test files
        state: Current workflow state
        
    Returns:
        List of execution results
    """
    results = []
    
    for i, test_structure in enumerate(test_structures):
        test_file = test_dir / test_structure["test_file"]
        
        if test_file.exists():
            if state.get("verbose", False):
                print(f"  🔧 Running test {i+1}/{len(test_structures)}: {test_structure['test_name']}")
            
            cmd = [sys.executable, str(test_file)]
            
            try:
                start_time = time.time()
                result = subprocess.run(cmd, cwd=test_dir, capture_output=True, text=True, timeout=60)
                end_time = time.time()
                
                success = result.returncode == 0
                
                # Try to parse JSON output
                output_data = None
                if result.stdout:
                    try:
                        output_data = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        output_data = {"raw_output": result.stdout}
                
                results.append({
                    "test_name": test_structure["test_name"],
                    "success": success,
                    "return_code": result.returncode,
                    "output": output_data,
                    "stderr": result.stderr,
                    "execution_time": end_time - start_time
                })
                
            except subprocess.TimeoutExpired:
                results.append({
                    "test_name": test_structure["test_name"],
                    "success": False,
                    "error": "Test timed out after 60 seconds",
                    "execution_time": 60.0
                })
            except Exception as e:
                results.append({
                    "test_name": test_structure["test_name"],
                    "success": False,
                    "error": str(e),
                    "execution_time": 0.0
                })
        else:
            results.append({
                "test_name": test_structure["test_name"],
                "success": False,
                "error": f"Test file not found: {test_file}",
                "execution_time": 0.0
            })
    
    return results


def aggregate_results(execution_results: List[Dict[str, Any]], state: PostmanWorkflowState) -> Dict[str, Any]:
    """
    Aggregate execution results into summary statistics.
    
    Args:
        execution_results: List of individual execution results
        state: Current workflow state
        
    Returns:
        Aggregated results
    """
    if not execution_results:
        return {
            "overall_success": False,
            "passed_count": 0,
            "failed_count": 0,
            "success_rate": 0.0,
            "total_time": 0.0,
            "details": "No execution results to aggregate"
        }
    
    # Handle test runner results
    if len(execution_results) == 1 and execution_results[0].get("type") == "test_runner":
        runner_result = execution_results[0]
        
        if runner_result["success"] and "output" in runner_result:
            output = runner_result["output"]
            
            if isinstance(output, dict) and "total_tests" in output:
                # Structured output from test runner
                return {
                    "overall_success": output.get("failed_tests", 1) == 0,
                    "passed_count": output.get("passed_tests", 0),
                    "failed_count": output.get("failed_tests", 0),
                    "success_rate": output.get("success_rate", 0.0),
                    "total_time": output.get("total_time", runner_result.get("execution_time", 0.0)),
                    "details": output
                }
        
        # Fallback for runner results
        return {
            "overall_success": runner_result["success"],
            "passed_count": 1 if runner_result["success"] else 0,
            "failed_count": 0 if runner_result["success"] else 1,
            "success_rate": 100.0 if runner_result["success"] else 0.0,
            "total_time": runner_result.get("execution_time", 0.0),
            "details": runner_result
        }
    
    # Handle individual test results
    passed_count = sum(1 for result in execution_results if result.get("success", False))
    failed_count = len(execution_results) - passed_count
    total_time = sum(result.get("execution_time", 0.0) for result in execution_results)
    success_rate = (passed_count / len(execution_results)) * 100 if execution_results else 0.0
    
    return {
        "overall_success": failed_count == 0,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "success_rate": success_rate,
        "total_time": total_time,
        "details": execution_results
    }


def print_execution_summary(test_results: Dict[str, Any], state: PostmanWorkflowState):
    """
    Print a summary of test execution results.
    
    Args:
        test_results: Aggregated test results
        state: Current workflow state
    """
    collection_name = state.get("collection_info", {}).get("name", "Unknown Collection")
    
    print()
    print("=" * 60)
    print(f"📊 Test Execution Summary")
    print("=" * 60)
    print(f"Collection: {collection_name}")
    print(f"Total Tests: {test_results['passed_count'] + test_results['failed_count']}")
    print(f"Passed: {test_results['passed_count']}")
    print(f"Failed: {test_results['failed_count']}")
    print(f"Success Rate: {test_results['success_rate']:.1f}%")
    print(f"Total Time: {test_results['total_time']:.2f}s")
    print()
    
    if test_results["overall_success"]:
        print("🎉 All tests passed successfully!")
    else:
        print("⚠️  Some tests failed. Check the detailed results for more information.")
    
    print()