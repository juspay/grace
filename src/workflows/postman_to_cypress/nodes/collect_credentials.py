"""
Credential Collection Node
Dynamically collects required API credentials based on collection analysis
"""

import json
import os
import getpass
from typing import Dict, Any, List, Optional
from pathlib import Path
from ..states.postman_state import PostmanWorkflowState, CredentialRequirement


def collect_credentials(state: PostmanWorkflowState) -> PostmanWorkflowState:
    """
    Collect required API credentials based on the analyzed collection.
    
    Args:
        state: Current workflow state with credential requirements
        
    Returns:
        Updated state with collected credentials
    """
    try:
        credential_requirements = state.get("credential_requirements", [])
        if not credential_requirements:
            state["warnings"] = state.get("warnings", []) + ["No credential requirements found"]
            return state
        
        # Get progress tracker from state
        progress = state.get("_progress_tracker")
        if progress:
            progress.start_step(
                "Collecting API Credentials",
                {
                    "Auth Types": len(credential_requirements),
                    "Mode": "Headless" if state.get("headless") else "Interactive",
                    "Status": "Checking existing credentials"
                }
            )
        
        if state.get("verbose", False):
            print(f"🔑 Collecting credentials for {len(credential_requirements)} authentication types...")
        
        collected_credentials = {}
        auth_config = {}
        
        # Check if credentials already exist
        existing_creds = load_existing_credentials(state)
        if existing_creds:
            if progress:
                progress.update_details("Status", "Using existing credentials")
            if state.get("verbose", False):
                print("📂 Found existing credentials, using those...")
            collected_credentials = existing_creds
        else:
            if progress:
                progress.update_details("Status", "Collecting credentials interactively")
            # Interactive credential collection
            collected_credentials = interactive_credential_collection(credential_requirements, state)
        
        # Validate collected credentials
        validation_results = validate_credentials(collected_credentials, credential_requirements, state)
        
        if validation_results["valid"]:
            # Save credentials securely
            save_credentials(collected_credentials, state)
            
            # Build auth configuration
            auth_config = build_auth_config(collected_credentials, credential_requirements)
            
            state["collected_credentials"] = collected_credentials
            state["auth_config"] = auth_config
            
            # Update progress tracker
            if progress:
                progress.update_details("Status", "Credentials validated and saved")
                progress.update_details("Auth Types Collected", len(credential_requirements))
                progress.complete_step("✅ Credentials collected successfully")
            
            # Update metadata
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["collected_credentials"] = len(credential_requirements)
            
            if state.get("verbose", False):
                print("✅ Credentials collected and validated successfully")
                
        else:
            error_msg = f"Credential validation failed: {validation_results['errors']}"
            state["errors"] = state.get("errors", []) + [error_msg]
            state["error"] = error_msg
        
        return state
        
    except Exception as e:
        error_msg = f"Failed to collect credentials: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        state["error"] = error_msg
        if state.get("verbose", False):
            print(f"❌ {error_msg}")
        return state


def load_existing_credentials(state: PostmanWorkflowState) -> Optional[Dict[str, Any]]:
    """
    Load existing credentials from various sources.
    
    Args:
        state: Current workflow state
        
    Returns:
        Existing credentials or None
    """
    # Try environment variables first
    env_creds = load_from_environment()
    if env_creds:
        return env_creds
    
    # Try credentials file
    output_dir = state.get("output_dir", Path("."))
    creds_file = output_dir / "credentials.json"
    
    if creds_file.exists():
        try:
            with open(creds_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            if state.get("verbose", False):
                print(f"⚠️ Failed to load credentials file: {str(e)}")
    
    return None


def load_from_environment() -> Optional[Dict[str, Any]]:
    """Load credentials from environment variables"""
    env_creds = {}
    
    # Common environment variable patterns
    env_mappings = {
        "API_KEY": "api_key",
        "BEARER_TOKEN": "bearer_token", 
        "ACCESS_TOKEN": "access_token",
        "CLIENT_ID": "client_id",
        "CLIENT_SECRET": "client_secret",
        "USERNAME": "username",
        "PASSWORD": "password"
    }
    
    found_any = False
    for env_var, cred_key in env_mappings.items():
        value = os.getenv(env_var)
        if value:
            env_creds[cred_key] = value
            found_any = True
    
    return env_creds if found_any else None


def interactive_credential_collection(requirements: List[CredentialRequirement], state: PostmanWorkflowState) -> Dict[str, Any]:
    """
    Interactively collect credentials from user.
    
    Args:
        requirements: List of credential requirements
        state: Current workflow state
        
    Returns:
        Collected credentials
    """
    collected = {}
    collection_name = state.get("collection_info", {}).get("name", "Unknown Collection")
    
    if not state.get("headless", False):
        print("\n" + "="*60)
        print(f"🔐 Credential Collection for {collection_name}")
        print("="*60)
        print()
        print("The following credentials are required to run the tests:")
        print()
        
        for i, req in enumerate(requirements, 1):
            print(f"{i}. {req['description']}")
            print(f"   Type: {req['auth_type']}")
            print(f"   Required fields: {', '.join(req['required_fields'])}")
            if req.get('example_value'):
                print(f"   Example: {req['example_value']}")
            print()
    
    # Collect credentials for each requirement
    for req in requirements:
        auth_type = req["auth_type"]
        required_fields = req["required_fields"]
        description = req["description"]
        
        if not state.get("headless", False):
            print(f"📝 {description}")
        
        if auth_type == "bearer":
            token = collect_bearer_token(state)
            collected.update(token)
            
        elif auth_type == "basic":
            basic_creds = collect_basic_auth(state)
            collected.update(basic_creds)
            
        elif auth_type == "api_key":
            api_key_creds = collect_api_key(required_fields, state)
            collected.update(api_key_creds)
            
        elif auth_type == "oauth2":
            oauth_creds = collect_oauth2(state)
            collected.update(oauth_creds)
            
        else:
            custom_creds = collect_custom_auth(required_fields, auth_type, state)
            collected.update(custom_creds)
        
        if not state.get("headless", False):
            print()
    
    return collected


def collect_bearer_token(state: PostmanWorkflowState) -> Dict[str, str]:
    """Collect bearer token credentials"""
    if state.get("headless", False):
        # In headless mode, credentials must be provided via environment
        token = os.getenv("BEARER_TOKEN") or os.getenv("API_KEY")
        if not token:
            raise ValueError("Bearer token required but not found in environment variables")
        return {"bearer_token": token}
    
    token = getpass.getpass("Enter Bearer Token (input hidden): ").strip()
    while not token:
        print("❌ Bearer token cannot be empty")
        token = getpass.getpass("Enter Bearer Token (input hidden): ").strip()
    
    return {"bearer_token": token}


def collect_basic_auth(state: PostmanWorkflowState) -> Dict[str, str]:
    """Collect basic authentication credentials"""
    if state.get("headless", False):
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        if not username or not password:
            raise ValueError("Username and password required but not found in environment variables")
        return {"username": username, "password": password}
    
    username = input("Enter Username: ").strip()
    while not username:
        print("❌ Username cannot be empty")
        username = input("Enter Username: ").strip()
    
    password = getpass.getpass("Enter Password (input hidden): ").strip()
    while not password:
        print("❌ Password cannot be empty")
        password = getpass.getpass("Enter Password (input hidden): ").strip()
    
    return {"username": username, "password": password}


def collect_api_key(required_fields: List[str], state: PostmanWorkflowState) -> Dict[str, str]:
    """Collect API key credentials"""
    collected = {}
    
    for field in required_fields:
        if state.get("headless", False):
            value = os.getenv(field.upper()) or os.getenv("API_KEY")
            if not value:
                raise ValueError(f"{field} required but not found in environment variables")
            collected[field] = value
        else:
            if "secret" in field.lower() or "key" in field.lower():
                value = getpass.getpass(f"Enter {field} (input hidden): ").strip()
            else:
                value = input(f"Enter {field}: ").strip()
            
            while not value:
                print(f"❌ {field} cannot be empty")
                if "secret" in field.lower() or "key" in field.lower():
                    value = getpass.getpass(f"Enter {field} (input hidden): ").strip()
                else:
                    value = input(f"Enter {field}: ").strip()
            
            collected[field] = value
    
    return collected


def collect_oauth2(state: PostmanWorkflowState) -> Dict[str, str]:
    """Collect OAuth2 credentials"""
    if state.get("headless", False):
        access_token = os.getenv("ACCESS_TOKEN")
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        
        if not access_token:
            raise ValueError("OAuth2 access token required but not found in environment variables")
        
        return {
            "access_token": access_token,
            "client_id": client_id or "",
            "client_secret": client_secret or ""
        }
    
    print("For OAuth2, you can provide either:")
    print("1. Access token (if you already have one)")
    print("2. Client ID and Secret (for token generation)")
    
    access_token = getpass.getpass("Enter Access Token (optional, input hidden): ").strip()
    
    if access_token:
        return {"access_token": access_token}
    else:
        client_id = input("Enter Client ID: ").strip()
        client_secret = getpass.getpass("Enter Client Secret (input hidden): ").strip()
        
        while not client_id or not client_secret:
            print("❌ Both Client ID and Secret are required")
            client_id = input("Enter Client ID: ").strip()
            client_secret = getpass.getpass("Enter Client Secret (input hidden): ").strip()
        
        return {"client_id": client_id, "client_secret": client_secret}


def collect_custom_auth(required_fields: List[str], auth_type: str, state: PostmanWorkflowState) -> Dict[str, str]:
    """Collect custom authentication credentials"""
    collected = {}
    
    if not state.get("headless", False):
        print(f"Custom authentication type: {auth_type}")
    
    for field in required_fields:
        if state.get("headless", False):
            value = os.getenv(field.upper())
            if not value:
                raise ValueError(f"Custom field {field} required but not found in environment variables")
            collected[field] = value
        else:
            value = getpass.getpass(f"Enter {field} (input hidden): ").strip()
            while not value:
                print(f"❌ {field} cannot be empty")
                value = getpass.getpass(f"Enter {field} (input hidden): ").strip()
            collected[field] = value
    
    return collected


def validate_credentials(credentials: Dict[str, Any], requirements: List[CredentialRequirement], state: PostmanWorkflowState) -> Dict[str, Any]:
    """
    Validate collected credentials against requirements.
    
    Args:
        credentials: Collected credentials
        requirements: List of requirements to validate against
        state: Current workflow state
        
    Returns:
        Validation results
    """
    errors = []
    warnings = []
    
    # Check that all required fields are present
    for req in requirements:
        required_fields = req["required_fields"]
        auth_type = req["auth_type"]
        
        missing_fields = []
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                missing_fields.append(field)
        
        if missing_fields:
            errors.append(f"Missing required fields for {auth_type}: {missing_fields}")
    
    # Basic format validation
    if "bearer_token" in credentials:
        token = credentials["bearer_token"]
        if len(token) < 10:
            warnings.append("Bearer token seems unusually short")
    
    if "username" in credentials and "password" in credentials:
        if len(credentials["password"]) < 4:
            warnings.append("Password seems unusually short")
    
    # OAuth2 validation
    if "client_id" in credentials and "client_secret" in credentials:
        if not credentials["client_id"] or not credentials["client_secret"]:
            if "access_token" not in credentials:
                errors.append("Either access_token or both client_id and client_secret are required for OAuth2")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def save_credentials(credentials: Dict[str, Any], state: PostmanWorkflowState):
    """
    Save credentials securely to file.
    
    Args:
        credentials: Credentials to save
        state: Current workflow state
    """
    output_dir = state.get("output_dir", Path("."))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    creds_file = output_dir / "credentials.json"
    
    # Save credentials
    with open(creds_file, 'w') as f:
        json.dump(credentials, f, indent=2)
    
    # Set restrictive permissions (Unix only)
    try:
        os.chmod(creds_file, 0o600)  # Read/write for owner only
    except (OSError, AttributeError):
        # Windows or other systems that don't support chmod
        pass
    
    if state.get("verbose", False):
        print(f"💾 Credentials saved to {creds_file}")


def build_auth_config(credentials: Dict[str, Any], requirements: List[CredentialRequirement]) -> Dict[str, Any]:
    """
    Build authentication configuration for test execution.
    
    Args:
        credentials: Collected credentials
        requirements: Credential requirements
        
    Returns:
        Authentication configuration
    """
    auth_config = {
        "headers": {"Content-Type": "application/json"},
        "auth_type": None,
        "auth_data": {}
    }
    
    # Determine primary auth type and build config
    for req in requirements:
        auth_type = req["auth_type"]
        
        if auth_type == "bearer" and "bearer_token" in credentials:
            auth_config["headers"]["Authorization"] = f"Bearer {credentials['bearer_token']}"
            auth_config["auth_type"] = "bearer"
            
        elif auth_type == "basic" and "username" in credentials and "password" in credentials:
            import base64
            auth_string = base64.b64encode(f"{credentials['username']}:{credentials['password']}".encode()).decode()
            auth_config["headers"]["Authorization"] = f"Basic {auth_string}"
            auth_config["auth_type"] = "basic"
            
        elif auth_type == "api_key":
            # Add API key to headers
            for field in req["required_fields"]:
                if field in credentials:
                    auth_config["headers"][field] = credentials[field]
            auth_config["auth_type"] = "api_key"
            
        elif auth_type == "oauth2" and "access_token" in credentials:
            auth_config["headers"]["Authorization"] = f"Bearer {credentials['access_token']}"
            auth_config["auth_type"] = "oauth2"
            
        # Store raw credential data for advanced use cases
        auth_config["auth_data"].update(credentials)
    
    return auth_config