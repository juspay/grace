"""
API Categorization Node using Claude Subagents
Analyzes API endpoints and categorizes them into payment flow patterns
"""

import json
from typing import Dict, Any, List, Optional, Literal
from ..states.postman_state import PostmanWorkflowState, APIEndpoint
from src.ai.claude_code_service import get_claude_code_service
from src.utils.progress import create_ai_progress


def categorize_apis(state: PostmanWorkflowState) -> PostmanWorkflowState:
    """
    Use Claude subagents to categorize API endpoints into payment flow patterns.
    
    Args:
        state: Current workflow state with parsed endpoints
        
    Returns:
        Updated state with categorized endpoints and execution sequence
    """
    try:
        api_endpoints = state.get("api_endpoints", [])
        if not api_endpoints:
            state["warnings"] = state.get("warnings", []) + ["No API endpoints found to categorize"]
            return state
        
        # Get progress tracker from state
        progress = state.get("_progress_tracker")
        if progress:
            progress.start_step(
                "AI-Powered API Categorization",
                {
                    "Total Endpoints": len(api_endpoints),
                    "AI Model": "Claude",
                    "Categories": "authorize, capture, psync, other"
                }
            )
        
        # Initialize AI progress tracker
        ai_progress = create_ai_progress("API Categorization", state.get("verbose", False))
        
        if state.get("verbose", False):
            print(f"\n🤖 Starting AI categorization of {len(api_endpoints)} endpoints...")
            print(f"🧠 Claude Code will analyze each endpoint to identify payment flow patterns")
            print(f"📋 Categories: authorize, capture, psync, other")
            print(f"⚡ Using Claude Code CLI for enhanced reasoning capabilities")
            print()
        
        # Initialize Claude Code service
        try:
            claude_service = get_claude_code_service()
        except Exception as e:
            error_msg = f"Failed to initialize Claude Code service: {str(e)}"
            state["errors"] = state.get("errors", []) + [error_msg]
            state["error"] = error_msg
            if state.get("verbose", False):
                print(f"❌ {error_msg}")
                print("💡 Falling back to pattern-based categorization")
            # Use fallback categorization
            return fallback_categorize_all_endpoints(state, api_endpoints, progress)
        
        # Categorize endpoints using Claude subagents
        categorized_endpoints = {}
        execution_sequence = []
        
        for i, endpoint in enumerate(api_endpoints):
            if state.get("verbose", False):
                progress_bar = f"[{'█' * int(20 * i / len(api_endpoints))}{'░' * (20 - int(20 * i / len(api_endpoints)))}]"
                print(f"\n{progress_bar} {i}/{len(api_endpoints)} endpoints processed")
                print(f"🔍 Analyzing: {endpoint['name']}")
                print(f"   📍 Method: {endpoint['method']} | URL: {endpoint['url'][:50]}...")
                print(f"   📁 Folder: {endpoint['folder']}")
            
            # Categorize single endpoint using Claude Code
            try:
                if ai_progress:
                    prompt_preview = f"Categorizing {endpoint['name']} ({endpoint['method']} {endpoint['url'][:30]}...)"
                    ai_progress.start_ai_request(prompt_preview)
                
                category = claude_service.analyze_api_endpoint(endpoint)
                endpoint["category"] = category
                
                if ai_progress:
                    ai_progress.complete_ai_request(f"Category: {category}")
                    
            except Exception as e:
                if state.get("verbose", False):
                    print(f"   ⚠️ Claude Code failed for {endpoint['name']}: {str(e)}")
                    print(f"   🔄 Using fallback categorization")
                
                # Fallback to pattern-based categorization
                category = fallback_categorization(endpoint)
                endpoint["category"] = category
            
            if state.get("verbose", False):
                category_emoji = {
                    "authorize": "🔐",
                    "capture": "💳", 
                    "psync": "🔄",
                    "other": "📋"
                }
                print(f"   ✅ Categorized as: {category_emoji.get(category, '📋')} {category}")
            
            # Group by category
            if category not in categorized_endpoints:
                categorized_endpoints[category] = []
            categorized_endpoints[category].append(endpoint)
        
        # Determine execution order using Claude
        if state.get("verbose", False):
            print(f"\n🔄 Determining optimal execution order...")
            print(f"🧠 Claude will analyze dependencies and flow logic")
        
        ai_progress.start_ai_request("Analyzing execution order and dependencies...")
        try:
            execution_sequence = claude_service.determine_execution_order(categorized_endpoints)
            ai_progress.complete_ai_request("Execution order determined")
        except Exception as e:
            if state.get("verbose", False):
                print(f"   ⚠️ Claude Code failed for execution order: {str(e)}")
                print(f"   🔄 Using fallback ordering")
            execution_sequence = fallback_execution_order(categorized_endpoints)
            ai_progress.complete_ai_request("Fallback order applied")
        
        # Update endpoints with execution order
        for order, endpoint in enumerate(execution_sequence):
            endpoint["execution_order"] = order + 1
        
        state["categorized_endpoints"] = categorized_endpoints
        state["execution_sequence"] = execution_sequence
        
        # Update progress tracker
        if progress:
            category_summary = {cat: len(eps) for cat, eps in categorized_endpoints.items()}
            progress.update_details("Categorization Results", category_summary)
            progress.update_details("Execution Sequence", f"{len(execution_sequence)} steps")
            progress.complete_step(f"✅ Categorized {len(api_endpoints)} endpoints")
        
        # Update metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["categorized_endpoints"] = len(api_endpoints)
        
        if state.get("verbose", False):
            print(f"✅ Categorization complete:")
            for category, endpoints in categorized_endpoints.items():
                print(f"  📋 {category}: {len(endpoints)} endpoints")
            print(f"  🔄 Execution sequence: {len(execution_sequence)} steps")
        
        return state
        
    except Exception as e:
        error_msg = f"Failed to categorize APIs: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        state["error"] = error_msg
        if state.get("verbose", False):
            print(f"❌ {error_msg}")
        return state


# Old categorize_single_endpoint function removed - now using Claude Code service directly


# Old determine_execution_order function removed - now using Claude Code service directly


def get_body_structure(body: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """
    Extract body structure for analysis (field names and types only).
    
    Args:
        body: Request body data
        
    Returns:
        Simplified body structure
    """
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


def fallback_categorization(endpoint: APIEndpoint) -> Literal["authorize", "capture", "psync", "other"]:
    """
    Fallback categorization based on simple patterns.
    
    Args:
        endpoint: API endpoint to categorize
        
    Returns:
        Category classification
    """
    name_lower = endpoint["name"].lower()
    url_lower = endpoint["url"].lower()
    method = endpoint["method"].upper()
    
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


def fallback_execution_order(categorized_endpoints: Dict[str, List[APIEndpoint]]) -> List[APIEndpoint]:
    """
    Fallback execution order using simple rules.
    
    Args:
        categorized_endpoints: Endpoints grouped by category
        
    Returns:
        Ordered list of endpoints
    """
    ordered_endpoints = []
    
    # Order: other (setup) -> authorize -> capture -> psync -> other (cleanup)
    categories_order = ["other", "authorize", "capture", "psync"]
    
    for category in categories_order:
        if category in categorized_endpoints:
            ordered_endpoints.extend(categorized_endpoints[category])
    
    return ordered_endpoints


def fallback_categorize_all_endpoints(state: PostmanWorkflowState, api_endpoints: List[APIEndpoint], progress) -> PostmanWorkflowState:
    """Fallback categorization for all endpoints when Claude Code is not available"""
    categorized_endpoints = {}
    
    for endpoint in api_endpoints:
        category = fallback_categorization(endpoint)
        endpoint["category"] = category
        
        if category not in categorized_endpoints:
            categorized_endpoints[category] = []
        categorized_endpoints[category].append(endpoint)
    
    # Simple execution order
    execution_sequence = fallback_execution_order(categorized_endpoints)
    
    # Update endpoints with execution order
    for order, endpoint in enumerate(execution_sequence):
        endpoint["execution_order"] = order + 1
    
    state["categorized_endpoints"] = categorized_endpoints
    state["execution_sequence"] = execution_sequence
    
    # Update progress tracker
    if progress:
        category_summary = {cat: len(eps) for cat, eps in categorized_endpoints.items()}
        progress.update_details("Categorization Results", category_summary)
        progress.update_details("Execution Sequence", f"{len(execution_sequence)} steps")
        progress.complete_step(f"✅ Categorized {len(api_endpoints)} endpoints (fallback mode)")
    
    # Update metadata
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"]["categorized_endpoints"] = len(api_endpoints)
    
    if state.get("verbose", False):
        print(f"✅ Categorization complete (fallback mode):")
        for category, endpoints in categorized_endpoints.items():
            print(f"  📋 {category}: {len(endpoints)} endpoints")
        print(f"  🔄 Execution sequence: {len(execution_sequence)} steps")
    
    return state