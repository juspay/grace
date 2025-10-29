"""
Postman Collection Parser Node
Parses Postman JSON collection and extracts API endpoints
"""

import json
import urllib.parse
from typing import Dict, Any, List, Optional
from pathlib import Path
from ..states.postman_state import PostmanWorkflowState, APIEndpoint, CredentialRequirement


def parse_collection(state: PostmanWorkflowState) -> PostmanWorkflowState:
    """
    Parse Postman collection JSON and extract API endpoints with metadata.
    
    Args:
        state: Current workflow state containing collection file path
        
    Returns:
        Updated state with parsed endpoints and collection info
    """
    try:
        # Load Postman collection
        collection_path = state["collection_file"]
        with open(collection_path, 'r', encoding='utf-8') as f:
            raw_collection = json.load(f)
        
        state["raw_collection"] = raw_collection
        
        # Extract collection metadata
        collection_info = {
            "name": raw_collection.get("info", {}).get("name", "Unknown Collection"),
            "version": raw_collection.get("info", {}).get("version", "1.0.0"),
            "description": raw_collection.get("info", {}).get("description", ""),
            "schema": raw_collection.get("info", {}).get("schema", "")
        }
        state["collection_info"] = collection_info
        
        # Extract collection variables
        variables = {}
        if "variable" in raw_collection:
            for var in raw_collection["variable"]:
                variables[var.get("key", "")] = var.get("value", "")
        state["collection_variables"] = variables
        
        # Parse API endpoints
        api_endpoints = []
        credential_requirements = []
        
        def parse_items(items: List[Dict], folder_name: str = "root"):
            """Recursively parse collection items (folders and requests)"""
            for item in items:
                if "item" in item:
                    # This is a folder
                    folder_name = item.get("name", "unnamed_folder")
                    parse_items(item["item"], folder_name)
                else:
                    # This is a request
                    endpoint = parse_request(item, folder_name)
                    if endpoint:
                        api_endpoints.append(endpoint)
                        
                        # Extract credential requirements
                        auth_req = extract_auth_requirements(item)
                        if auth_req and auth_req not in credential_requirements:
                            credential_requirements.append(auth_req)
        
        # Start parsing from root items
        parse_items(raw_collection.get("item", []))
        
        state["api_endpoints"] = api_endpoints
        state["credential_requirements"] = credential_requirements
        
        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["total_endpoints"] = len(api_endpoints)
        
        if state.get("verbose", False):
            print(f"✅ Parsed {len(api_endpoints)} API endpoints from collection '{collection_info['name']}'")
            print(f"📁 Found {len(set(ep['folder'] for ep in api_endpoints))} folders")
            print(f"🔑 Detected {len(credential_requirements)} credential requirements")
        
        return state
        
    except Exception as e:
        error_msg = f"Failed to parse Postman collection: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        state["error"] = error_msg
        if state.get("verbose", False):
            print(f"❌ {error_msg}")
        return state


def parse_request(item: Dict[str, Any], folder_name: str) -> Optional[APIEndpoint]:
    """
    Parse a single request item from Postman collection.
    
    Args:
        item: Request item from collection
        folder_name: Name of the containing folder
        
    Returns:
        Parsed API endpoint or None if parsing fails
    """
    try:
        request = item.get("request", {})
        
        # Extract basic request info
        name = item.get("name", "unnamed_request")
        method = request.get("method", "GET").upper()
        
        # Parse URL
        url_info = request.get("url", {})
        if isinstance(url_info, str):
            url = url_info
            query_params = {}
        else:
            # URL is an object
            raw_url = url_info.get("raw", "")
            url = raw_url
            
            # Extract query parameters
            query_params = {}
            if "query" in url_info:
                for param in url_info["query"]:
                    if param.get("disabled", False):
                        continue
                    key = param.get("key", "")
                    value = param.get("value", "")
                    query_params[key] = value
        
        # Parse headers
        headers = {}
        if "header" in request:
            for header in request["header"]:
                if header.get("disabled", False):
                    continue
                key = header.get("key", "")
                value = header.get("value", "")
                headers[key] = value
        
        # Parse body
        body = None
        if "body" in request:
            body_info = request["body"]
            mode = body_info.get("mode", "")
            
            if mode == "raw":
                try:
                    body = json.loads(body_info.get("raw", "{}"))
                except json.JSONDecodeError:
                    body = {"raw": body_info.get("raw", "")}
            elif mode == "urlencoded":
                body = {}
                for param in body_info.get("urlencoded", []):
                    if not param.get("disabled", False):
                        body[param.get("key", "")] = param.get("value", "")
            elif mode == "formdata":
                body = {}
                for param in body_info.get("formdata", []):
                    if not param.get("disabled", False):
                        body[param.get("key", "")] = param.get("value", "")
        
        # Extract auth type
        auth_type = None
        if "auth" in request:
            auth_type = request["auth"].get("type", "")
        
        # Get description
        description = item.get("description", "")
        
        endpoint: APIEndpoint = {
            "name": name,
            "method": method,
            "url": url,
            "headers": headers,
            "body": body,
            "query_params": query_params,
            "auth_type": auth_type,
            "folder": folder_name,
            "description": description,
            "category": None,  # Will be set by categorize_apis node
            "execution_order": None  # Will be set by categorize_apis node
        }
        
        return endpoint
        
    except Exception as e:
        print(f"⚠️ Failed to parse request '{item.get('name', 'unknown')}': {str(e)}")
        return None


def extract_auth_requirements(item: Dict[str, Any]) -> Optional[CredentialRequirement]:
    """
    Extract authentication requirements from a request item.
    
    Args:
        item: Request item from collection
        
    Returns:
        Credential requirement or None if no auth found
    """
    try:
        request = item.get("request", {})
        auth = request.get("auth", {})
        
        if not auth:
            return None
            
        auth_type = auth.get("type", "")
        
        if auth_type == "bearer":
            return {
                "auth_type": "bearer",
                "required_fields": ["token"],
                "description": "Bearer token authentication",
                "example_value": "your_bearer_token_here"
            }
        elif auth_type == "basic":
            return {
                "auth_type": "basic", 
                "required_fields": ["username", "password"],
                "description": "Basic authentication with username and password",
                "example_value": "username:password"
            }
        elif auth_type == "apikey":
            apikey_data = auth.get("apikey", [])
            key_name = next((item["value"] for item in apikey_data if item["key"] == "key"), "api_key")
            return {
                "auth_type": "api_key",
                "required_fields": [key_name],
                "description": f"API key authentication using {key_name}",
                "example_value": "your_api_key_here"
            }
        elif auth_type == "oauth2":
            return {
                "auth_type": "oauth2",
                "required_fields": ["access_token", "client_id", "client_secret"],
                "description": "OAuth 2.0 authentication",
                "example_value": "oauth_access_token"
            }
        else:
            return {
                "auth_type": "custom",
                "required_fields": ["custom_auth"],
                "description": f"Custom authentication type: {auth_type}",
                "example_value": "custom_auth_value"
            }
            
    except Exception as e:
        print(f"⚠️ Failed to extract auth requirements: {str(e)}")
        return None