"""
Test Structure Generator Node
Generates deterministic test structures inspired by Cypress patterns
"""

import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from ..states.postman_state import PostmanWorkflowState, APIEndpoint, TestStructure


def generate_tests(state: PostmanWorkflowState) -> PostmanWorkflowState:
    """
    Generate deterministic test structures from categorized API endpoints.
    
    Args:
        state: Current workflow state with categorized endpoints
        
    Returns:
        Updated state with generated test structures
    """
    try:
        execution_sequence = state.get("execution_sequence", [])
        if not execution_sequence:
            state["warnings"] = state.get("warnings", []) + ["No execution sequence found to generate tests"]
            return state
        
        # Get progress tracker from state
        progress = state.get("_progress_tracker")
        if progress:
            progress.start_step(
                "Generating Test Structures",
                {
                    "Total Tests": len(execution_sequence),
                    "Test Type": "Python (Cypress-inspired)",
                    "Output Format": "Deterministic test files"
                }
            )
        
        if state.get("verbose", False):
            print(f"🏗️ Generating test structures for {len(execution_sequence)} endpoints...")
        
        test_structures = []
        test_files = {}
        test_config = {
            "collection_name": state.get("collection_info", {}).get("name", "UnknownCollection"),
            "base_url": extract_base_url(execution_sequence),
            "total_tests": len(execution_sequence),
            "execution_order": [ep["name"] for ep in execution_sequence]
        }
        
        # Generate test structures
        for i, endpoint in enumerate(execution_sequence):
            if progress:
                progress.update_details("Current", f"Generating test {i+1}/{len(execution_sequence)}: {endpoint['name']}")
            
            test_structure = generate_single_test(endpoint, i, execution_sequence, state)
            test_structures.append(test_structure)
            
            # Generate test file content
            test_file_content = generate_test_file_content(test_structure, state)
            test_files[test_structure["test_file"]] = test_file_content
        
        # Generate main test runner
        test_runner_content = generate_test_runner(test_structures, state)
        test_files["test_runner.py"] = test_runner_content
        
        # Generate configuration file
        config_content = generate_config_file(test_config, state)
        test_files["test_config.py"] = config_content
        
        state["test_structures"] = test_structures
        state["test_files"] = test_files
        state["test_config"] = test_config
        
        # Update progress tracker
        if progress:
            progress.update_details("Generated Files", len(test_files))
            progress.update_details("Test Structures", len(test_structures))
            progress.complete_step(f"✅ Generated {len(test_structures)} tests with {len(test_files)} files")
        
        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["generated_tests"] = len(test_structures)
        
        if state.get("verbose", False):
            print(f"✅ Generated {len(test_structures)} test structures")
            print(f"📄 Created {len(test_files)} test files")
        
        return state
        
    except Exception as e:
        error_msg = f"Failed to generate tests: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        state["error"] = error_msg
        if state.get("verbose", False):
            print(f"❌ {error_msg}")
        return state


def generate_single_test(endpoint: APIEndpoint, index: int, all_endpoints: List[APIEndpoint], state: PostmanWorkflowState) -> TestStructure:
    """
    Generate a single test structure for an API endpoint.
    
    Args:
        endpoint: API endpoint to generate test for
        index: Position in execution sequence
        all_endpoints: All endpoints in sequence
        state: Current workflow state
        
    Returns:
        Generated test structure
    """
    # Generate test name and file
    safe_name = sanitize_name(endpoint["name"])
    test_name = f"test_{index:03d}_{safe_name}"
    test_file = f"{test_name}.py"
    
    # Determine dependencies
    dependencies = []
    if index > 0:
        # Add dependency on previous test
        prev_endpoint = all_endpoints[index - 1]
        prev_safe_name = sanitize_name(prev_endpoint["name"])
        dependencies.append(f"test_{index-1:03d}_{prev_safe_name}")
    
    # Generate assertions based on endpoint type
    assertions = generate_assertions(endpoint)
    
    # Generate pre/post conditions
    pre_conditions = generate_pre_conditions(endpoint, index, all_endpoints)
    post_conditions = generate_post_conditions(endpoint, index, all_endpoints)
    
    test_structure: TestStructure = {
        "test_name": test_name,
        "test_file": test_file,
        "dependencies": dependencies,
        "api_endpoint": endpoint,
        "assertions": assertions,
        "pre_conditions": pre_conditions,
        "post_conditions": post_conditions
    }
    
    return test_structure


def generate_assertions(endpoint: APIEndpoint) -> List[Dict[str, Any]]:
    """
    Generate appropriate assertions based on endpoint category and method.
    
    Args:
        endpoint: API endpoint
        
    Returns:
        List of assertion configurations
    """
    assertions = []
    
    # Basic status code assertion
    if endpoint["method"] in ["POST", "PUT"]:
        assertions.append({
            "type": "status_code",
            "expected": [200, 201, 202],
            "description": f"Check {endpoint['method']} request succeeds"
        })
    elif endpoint["method"] == "GET":
        assertions.append({
            "type": "status_code", 
            "expected": [200],
            "description": "Check GET request succeeds"
        })
    
    # Response time assertion
    assertions.append({
        "type": "response_time",
        "max_time": 10000,  # 10 seconds
        "description": "Check response time is reasonable"
    })
    
    # Content type assertion
    assertions.append({
        "type": "content_type",
        "expected": "application/json",
        "description": "Check response is JSON"
    })
    
    # Category-specific assertions
    category = endpoint.get("category", "other")
    
    if category == "authorize":
        assertions.extend([
            {
                "type": "response_body",
                "field": "id",
                "condition": "exists",
                "description": "Check payment/transaction ID is returned"
            },
            {
                "type": "response_body",
                "field": "status",
                "condition": "in",
                "expected": ["pending", "authorized", "requires_confirmation"],
                "description": "Check authorization status is valid"
            }
        ])
    elif category == "capture":
        assertions.extend([
            {
                "type": "response_body",
                "field": "status",
                "condition": "in", 
                "expected": ["succeeded", "captured", "completed"],
                "description": "Check capture status indicates success"
            },
            {
                "type": "response_body",
                "field": "amount",
                "condition": "exists",
                "description": "Check captured amount is returned"
            }
        ])
    elif category == "psync":
        assertions.extend([
            {
                "type": "response_body",
                "field": "status",
                "condition": "exists",
                "description": "Check payment status is returned"
            },
            {
                "type": "response_body",
                "field": "id",
                "condition": "exists",
                "description": "Check payment ID is returned"
            }
        ])
    
    return assertions


def generate_pre_conditions(endpoint: APIEndpoint, index: int, all_endpoints: List[APIEndpoint]) -> List[str]:
    """
    Generate pre-conditions that must be met before running this test.
    
    Args:
        endpoint: Current API endpoint
        index: Position in sequence
        all_endpoints: All endpoints in sequence
        
    Returns:
        List of pre-condition descriptions
    """
    pre_conditions = []
    
    # Basic connectivity check
    pre_conditions.append("Verify API server is accessible")
    pre_conditions.append("Verify authentication credentials are available")
    
    # Category-specific pre-conditions
    category = endpoint.get("category", "other")
    
    if category == "capture" and index > 0:
        # Look for previous authorization
        for i in range(index):
            if all_endpoints[i].get("category") == "authorize":
                pre_conditions.append("Payment must be previously authorized")
                pre_conditions.append("Authorization ID must be available from previous test")
                break
    
    if category == "psync" and index > 0:
        # Look for previous payment creation
        for i in range(index):
            if all_endpoints[i].get("category") in ["authorize", "capture"]:
                pre_conditions.append("Payment must exist from previous test")
                pre_conditions.append("Payment ID must be available")
                break
    
    # Check for variable dependencies
    body = endpoint.get("body", {})
    if body:
        for key, value in body.items():
            if isinstance(value, str) and "{{" in value:
                pre_conditions.append(f"Variable {key} must be available from previous test")
    
    return pre_conditions


def generate_post_conditions(endpoint: APIEndpoint, index: int, all_endpoints: List[APIEndpoint]) -> List[str]:
    """
    Generate post-conditions that should be verified after running this test.
    
    Args:
        endpoint: Current API endpoint
        index: Position in sequence
        all_endpoints: All endpoints in sequence
        
    Returns:
        List of post-condition descriptions
    """
    post_conditions = []
    
    # Category-specific post-conditions
    category = endpoint.get("category", "other")
    
    if category == "authorize":
        post_conditions.extend([
            "Payment ID should be stored for subsequent tests",
            "Authorization status should be confirmed",
            "Amount should match request"
        ])
    elif category == "capture":
        post_conditions.extend([
            "Capture status should indicate success",
            "Captured amount should match authorized amount",
            "Payment status should be updated"
        ])
    elif category == "psync":
        post_conditions.extend([
            "Payment status should be current",
            "Response data should match previous operations"
        ])
    
    # Check if this endpoint's output is needed by later tests
    remaining_endpoints = all_endpoints[index + 1:]
    for future_endpoint in remaining_endpoints:
        future_body = future_endpoint.get("body", {})
        if future_body:
            for key, value in future_body.items():
                if isinstance(value, str) and endpoint["name"].lower() in value.lower():
                    post_conditions.append(f"Response data should be stored for {future_endpoint['name']}")
                    break
    
    return post_conditions


def generate_test_file_content(test_structure: TestStructure, state: PostmanWorkflowState) -> str:
    """
    Generate Python test file content for a test structure.
    
    Args:
        test_structure: Test structure to generate code for
        state: Current workflow state
        
    Returns:
        Python test file content
    """
    endpoint = test_structure["api_endpoint"]
    test_name = test_structure["test_name"]
    
    # Generate imports
    imports = [
        "import requests",
        "import json",
        "import time",
        "from typing import Dict, Any, Optional",
        "from test_config import TestConfig, get_credentials, store_variable, get_variable"
    ]
    
    # Generate test class
    class_name = "".join(word.capitalize() for word in test_name.split("_"))
    
    content = f'''"""
{endpoint['name']} Test
Generated from Postman collection: {state.get("collection_info", {}).get("name", "Unknown")}

Category: {endpoint.get("category", "other")}
Method: {endpoint["method"]}
URL: {endpoint["url"]}
"""

{chr(10).join(imports)}


class {class_name}:
    """Test class for {endpoint['name']}"""
    
    def __init__(self):
        self.config = TestConfig()
        self.test_name = "{test_name}"
        self.endpoint_name = "{endpoint['name']}"
        
    def setup(self):
        """Setup before test execution"""
        {generate_setup_code(test_structure)}
        
    def execute(self) -> Dict[str, Any]:
        """Execute the API test"""
        try:
            # Setup
            self.setup()
            
            # Prepare request
            {generate_request_code(endpoint)}
            
            # Execute request
            print(f"🚀 Executing {{self.endpoint_name}}...")
            start_time = time.time()
            response = requests.request(method, url, headers=headers, json=body, params=params)
            end_time = time.time()
            
            # Process response
            response_time = (end_time - start_time) * 1000  # ms
            
            result = {{
                "test_name": self.test_name,
                "success": True,
                "status_code": response.status_code,
                "response_time": response_time,
                "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "headers": dict(response.headers)
            }}
            
            # Run assertions
            assertion_results = self.run_assertions(result)
            result["assertions"] = assertion_results
            result["success"] = all(a["passed"] for a in assertion_results)
            
            # Post-conditions
            self.cleanup(result)
            
            return result
            
        except Exception as e:
            return {{
                "test_name": self.test_name,
                "success": False,
                "error": str(e),
                "assertions": []
            }}
    
    def run_assertions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run all assertions for this test"""
        assertion_results = []
        
        {generate_assertion_code(test_structure["assertions"])}
        
        return assertion_results
    
    def cleanup(self, result: Dict[str, Any]):
        """Cleanup after test execution"""
        {generate_cleanup_code(test_structure)}


if __name__ == "__main__":
    test = {class_name}()
    result = test.execute()
    print(json.dumps(result, indent=2))
'''
    
    return content


def generate_setup_code(test_structure: TestStructure) -> str:
    """Generate setup code for pre-conditions"""
    setup_lines = []
    
    for condition in test_structure["pre_conditions"]:
        if "credentials" in condition.lower():
            setup_lines.append("        # Verify credentials are available")
            setup_lines.append("        assert get_credentials(), 'Credentials not configured'")
        elif "previous test" in condition.lower():
            setup_lines.append("        # Check dependencies from previous tests")
            setup_lines.append("        # TODO: Add specific dependency checks")
    
    if not setup_lines:
        setup_lines.append("        pass")
    
    return "\n".join(setup_lines)


def generate_request_code(endpoint: APIEndpoint) -> str:
    """Generate request preparation code"""
    lines = [
        f'        method = "{endpoint["method"]}"',
        f'        url = "{endpoint["url"]}"',
        '        headers = get_credentials().get("headers", {})'
    ]
    
    # Add endpoint-specific headers
    if endpoint.get("headers"):
        lines.append("        headers.update({")
        for key, value in endpoint["headers"].items():
            lines.append(f'            "{key}": "{value}",')
        lines.append("        })")
    
    # Add body
    if endpoint.get("body"):
        lines.append("        body = {")
        for key, value in endpoint["body"].items():
            if isinstance(value, str) and "{{" in value:
                # Handle variables
                var_name = value.strip("{}")
                lines.append(f'            "{key}": get_variable("{var_name}") or "{value}",')
            else:
                lines.append(f'            "{key}": {json.dumps(value)},')
        lines.append("        }")
    else:
        lines.append("        body = None")
    
    # Add query params
    if endpoint.get("query_params"):
        lines.append("        params = {")
        for key, value in endpoint["query_params"].items():
            lines.append(f'            "{key}": "{value}",')
        lines.append("        }")
    else:
        lines.append("        params = None")
    
    return "\n".join(lines)


def generate_assertion_code(assertions: List[Dict[str, Any]]) -> str:
    """Generate assertion code"""
    lines = []
    
    for i, assertion in enumerate(assertions):
        assertion_type = assertion["type"]
        description = assertion["description"]
        
        lines.append(f"        # Assertion {i+1}: {description}")
        
        if assertion_type == "status_code":
            expected = assertion["expected"]
            if isinstance(expected, list):
                lines.append(f"        passed = result['status_code'] in {expected}")
            else:
                lines.append(f"        passed = result['status_code'] == {expected}")
        elif assertion_type == "response_time":
            max_time = assertion["max_time"]
            lines.append(f"        passed = result['response_time'] <= {max_time}")
        elif assertion_type == "content_type":
            expected = assertion["expected"]
            lines.append(f"        passed = result['headers'].get('content-type', '').startswith('{expected}')")
        elif assertion_type == "response_body":
            field = assertion["field"]
            condition = assertion["condition"]
            if condition == "exists":
                lines.append(f"        passed = '{field}' in result['response_data']")
            elif condition == "in":
                expected = assertion["expected"]
                lines.append(f"        passed = result['response_data'].get('{field}') in {expected}")
        
        lines.append("        assertion_results.append({")
        lines.append(f"            'description': '{description}',")
        lines.append("            'passed': passed")
        lines.append("        })")
        lines.append("")
    
    return "\n".join(lines)


def generate_cleanup_code(test_structure: TestStructure) -> str:
    """Generate cleanup code for post-conditions"""
    lines = []
    endpoint = test_structure["api_endpoint"]
    
    # Store important response data for future tests
    if endpoint.get("category") == "authorize":
        lines.append("        # Store payment ID for future tests")
        lines.append("        if result['success'] and 'id' in result['response_data']:")
        lines.append("            store_variable('payment_id', result['response_data']['id'])")
    
    if endpoint.get("category") == "capture":
        lines.append("        # Store capture information")
        lines.append("        if result['success']:")
        lines.append("            store_variable('capture_status', result['response_data'].get('status'))")
    
    if not lines:
        lines.append("        pass")
    
    return "\n".join(lines)


def generate_test_runner(test_structures: List[TestStructure], state: PostmanWorkflowState) -> str:
    """Generate main test runner file"""
    collection_name = state.get("collection_info", {}).get("name", "UnknownCollection")
    
    imports = [f"from {ts['test_name']} import {ts['test_name'].replace('_', '').title()}" for ts in test_structures]
    
    content = f'''"""
Test Runner for {collection_name}
Executes all generated tests in the correct order
"""

import json
import time
from typing import List, Dict, Any
from test_config import TestConfig

{chr(10).join(imports)}


class TestRunner:
    """Main test runner for the collection"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.config = TestConfig()
        self.results = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in sequence"""
        start_time = time.time()
        
        if not self.headless:
            print(f"🎯 Starting test execution for {collection_name}")
            print(f"📋 Total tests: {len(test_structures)}")
            print()
        
        test_classes = [
{chr(10).join(f"            {ts['test_name'].replace('_', '').title()}()," for ts in test_structures)}
        ]
        
        success_count = 0
        for i, test_class in enumerate(test_classes):
            if not self.headless:
                print(f"▶️  Running test {{i+1}}/{{len(test_classes)}}: {{test_class.endpoint_name}}")
            
            result = test_class.execute()
            self.results.append(result)
            
            if result["success"]:
                success_count += 1
                if not self.headless:
                    print(f"✅ Test passed in {{result.get('response_time', 0):.0f}}ms")
            else:
                if not self.headless:
                    print(f"❌ Test failed: {{result.get('error', 'Unknown error')}}")
            
            if not self.headless:
                print()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        summary = {{
            "collection_name": "{collection_name}",
            "total_tests": len(test_classes),
            "passed_tests": success_count,
            "failed_tests": len(test_classes) - success_count,
            "success_rate": (success_count / len(test_classes)) * 100,
            "total_time": total_time,
            "results": self.results
        }}
        
        if not self.headless:
            self.print_summary(summary)
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test execution summary"""
        print("=" * 60)
        print(f"📊 Test Execution Summary")
        print("=" * 60)
        print(f"Collection: {{summary['collection_name']}}")
        print(f"Total Tests: {{summary['total_tests']}}")
        print(f"Passed: {{summary['passed_tests']}}")
        print(f"Failed: {{summary['failed_tests']}}")
        print(f"Success Rate: {{summary['success_rate']:.1f}}%")
        print(f"Total Time: {{summary['total_time']:.2f}}s")
        print()
        
        if summary['failed_tests'] > 0:
            print("❌ Failed Tests:")
            for result in summary['results']:
                if not result['success']:
                    print(f"  - {{result['test_name']}}: {{result.get('error', 'Unknown error')}}")
            print()


if __name__ == "__main__":
    import sys
    
    headless = "--headless" in sys.argv
    runner = TestRunner(headless=headless)
    summary = runner.run_all_tests()
    
    # Exit with error code if any tests failed
    if summary['failed_tests'] > 0:
        sys.exit(1)
'''
    
    return content


def generate_config_file(test_config: Dict[str, Any], state: PostmanWorkflowState) -> str:
    """Generate test configuration file"""
    content = f'''"""
Test Configuration
Manages credentials, variables, and test settings
"""

import json
import os
from typing import Dict, Any, Optional


class TestConfig:
    """Configuration manager for tests"""
    
    def __init__(self):
        self.base_url = "{test_config.get('base_url', 'https://api.example.com')}"
        self.collection_name = "{test_config['collection_name']}"
        self.credentials = {{}}
        self.variables = {{}}
        
        # Load credentials from environment or file
        self.load_credentials()
    
    def load_credentials(self):
        """Load credentials from various sources"""
        # Try environment variables first
        if os.getenv("API_KEY"):
            self.credentials["headers"] = {{
                "Authorization": f"Bearer {{os.getenv('API_KEY')}}",
                "Content-Type": "application/json"
            }}
        
        # Try credentials file
        creds_file = os.getenv("CREDENTIALS_FILE", "credentials.json")
        if os.path.exists(creds_file):
            with open(creds_file, 'r') as f:
                file_creds = json.load(f)
                self.credentials.update(file_creds)


# Global instances
_config = TestConfig()
_variables = {{}}


def get_credentials() -> Dict[str, Any]:
    """Get authentication credentials"""
    return _config.credentials


def store_variable(key: str, value: Any):
    """Store a variable for use in subsequent tests"""
    _variables[key] = value


def get_variable(key: str) -> Optional[Any]:
    """Get a stored variable"""
    return _variables.get(key)


def setup_credentials():
    """Interactive credential setup"""
    print("🔑 Setting up credentials for {test_config['collection_name']}")
    print()
    
    # Get required credentials based on collection analysis
    {generate_credential_prompts(state)}
    
    # Save credentials
    with open("credentials.json", "w") as f:
        json.dump(_config.credentials, f, indent=2)
    
    print("✅ Credentials saved to credentials.json")


if __name__ == "__main__":
    setup_credentials()
'''
    
    return content


def generate_credential_prompts(state: PostmanWorkflowState) -> str:
    """Generate credential collection prompts"""
    lines = []
    
    credential_requirements = state.get("credential_requirements", [])
    
    for req in credential_requirements:
        auth_type = req["auth_type"]
        required_fields = req["required_fields"]
        description = req["description"]
        
        lines.append(f"    # {description}")
        
        if auth_type == "bearer":
            lines.append('    api_key = input("Enter your API key/Bearer token: ")')
            lines.append('    _config.credentials["headers"] = {')
            lines.append('        "Authorization": f"Bearer {api_key}",')
            lines.append('        "Content-Type": "application/json"')
            lines.append('    }')
        elif auth_type == "basic":
            lines.append('    username = input("Enter username: ")')
            lines.append('    password = input("Enter password: ")')
            lines.append('    import base64')
            lines.append('    auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()')
            lines.append('    _config.credentials["headers"] = {')
            lines.append('        "Authorization": f"Basic {auth_string}",')
            lines.append('        "Content-Type": "application/json"')
            lines.append('    }')
        elif auth_type == "api_key":
            for field in required_fields:
                lines.append(f'    {field} = input("Enter {field}: ")')
            lines.append('    _config.credentials["headers"] = {')
            for field in required_fields:
                lines.append(f'        "{field}": {field},')
            lines.append('        "Content-Type": "application/json"')
            lines.append('    }')
        
        lines.append("")
    
    if not lines:
        lines.append("    # No specific credentials required")
        lines.append("    pass")
    
    return "\n".join(lines)


def extract_base_url(endpoints: List[APIEndpoint]) -> str:
    """Extract common base URL from endpoints"""
    if not endpoints:
        return "https://api.example.com"
    
    urls = [ep["url"] for ep in endpoints]
    
    # Find common prefix
    if len(urls) == 1:
        url = urls[0]
        # Extract base URL (protocol + domain)
        if "://" in url:
            parts = url.split("/")
            return "/".join(parts[:3])
    
    # Find common base among multiple URLs
    common_parts = []
    split_urls = [url.split("/") for url in urls]
    
    if split_urls:
        min_parts = min(len(parts) for parts in split_urls)
        for i in range(min_parts):
            if all(parts[i] == split_urls[0][i] for parts in split_urls):
                common_parts.append(split_urls[0][i])
            else:
                break
    
    if len(common_parts) >= 3:  # protocol, empty, domain
        return "/".join(common_parts)
    
    return "https://api.example.com"


def sanitize_name(name: str) -> str:
    """Sanitize name for use in file names and Python identifiers"""
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = f"api_{sanitized}"
    
    return sanitized.lower()