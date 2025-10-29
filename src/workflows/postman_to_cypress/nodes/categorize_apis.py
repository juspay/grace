"""
API Categorization Node using Claude Subagents
Analyzes API endpoints and categorizes them into payment flow patterns
"""

import json
from typing import Dict, Any, List, Optional, Literal
from ..states.postman_state import PostmanWorkflowState, APIEndpoint
from src.ai.ai_service import get_ai_service


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
        
        if state.get("verbose", False):
            print(f"🤖 Starting AI categorization of {len(api_endpoints)} endpoints...")
        
        # Initialize AI service
        ai_service = get_ai_service()
        
        # Categorize endpoints using Claude subagents
        categorized_endpoints = {}
        execution_sequence = []
        
        for i, endpoint in enumerate(api_endpoints):
            if state.get("verbose", False):
                print(f"  🔍 Analyzing endpoint {i+1}/{len(api_endpoints)}: {endpoint['name']}")
            
            # Categorize single endpoint
            category = categorize_single_endpoint(ai_service, endpoint, state)
            endpoint["category"] = category
            
            # Group by category
            if category not in categorized_endpoints:
                categorized_endpoints[category] = []
            categorized_endpoints[category].append(endpoint)
        
        # Determine execution order using Claude
        execution_sequence = determine_execution_order(ai_service, categorized_endpoints, state)
        
        # Update endpoints with execution order
        for order, endpoint in enumerate(execution_sequence):
            endpoint["execution_order"] = order + 1
        
        state["categorized_endpoints"] = categorized_endpoints
        state["execution_sequence"] = execution_sequence
        
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


def categorize_single_endpoint(ai_service, endpoint: APIEndpoint, state: PostmanWorkflowState) -> Literal["authorize", "capture", "psync", "other"]:
    """
    Categorize a single API endpoint using Claude.
    
    Args:
        ai_service: AI service instance
        endpoint: API endpoint to categorize
        state: Current workflow state
        
    Returns:
        Category classification
    """
    try:
        # Prepare context for Claude
        endpoint_context = {
            "name": endpoint["name"],
            "method": endpoint["method"],
            "url": endpoint["url"],
            "description": endpoint.get("description", ""),
            "folder": endpoint["folder"],
            "headers": endpoint.get("headers", {}),
            "body_structure": get_body_structure(endpoint.get("body"))
        }
        
        # Claude categorization prompt
        categorization_prompt = f"""
You are an expert payment API analyst. Analyze this API endpoint and categorize it into one of these payment flow patterns:

1. "authorize" - APIs that authorize payments, create payment intents, or initiate transactions
2. "capture" - APIs that capture previously authorized payments or confirm transactions  
3. "psync" - APIs that sync payment status, retrieve payment details, or check transaction state
4. "other" - APIs that don't fit the above patterns (webhooks, refunds, customers, etc.)

API Endpoint Details:
- Name: {endpoint_context['name']}
- Method: {endpoint_context['method']}
- URL: {endpoint_context['url']}
- Folder: {endpoint_context['folder']}
- Description: {endpoint_context['description']}
- Headers: {json.dumps(endpoint_context['headers'], indent=2)}
- Body Structure: {json.dumps(endpoint_context['body_structure'], indent=2)}

Payment Flow Context:
- Authorize: Create payment intent, authorize card, initiate payment
- Capture: Capture authorized payment, confirm payment, complete transaction
- Psync: Get payment status, retrieve payment details, sync transaction state

Analyze the endpoint name, URL path, HTTP method, and body structure to determine which category this API belongs to.

Respond with ONLY the category name: authorize, capture, psync, or other
"""
        
        # Get categorization from Claude
        response = ai_service.get_ai_response(categorization_prompt)
        category = response.strip().lower()
        
        # Validate category
        valid_categories = ["authorize", "capture", "psync", "other"]
        if category not in valid_categories:
            # Fallback categorization based on patterns
            category = fallback_categorization(endpoint)
        
        return category
        
    except Exception as e:
        if state.get("verbose", False):
            print(f"⚠️ Failed to categorize endpoint '{endpoint['name']}': {str(e)}")
        # Fallback to pattern-based categorization
        return fallback_categorization(endpoint)


def determine_execution_order(ai_service, categorized_endpoints: Dict[str, List[APIEndpoint]], state: PostmanWorkflowState) -> List[APIEndpoint]:
    """
    Determine the optimal execution order for payment flow testing.
    
    Args:
        ai_service: AI service instance
        categorized_endpoints: Endpoints grouped by category
        state: Current workflow state
        
    Returns:
        Ordered list of endpoints for execution
    """
    try:
        # Prepare endpoint summaries for Claude
        endpoint_summaries = {}
        for category, endpoints in categorized_endpoints.items():
            endpoint_summaries[category] = [
                {
                    "name": ep["name"],
                    "method": ep["method"],
                    "url": ep["url"],
                    "folder": ep["folder"]
                }
                for ep in endpoints
            ]
        
        # Claude ordering prompt
        ordering_prompt = f"""
You are an expert in payment flow testing. Given these categorized API endpoints, determine the optimal execution order for a complete payment test flow.

Categorized Endpoints:
{json.dumps(endpoint_summaries, indent=2)}

Payment Flow Logic:
1. AUTHORIZE endpoints should come first (create payment intent, authorize payment)
2. CAPTURE endpoints should come second (capture authorized payment)  
3. PSYNC endpoints should come third (verify payment status)
4. OTHER endpoints can be interspersed as needed (customer creation, etc.)

Consider these factors:
- Dependencies between endpoints (some may need output from previous calls)
- Logical payment flow progression
- Prerequisites (customer creation before payment, etc.)

Provide the execution order as a JSON array of objects with "category" and "name" fields:
[
    {{"category": "other", "name": "Create Customer"}},
    {{"category": "authorize", "name": "Create Payment Intent"}},
    {{"category": "capture", "name": "Capture Payment"}},
    {{"category": "psync", "name": "Get Payment Status"}}
]

Return ONLY the JSON array, no other text.
"""
        
        # Get ordering from Claude
        response = ai_service.get_ai_response(ordering_prompt)
        
        try:
            execution_order = json.loads(response.strip())
            ordered_endpoints = []
            
            # Map order to actual endpoints
            for order_item in execution_order:
                category = order_item["category"]
                name = order_item["name"]
                
                # Find matching endpoint
                if category in categorized_endpoints:
                    for endpoint in categorized_endpoints[category]:
                        if endpoint["name"] == name:
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
            
        except json.JSONDecodeError:
            # Fallback to default ordering
            return fallback_execution_order(categorized_endpoints)
        
    except Exception as e:
        if state.get("verbose", False):
            print(f"⚠️ Failed to determine execution order: {str(e)}")
        return fallback_execution_order(categorized_endpoints)


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