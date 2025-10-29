"""
Claude Code Service
Integrates with Claude Code CLI for enhanced AI capabilities in PostmanToCypress workflows
"""

import subprocess
import json
import tempfile
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from .system.prompt_config import prompt_config


class ClaudeCodeService:
    """Service for interfacing with Claude Code CLI"""
    
    def __init__(self, claude_code_path: Optional[str] = None):
        """
        Initialize Claude Code service
        
        Args:
            claude_code_path: Path to claude executable, defaults to system PATH
        """
        self.claude_code_path = claude_code_path or "claude"
        self.verify_claude_code_available()
    
    def verify_claude_code_available(self):
        """Verify that Claude Code is available in the system"""
        try:
            result = subprocess.run(
                [self.claude_code_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise Exception(f"Claude Code not available: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise Exception(f"Claude Code CLI not found. Please ensure 'claude' is installed and in PATH: {str(e)}")
    
    def get_ai_response(self, prompt: str, context_files: Optional[List[str]] = None, 
                       max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """
        Get AI response using Claude Code CLI
        
        Args:
            prompt: The prompt to send to Claude
            context_files: Optional list of file paths to include as context
            max_tokens: Maximum tokens for response (if supported)
            temperature: Temperature setting (if supported)
            
        Returns:
            Claude's response
        """
        try:
            # Build Claude Code command
            cmd = [self.claude_code_path, "--dangerously-skip-permissions", "-p", prompt]
            
            # Add context files if provided
            if context_files:
                for file_path in context_files:
                    if os.path.exists(file_path):
                        cmd.extend(["-f", file_path])
            
            # Execute Claude Code
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for complex analysis
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                raise Exception(f"Claude Code execution failed: {error_msg}")
            
            response = result.stdout.strip()
            if not response:
                raise Exception("Claude Code returned empty response")
            
            return response
            
        except subprocess.TimeoutExpired:
            raise Exception("Claude Code request timed out after 2 minutes")
        except Exception as e:
            raise Exception(f"Failed to get Claude Code response: {str(e)}")
    
    def analyze_api_endpoint(self, endpoint_data: Dict[str, Any]) -> str:
        """
        Analyze a single API endpoint for categorization
        
        Args:
            endpoint_data: Dictionary containing endpoint information
            
        Returns:
            Category classification (authorize, capture, psync, other)
        """
        # Get prompt from YAML configuration
        prompt = prompt_config().get_with_values("postmanApiCategorizationPrompt", {
            "endpoint_name": endpoint_data.get('name', 'Unknown'),
            "endpoint_method": endpoint_data.get('method', 'GET'),
            "endpoint_url": endpoint_data.get('url', ''),
            "endpoint_folder": endpoint_data.get('folder', 'root'),
            "endpoint_description": endpoint_data.get('description', 'No description'),
            "endpoint_headers": json.dumps(endpoint_data.get('headers', {}), indent=2),
            "endpoint_body_structure": json.dumps(self._get_body_structure(endpoint_data.get('body')), indent=2)
        })
        
        if not prompt:
            raise Exception("postmanApiCategorizationPrompt not found in prompts.yaml")
        
        try:
            response = self.get_ai_response(prompt)
            
            # Extract just the category from response
            category = response.strip().lower()
            
            # Clean up response in case Claude added extra text
            if "authorize" in category:
                return "authorize"
            elif "capture" in category:
                return "capture"
            elif "psync" in category:
                return "psync"
            else:
                return "other"
                
        except Exception as e:
            # Fallback to pattern-based categorization if Claude Code fails
            return self._fallback_categorization(endpoint_data)
    
    def determine_execution_order(self, categorized_endpoints: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Determine optimal execution order for categorized endpoints
        
        Args:
            categorized_endpoints: Dictionary of endpoints grouped by category
            
        Returns:
            Ordered list of endpoints for execution
        """
        # Prepare endpoint summaries for Claude Code analysis
        endpoint_summaries = {}
        for category, endpoints in categorized_endpoints.items():
            endpoint_summaries[category] = [
                {
                    "name": ep.get("name", ""),
                    "method": ep.get("method", ""),
                    "url": ep.get("url", ""),
                    "folder": ep.get("folder", "")
                }
                for ep in endpoints
            ]
        
        # Get prompt from YAML configuration
        prompt = prompt_config().get_with_values("postmanExecutionOrderPrompt", {
            "categorized_endpoints": json.dumps(endpoint_summaries, indent=2)
        })
        
        if not prompt:
            raise Exception("postmanExecutionOrderPrompt not found in prompts.yaml")
        
        try:
            response = self.get_ai_response(prompt)
            
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                execution_order = json.loads(json_str)
                
                # Map order to actual endpoints
                ordered_endpoints = []
                for order_item in execution_order:
                    category = order_item.get("category", "")
                    name = order_item.get("name", "")
                    
                    # Find matching endpoint
                    if category in categorized_endpoints:
                        for endpoint in categorized_endpoints[category]:
                            if endpoint.get("name") == name:
                                ordered_endpoints.append(endpoint)
                                break
                
                # Add any remaining endpoints that weren't included
                all_endpoints = []
                for endpoints in categorized_endpoints.values():
                    all_endpoints.extend(endpoints)
                
                for endpoint in all_endpoints:
                    if endpoint not in ordered_endpoints:
                        ordered_endpoints.append(endpoint)
                
                return ordered_endpoints
                
            else:
                # Fallback if JSON parsing fails
                return self._fallback_execution_order(categorized_endpoints)
                
        except Exception as e:
            # Fallback to simple ordering if Claude Code fails
            return self._fallback_execution_order(categorized_endpoints)
    
    def _get_body_structure(self, body: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Extract body structure for analysis (field names and types only)"""
        if not body:
            return {}
        
        structure = {}
        for key, value in body.items():
            if isinstance(value, dict):
                structure[key] = "object"
            elif isinstance(value, list):
                structure[key] = "array"
            elif isinstance(value, str):
                structure[key] = "string"
            elif isinstance(value, (int, float)):
                structure[key] = "number"
            elif isinstance(value, bool):
                structure[key] = "boolean"
            else:
                structure[key] = "unknown"
        
        return structure
    
    def _fallback_categorization(self, endpoint_data: Dict[str, Any]) -> str:
        """Fallback categorization based on simple patterns"""
        name_lower = endpoint_data.get('name', '').lower()
        url_lower = endpoint_data.get('url', '').lower()
        method = endpoint_data.get('method', 'GET').upper()
        
        # Authorize patterns
        authorize_patterns = [
            "create", "authorize", "intent", "payment", "charge", "transaction",
            "pay", "purchase", "order", "checkout"
        ]
        
        # Capture patterns  
        capture_patterns = [
            "capture", "confirm", "complete", "settle", "finalize"
        ]
        
        # Psync patterns
        psync_patterns = [
            "get", "retrieve", "status", "sync", "fetch", "show", "details"
        ]
        
        # Check authorize patterns
        if method == "POST" and any(pattern in name_lower or pattern in url_lower for pattern in authorize_patterns):
            return "authorize"
        
        # Check capture patterns
        if any(pattern in name_lower or pattern in url_lower for pattern in capture_patterns):
            return "capture"
        
        # Check psync patterns
        if method == "GET" or any(pattern in name_lower or pattern in url_lower for pattern in psync_patterns):
            return "psync"
        
        return "other"
    
    def _fallback_execution_order(self, categorized_endpoints: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Fallback execution order using simple rules"""
        ordered_endpoints = []
        
        # Order: other (setup) -> authorize -> capture -> psync -> other (cleanup)
        categories_order = ["other", "authorize", "capture", "psync"]
        
        for category in categories_order:
            if category in categorized_endpoints:
                ordered_endpoints.extend(categorized_endpoints[category])
        
        return ordered_endpoints


def get_claude_code_service() -> ClaudeCodeService:
    """Get a Claude Code service instance"""
    return ClaudeCodeService()