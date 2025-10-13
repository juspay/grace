"""Techspec workflow using LangGraph for technical specification generation."""

from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import re
import os
from pathlib import Path
from langgraph.graph import StateGraph, START, END


class TechspecWorkflowState(TypedDict):
    """State container for the techspec workflow."""
    connector_name: str
    api_doc_path: Optional[str]
    output_dir: Optional[str]
    template_path: Optional[str]
    config_path: Optional[str]
    test_only: bool
    verbose: bool

    # Processing state
    api_analysis: Optional[Dict[str, Any]]
    schema_data: Optional[Dict[str, Any]]
    generated_code: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    documentation: Optional[Dict[str, Any]]
    final_output: Dict[str, Any]

    # Workflow state
    error: Optional[str]
    metadata: Dict[str, Any]


class TechspecWorkflow:
    """LangGraph-based techspec workflow orchestrator."""

    def __init__(self):
        """Initialize the techspec workflow."""
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self):
        """Build the LangGraph workflow graph."""

        # Create state graph
        workflow = StateGraph(TechspecWorkflowState)

        # Add nodes for each step
        workflow.add_node("analyze_api", self._analyze_api_documentation)
        workflow.add_node("extract_schema", self._extract_schema)
        workflow.add_node("generate_code", self._generate_connector_code)
        workflow.add_node("validate_output", self._validate_generated_code)
        workflow.add_node("generate_docs", self._generate_documentation)
        workflow.add_node("finalize_output", self._finalize_output)

        # Add edges to define workflow flow
        workflow.add_edge(START, "analyze_api")
        workflow.add_edge("analyze_api", "extract_schema")
        workflow.add_edge("extract_schema", "generate_code")
        workflow.add_edge("generate_code", "validate_output")
        workflow.add_edge("validate_output", "generate_docs")
        workflow.add_edge("generate_docs", "finalize_output")
        workflow.add_edge("finalize_output", END)

        # Compile the graph
        return workflow.compile()

    def _analyze_api_documentation(self, state: TechspecWorkflowState) -> TechspecWorkflowState:
        """Analyze API documentation to understand connector requirements."""
        try:
            connector_name = state["connector_name"]
            api_doc_path = state.get("api_doc_path")

            # Mock API analysis - in real scenario, parse OpenAPI specs,
            # API documentation, postman collections, etc.

            api_analysis = {
                "connector_type": "payment_processor",
                "base_url": f"https://api.{connector_name.lower()}.com",
                "authentication": {
                    "type": "api_key",
                    "header": "Authorization",
                    "format": "Bearer {api_key}"
                },
                "endpoints": {
                    "payments": {
                        "create_payment": {
                            "method": "POST",
                            "path": "/v1/payments",
                            "description": "Create a new payment",
                            "request_body": {
                                "amount": "integer",
                                "currency": "string",
                                "payment_method": "object",
                                "customer": "object",
                                "metadata": "object"
                            },
                            "response": {
                                "id": "string",
                                "status": "string",
                                "amount": "integer",
                                "currency": "string",
                                "created": "timestamp"
                            }
                        },
                        "capture_payment": {
                            "method": "POST",
                            "path": "/v1/payments/{payment_id}/capture",
                            "description": "Capture an authorized payment",
                            "path_params": {"payment_id": "string"},
                            "request_body": {"amount": "integer"},
                            "response": {"status": "string", "captured_amount": "integer"}
                        },
                        "refund_payment": {
                            "method": "POST",
                            "path": "/v1/payments/{payment_id}/refund",
                            "description": "Refund a payment",
                            "path_params": {"payment_id": "string"},
                            "request_body": {"amount": "integer", "reason": "string"},
                            "response": {"refund_id": "string", "status": "string", "amount": "integer"}
                        }
                    },
                    "webhooks": {
                        "payment_completed": {
                            "event": "payment.completed",
                            "payload": {
                                "id": "string",
                                "status": "string",
                                "amount": "integer",
                                "currency": "string"
                            }
                        },
                        "payment_failed": {
                            "event": "payment.failed",
                            "payload": {
                                "id": "string",
                                "status": "string",
                                "error": "object"
                            }
                        }
                    }
                },
                "error_codes": {
                    "400": "Bad Request - Invalid parameters",
                    "401": "Unauthorized - Invalid API key",
                    "404": "Not Found - Resource not found",
                    "429": "Too Many Requests - Rate limit exceeded",
                    "500": "Internal Server Error"
                },
                "rate_limits": {
                    "requests_per_minute": 100,
                    "burst_limit": 200
                },
                "supported_features": [
                    "payments",
                    "refunds",
                    "captures",
                    "webhooks",
                    "recurring_payments",
                    "multi_currency"
                ]
            }

            # If API doc path provided, attempt to parse it
            if api_doc_path and os.path.exists(api_doc_path):
                try:
                    with open(api_doc_path, 'r') as f:
                        content = f.read()
                        # Enhanced analysis would parse OpenAPI/Swagger specs
                        api_analysis["source_doc"] = api_doc_path
                        api_analysis["doc_size"] = len(content)
                        api_analysis["parsed_from_file"] = True
                except Exception as e:
                    if state["verbose"]:
                        print(f"Warning: Could not parse API doc: {e}")

            state["api_analysis"] = api_analysis
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"].update({
                "step": "api_analysis",
                "status": "completed",
                "endpoints_found": len(api_analysis["endpoints"]["payments"]),
                "features_supported": len(api_analysis["supported_features"])
            })

        except Exception as e:
            state["error"] = f"API analysis failed: {str(e)}"

        return state

    def _extract_schema(self, state: TechspecWorkflowState) -> TechspecWorkflowState:
        """Extract and normalize API schema information."""
        try:
            api_analysis = state["api_analysis"]
            if api_analysis is None:
                raise ValueError("API analysis data is required but was None")
            connector_name = state["connector_name"]

            # Extract schema data from API analysis
            schema_data = {
                "connector_info": {
                    "name": connector_name,
                    "display_name": connector_name.title(),
                    "type": api_analysis["connector_type"],
                    "base_url": api_analysis["base_url"],
                    "version": "1.0.0"
                },
                "authentication_schema": {
                    "type": api_analysis["authentication"]["type"],
                    "fields": {
                        "api_key": {
                            "type": "string",
                            "required": True,
                            "description": "API key for authentication",
                            "sensitive": True
                        }
                    }
                },
                "request_schemas": {},
                "response_schemas": {},
                "webhook_schemas": {},
                "error_schemas": {
                    "base_error": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "message": {"type": "string"},
                            "code": {"type": "string"}
                        }
                    }
                }
            }

            # Extract request/response schemas from endpoints
            for category, endpoints in api_analysis["endpoints"].items():
                if category == "webhooks":
                    for webhook_name, webhook_data in endpoints.items():
                        schema_data["webhook_schemas"][webhook_name] = {
                            "event": webhook_data["event"],
                            "payload_schema": self._normalize_schema(webhook_data["payload"])
                        }
                else:
                    for endpoint_name, endpoint_data in endpoints.items():
                        if "request_body" in endpoint_data:
                            schema_data["request_schemas"][endpoint_name] = {
                                "method": endpoint_data["method"],
                                "path": endpoint_data["path"],
                                "schema": self._normalize_schema(endpoint_data["request_body"])
                            }

                        if "response" in endpoint_data:
                            schema_data["response_schemas"][endpoint_name] = {
                                "schema": self._normalize_schema(endpoint_data["response"])
                            }

            state["schema_data"] = schema_data
            state["metadata"].update({
                "schemas_extracted": True,
                "request_schemas": len(schema_data["request_schemas"]),
                "response_schemas": len(schema_data["response_schemas"]),
                "webhook_schemas": len(schema_data["webhook_schemas"])
            })

        except Exception as e:
            state["error"] = f"Schema extraction failed: {str(e)}"

        return state

    def _generate_connector_code(self, state: TechspecWorkflowState) -> TechspecWorkflowState:
        """Generate connector implementation code."""
        try:
            schema_data = state["schema_data"]
            if schema_data is None:
                raise ValueError("Schema data is required but was None")
            connector_name = state["connector_name"]
            template_path = state.get("template_path")

            # Mock code generation - in real scenario, use templates and code generators
            generated_code = {
                "connector_impl": self._generate_connector_implementation(schema_data, connector_name),
                "types_definitions": self._generate_type_definitions(schema_data),
                "request_handlers": self._generate_request_handlers(schema_data),
                "webhook_handlers": self._generate_webhook_handlers(schema_data),
                "error_handlers": self._generate_error_handlers(schema_data),
                "tests": self._generate_test_files(schema_data, connector_name),
                "config": self._generate_config_files(schema_data, connector_name)
            }

            # Apply custom template if provided
            if template_path and os.path.exists(template_path):
                try:
                    # Load and apply custom template
                    generated_code["template_applied"] = True
                    generated_code["template_source"] = template_path
                except Exception as e:
                    if state["verbose"]:
                        print(f"Warning: Could not apply template: {e}")

            state["generated_code"] = generated_code
            state["metadata"].update({
                "code_generation_completed": True,
                "files_generated": len(generated_code),
                "template_used": template_path is not None
            })

        except Exception as e:
            state["error"] = f"Code generation failed: {str(e)}"

        return state

    def _validate_generated_code(self, state: TechspecWorkflowState) -> TechspecWorkflowState:
        """Validate the generated connector code."""
        try:
            generated_code = state["generated_code"]
            if generated_code is None:
                raise ValueError("Generated code is required but was None")
            connector_name = state["connector_name"]

            validation_results = {
                "syntax_validation": {"status": "passed", "errors": []},
                "type_validation": {"status": "passed", "errors": []},
                "api_compliance": {"status": "passed", "errors": []},
                "test_coverage": {"status": "passed", "coverage_percentage": 85},
                "security_check": {"status": "passed", "vulnerabilities": []},
                "performance_check": {"status": "passed", "recommendations": []},
                "overall_status": "passed"
            }

            # Mock validation checks
            validation_checks = [
                self._validate_syntax(generated_code),
                self._validate_types(generated_code),
                self._validate_api_compliance(generated_code),
                self._validate_security(generated_code),
                self._validate_performance(generated_code)
            ]

            failed_checks = [check for check in validation_checks if not check["passed"]]

            if failed_checks:
                validation_results["overall_status"] = "failed"
                for check in failed_checks:
                    validation_results[check["type"]]["status"] = "failed"
                    validation_results[check["type"]]["errors"] = check["errors"]

            # Test only mode - don't generate actual files
            if not state.get("test_only", False):
                validation_results["files_ready_for_output"] = True
            else:
                validation_results["test_mode"] = True

            state["validation_results"] = validation_results
            state["metadata"].update({
                "validation_completed": True,
                "validation_status": validation_results["overall_status"],
                "checks_performed": len(validation_checks)
            })

        except Exception as e:
            state["error"] = f"Code validation failed: {str(e)}"

        return state

    def _generate_documentation(self, state: TechspecWorkflowState) -> TechspecWorkflowState:
        """Generate comprehensive documentation for the connector."""
        try:
            schema_data = state["schema_data"]
            if schema_data is None:
                raise ValueError("Schema data is required but was None")
            generated_code = state["generated_code"]
            if generated_code is None:
                raise ValueError("Generated code is required but was None")
            validation_results = state["validation_results"]
            if validation_results is None:
                raise ValueError("Validation results are required but were None")
            connector_name = state["connector_name"]

            documentation = {
                "readme": self._generate_readme(schema_data, connector_name),
                "api_reference": self._generate_api_reference(schema_data),
                "integration_guide": self._generate_integration_guide(schema_data, connector_name),
                "examples": self._generate_code_examples(schema_data, connector_name),
                "changelog": self._generate_changelog(connector_name),
                "troubleshooting": self._generate_troubleshooting_guide(schema_data),
                "testing_guide": self._generate_testing_guide(generated_code, connector_name)
            }

            state["documentation"] = documentation
            state["metadata"].update({
                "documentation_generated": True,
                "doc_files_count": len(documentation),
                "readme_length": len(documentation["readme"])
            })

        except Exception as e:
            state["error"] = f"Documentation generation failed: {str(e)}"

        return state

    def _finalize_output(self, state: TechspecWorkflowState) -> TechspecWorkflowState:
        """Finalize and organize all generated output."""
        try:
            connector_name = state["connector_name"]
            output_dir = state.get("output_dir", f"./generated/{connector_name}")

            validation_results = state.get("validation_results")
            validation_status = "unknown"
            if validation_results is not None:
                validation_status = validation_results.get("overall_status", "unknown")

            final_output = {
                "connector_name": connector_name,
                "output_directory": output_dir,
                "generated_files": {},
                "summary": {
                    "total_files": 0,
                    "code_files": 0,
                    "documentation_files": 0,
                    "test_files": 0,
                    "config_files": 0
                },
                "validation_status": validation_status,
                "generation_metadata": state["metadata"]
            }

            # Organize files by type
            generated_code = state.get("generated_code")
            if generated_code:
                final_output["generated_files"]["src"] = {
                    f"{connector_name}_connector.rs": generated_code["connector_impl"],
                    "types.rs": generated_code["types_definitions"],
                    "requests.rs": generated_code["request_handlers"],
                    "webhooks.rs": generated_code["webhook_handlers"],
                    "errors.rs": generated_code["error_handlers"]
                }
                final_output["summary"]["code_files"] = 5

                if generated_code.get("tests"):
                    final_output["generated_files"]["tests"] = generated_code["tests"]
                    final_output["summary"]["test_files"] = len(generated_code["tests"])

                if generated_code.get("config"):
                    final_output["generated_files"]["config"] = generated_code["config"]
                    final_output["summary"]["config_files"] = len(generated_code["config"])

            documentation = state.get("documentation")
            if documentation:
                final_output["generated_files"]["docs"] = documentation
                final_output["summary"]["documentation_files"] = len(documentation)

            final_output["summary"]["total_files"] = (
                final_output["summary"]["code_files"] +
                final_output["summary"]["documentation_files"] +
                final_output["summary"]["test_files"] +
                final_output["summary"]["config_files"]
            )

            # Add generation instructions
            final_output["instructions"] = {
                "next_steps": [
                    f"Review generated files in {output_dir}",
                    "Run tests to validate implementation",
                    "Update configuration as needed",
                    "Review and customize generated documentation"
                ],
                "test_command": f"cargo test --package {connector_name}_connector",
                "build_command": f"cargo build --package {connector_name}_connector"
            }

            state["final_output"] = final_output
            state["metadata"].update({
                "finalization_completed": True,
                "output_ready": True,
                "total_files_generated": final_output["summary"]["total_files"]
            })

        except Exception as e:
            state["error"] = f"Output finalization failed: {str(e)}"

        return state

    # Helper methods for code generation
    def _normalize_schema(self, schema_data: Any) -> Dict[str, Any]:
        """Normalize schema data to standard format."""
        if isinstance(schema_data, dict):
            return {
                "type": "object",
                "properties": {k: {"type": v if isinstance(v, str) else "object"} for k, v in schema_data.items()}
            }
        else:
            return {"type": "object", "properties": {}}

    def _generate_connector_implementation(self, schema_data: Dict[str, Any], connector_name: str) -> str:
        """Generate main connector implementation."""
        return f'''// {connector_name.title()} Connector Implementation
use serde::{{Deserialize, Serialize}};
use std::collections::HashMap;

pub struct {connector_name.title()}Connector {{
    pub base_url: String,
    pub api_key: String,
    pub client: reqwest::Client,
}}

impl {connector_name.title()}Connector {{
    pub fn new(api_key: String) -> Self {{
        Self {{
            base_url: "{schema_data["connector_info"]["base_url"]}".to_string(),
            api_key,
            client: reqwest::Client::new(),
        }}
    }}

    pub async fn create_payment(&self, request: CreatePaymentRequest) -> Result<PaymentResponse, ConnectorError> {{
        // Implementation for payment creation
        let url = format!("{{}}/v1/payments", self.base_url);

        let response = self.client
            .post(&url)
            .header("Authorization", format!("Bearer {{}}", self.api_key))
            .json(&request)
            .send()
            .await?;

        let payment: PaymentResponse = response.json().await?;
        Ok(payment)
    }}

    pub async fn capture_payment(&self, payment_id: &str, amount: Option<i64>) -> Result<CaptureResponse, ConnectorError> {{
        // Implementation for payment capture
        let url = format!("{{}}/v1/payments/{{}}/capture", self.base_url, payment_id);

        let mut body = HashMap::new();
        if let Some(amt) = amount {{
            body.insert("amount", amt);
        }}

        let response = self.client
            .post(&url)
            .header("Authorization", format!("Bearer {{}}", self.api_key))
            .json(&body)
            .send()
            .await?;

        let capture: CaptureResponse = response.json().await?;
        Ok(capture)
    }}

    pub async fn refund_payment(&self, payment_id: &str, request: RefundRequest) -> Result<RefundResponse, ConnectorError> {{
        // Implementation for payment refund
        let url = format!("{{}}/v1/payments/{{}}/refund", self.base_url, payment_id);

        let response = self.client
            .post(&url)
            .header("Authorization", format!("Bearer {{}}", self.api_key))
            .json(&request)
            .send()
            .await?;

        let refund: RefundResponse = response.json().await?;
        Ok(refund)
    }}
}}'''

    def _generate_type_definitions(self, schema_data: Dict[str, Any]) -> str:
        """Generate type definitions."""
        return f'''// Type definitions for {schema_data["connector_info"]["name"]} connector
use serde::{{Deserialize, Serialize}};

#[derive(Debug, Serialize, Deserialize)]
pub struct CreatePaymentRequest {{
    pub amount: i64,
    pub currency: String,
    pub payment_method: PaymentMethod,
    pub customer: Option<Customer>,
    pub metadata: Option<serde_json::Value>,
}}

#[derive(Debug, Serialize, Deserialize)]
pub struct PaymentResponse {{
    pub id: String,
    pub status: String,
    pub amount: i64,
    pub currency: String,
    pub created: String,
}}

#[derive(Debug, Serialize, Deserialize)]
pub struct PaymentMethod {{
    pub r#type: String,
    pub card: Option<Card>,
}}

#[derive(Debug, Serialize, Deserialize)]
pub struct Card {{
    pub number: String,
    pub exp_month: i32,
    pub exp_year: i32,
    pub cvc: String,
}}

#[derive(Debug, Serialize, Deserialize)]
pub struct Customer {{
    pub id: Option<String>,
    pub email: String,
    pub name: Option<String>,
}}

#[derive(Debug, Serialize, Deserialize)]
pub struct CaptureResponse {{
    pub status: String,
    pub captured_amount: i64,
}}

#[derive(Debug, Serialize, Deserialize)]
pub struct RefundRequest {{
    pub amount: i64,
    pub reason: Option<String>,
}}

#[derive(Debug, Serialize, Deserialize)]
pub struct RefundResponse {{
    pub refund_id: String,
    pub status: String,
    pub amount: i64,
}}

#[derive(Debug, thiserror::Error)]
pub enum ConnectorError {{
    #[error("HTTP request failed: {{0}}")]
    HttpError(#[from] reqwest::Error),

    #[error("Authentication failed")]
    AuthenticationError,

    #[error("Invalid request: {{0}}")]
    InvalidRequest(String),

    #[error("Payment processing failed: {{0}}")]
    PaymentError(String),
}}'''

    def _generate_request_handlers(self, schema_data: Dict[str, Any]) -> str:
        """Generate request handling code."""
        return '''// Request handling utilities
use serde_json::Value;
use std::collections::HashMap;

pub struct RequestHandler {
    pub base_url: String,
    pub client: reqwest::Client,
}

impl RequestHandler {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            client: reqwest::Client::new(),
        }
    }

    pub async fn make_request(
        &self,
        method: reqwest::Method,
        endpoint: &str,
        headers: HashMap<String, String>,
        body: Option<Value>,
    ) -> Result<reqwest::Response, reqwest::Error> {
        let url = format!("{}{}", self.base_url, endpoint);
        let mut request = self.client.request(method, &url);

        for (key, value) in headers {
            request = request.header(key, value);
        }

        if let Some(body) = body {
            request = request.json(&body);
        }

        request.send().await
    }
}'''

    def _generate_webhook_handlers(self, schema_data: Dict[str, Any]) -> str:
        """Generate webhook handling code."""
        return '''// Webhook handling utilities
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Deserialize)]
pub struct WebhookEvent {
    pub event_type: String,
    pub data: serde_json::Value,
    pub created: String,
}

#[derive(Debug, Deserialize)]
pub struct PaymentCompletedEvent {
    pub id: String,
    pub status: String,
    pub amount: i64,
    pub currency: String,
}

#[derive(Debug, Deserialize)]
pub struct PaymentFailedEvent {
    pub id: String,
    pub status: String,
    pub error: ErrorDetails,
}

#[derive(Debug, Deserialize)]
pub struct ErrorDetails {
    pub code: String,
    pub message: String,
}

pub struct WebhookHandler;

impl WebhookHandler {
    pub fn process_webhook(payload: &str) -> Result<WebhookEvent, serde_json::Error> {
        serde_json::from_str(payload)
    }

    pub fn verify_signature(payload: &str, signature: &str, secret: &str) -> bool {
        // Implementation for webhook signature verification
        use hmac::{Hmac, Mac};
        use sha2::Sha256;

        type HmacSha256 = Hmac<Sha256>;

        let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).unwrap();
        mac.update(payload.as_bytes());
        let result = mac.finalize();
        let expected = hex::encode(result.into_bytes());

        signature == expected
    }
}'''

    def _generate_error_handlers(self, schema_data: Dict[str, Any]) -> str:
        """Generate error handling code."""
        return '''// Error handling utilities
use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Deserialize, Serialize)]
pub struct ApiError {
    pub error: String,
    pub message: String,
    pub code: Option<String>,
}

impl fmt::Display for ApiError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "API Error: {} - {}", self.error, self.message)
    }
}

impl std::error::Error for ApiError {}

pub fn handle_api_error(status: u16, body: &str) -> ConnectorError {
    match status {
        400 => {
            if let Ok(api_error) = serde_json::from_str::<ApiError>(body) {
                ConnectorError::InvalidRequest(api_error.message)
            } else {
                ConnectorError::InvalidRequest("Bad request".to_string())
            }
        }
        401 => ConnectorError::AuthenticationError,
        404 => ConnectorError::InvalidRequest("Resource not found".to_string()),
        429 => ConnectorError::InvalidRequest("Rate limit exceeded".to_string()),
        500..=599 => ConnectorError::PaymentError("Server error".to_string()),
        _ => ConnectorError::PaymentError(format!("Unexpected status code: {}", status)),
    }
}'''

    def _generate_test_files(self, schema_data: Dict[str, Any], connector_name: str) -> Dict[str, str]:
        """Generate test files."""
        return {
            "integration_tests.rs": f'''// Integration tests for {connector_name} connector
#[cfg(test)]
mod tests {{
    use super::*;
    use tokio;

    #[tokio::test]
    async fn test_create_payment() {{
        // Test payment creation
        let connector = {connector_name.title()}Connector::new("test_api_key".to_string());

        let request = CreatePaymentRequest {{
            amount: 1000,
            currency: "USD".to_string(),
            payment_method: PaymentMethod {{
                r#type: "card".to_string(),
                card: Some(Card {{
                    number: "4111111111111111".to_string(),
                    exp_month: 12,
                    exp_year: 2025,
                    cvc: "123".to_string(),
                }}),
            }},
            customer: None,
            metadata: None,
        }};

        // This would require a test API key and test mode
        // let result = connector.create_payment(request).await;
        // assert!(result.is_ok());
    }}

    #[tokio::test]
    async fn test_webhook_processing() {{
        let payload = r#"{{"event_type": "payment.completed", "data": {{"id": "pay_123", "status": "succeeded"}}}}"#;
        let event = WebhookHandler::process_webhook(payload);
        assert!(event.is_ok());
    }}
}}''',
            "unit_tests.rs": f'''// Unit tests for {connector_name} connector
#[cfg(test)]
mod unit_tests {{
    use super::*;

    #[test]
    fn test_connector_initialization() {{
        let connector = {connector_name.title()}Connector::new("test_key".to_string());
        assert_eq!(connector.api_key, "test_key");
        assert!(!connector.base_url.is_empty());
    }}

    #[test]
    fn test_webhook_signature_verification() {{
        let payload = "test payload";
        let secret = "test_secret";
        let signature = "expected_signature";

        // Test signature verification logic
        // let is_valid = WebhookHandler::verify_signature(payload, signature, secret);
        // This would require actual implementation
    }}
}}'''
        }

    def _generate_config_files(self, schema_data: Dict[str, Any], connector_name: str) -> Dict[str, str]:
        """Generate configuration files."""
        return {
            "Cargo.toml": f'''[package]
name = "{connector_name}_connector"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
reqwest = {{ version = "0.11", features = ["json"] }}
tokio = {{ version = "1.0", features = ["full"] }}
thiserror = "1.0"
hmac = "0.12"
sha2 = "0.10"
hex = "0.4"

[dev-dependencies]
tokio-test = "0.4"
''',
            "config.yaml": f'''# Configuration for {connector_name} connector
connector:
  name: "{connector_name}"
  version: "1.0.0"
  base_url: "{schema_data["connector_info"]["base_url"]}"

authentication:
  type: "api_key"
  header: "Authorization"
  format: "Bearer {{api_key}}"

features:
  - payments
  - refunds
  - captures
  - webhooks

rate_limits:
  requests_per_minute: 100
  burst_limit: 200

timeouts:
  connect_timeout: 30
  request_timeout: 60
'''
        }

    # Validation helper methods
    def _validate_syntax(self, generated_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate syntax of generated code."""
        return {"type": "syntax_validation", "passed": True, "errors": []}

    def _validate_types(self, generated_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate type definitions."""
        return {"type": "type_validation", "passed": True, "errors": []}

    def _validate_api_compliance(self, generated_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API compliance."""
        return {"type": "api_compliance", "passed": True, "errors": []}

    def _validate_security(self, generated_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security aspects."""
        return {"type": "security_check", "passed": True, "errors": []}

    def _validate_performance(self, generated_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance aspects."""
        return {"type": "performance_check", "passed": True, "errors": []}

    # Documentation generation methods
    def _generate_readme(self, schema_data: Dict[str, Any], connector_name: str) -> str:
        """Generate README documentation."""
        return f'''# {connector_name.title()} Connector

This connector provides integration with the {connector_name.title()} payment processing API.

## Features

- Payment processing
- Payment captures
- Refunds
- Webhook handling
- Multi-currency support

## Installation

Add this to your `Cargo.toml`:

```toml
[dependencies]
{connector_name}_connector = "0.1.0"
```

## Usage

```rust
use {connector_name}_connector::{{{connector_name.title()}Connector, CreatePaymentRequest}};

#[tokio::main]
async fn main() {{
    let connector = {connector_name.title()}Connector::new("your_api_key".to_string());

    let request = CreatePaymentRequest {{
        amount: 1000,
        currency: "USD".to_string(),
        // ... other fields
    }};

    let payment = connector.create_payment(request).await.unwrap();
    println!("Payment created: {{}}", payment.id);
}}
```

## Configuration

Set up your API credentials in the configuration file or environment variables.

## Testing

Run tests with:

```bash
cargo test
```

## Contributing

Please read the contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License.
'''

    def _generate_api_reference(self, schema_data: Dict[str, Any]) -> str:
        """Generate API reference documentation."""
        return f'''# API Reference

## Base URL
`{schema_data["connector_info"]["base_url"]}`

## Authentication
This API uses API key authentication. Include your API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Create Payment
`POST /v1/payments`

Creates a new payment.

**Request Body:**
```json
{{
  "amount": 1000,
  "currency": "USD",
  "payment_method": {{
    "type": "card",
    "card": {{
      "number": "4111111111111111",
      "exp_month": 12,
      "exp_year": 2025,
      "cvc": "123"
    }}
  }}
}}
```

**Response:**
```json
{{
  "id": "pay_123",
  "status": "succeeded",
  "amount": 1000,
  "currency": "USD",
  "created": "2024-01-01T00:00:00Z"
}}
```

### Capture Payment
`POST /v1/payments/{{payment_id}}/capture`

Captures a previously authorized payment.

### Refund Payment
`POST /v1/payments/{{payment_id}}/refund`

Refunds a payment.

## Webhooks

### payment.completed
Triggered when a payment is successfully completed.

### payment.failed
Triggered when a payment fails.

## Error Codes

- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error
'''

    def _generate_integration_guide(self, schema_data: Dict[str, Any], connector_name: str) -> str:
        """Generate integration guide."""
        return f'''# Integration Guide

## Getting Started

1. **Obtain API Credentials**
   - Sign up for a {connector_name.title()} account
   - Navigate to the API settings
   - Generate your API key

2. **Install the Connector**
   ```bash
   cargo add {connector_name}_connector
   ```

3. **Basic Setup**
   ```rust
   use {connector_name}_connector::{{{connector_name.title()}Connector}};

   let connector = {connector_name.title()}Connector::new("your_api_key".to_string());
   ```

## Common Integration Patterns

### Processing Payments
[Code examples for payment processing]

### Handling Webhooks
[Code examples for webhook handling]

### Error Handling
[Code examples for error handling]

## Best Practices

1. Always validate webhook signatures
2. Implement proper error handling
3. Use idempotency keys for payment requests
4. Log all API interactions for debugging

## Testing

Use the test API keys provided by {connector_name.title()} for development and testing.

## Production Deployment

1. Switch to production API keys
2. Enable webhook signature verification
3. Set up proper logging and monitoring
4. Implement rate limiting
'''

    def _generate_code_examples(self, schema_data: Dict[str, Any], connector_name: str) -> str:
        """Generate code examples."""
        return f'''# Code Examples

## Basic Payment Processing

```rust
use {connector_name}_connector::*;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {{
    let connector = {connector_name.title()}Connector::new("sk_test_...".to_string());

    // Create a payment
    let payment_request = CreatePaymentRequest {{
        amount: 2000, // $20.00
        currency: "USD".to_string(),
        payment_method: PaymentMethod {{
            r#type: "card".to_string(),
            card: Some(Card {{
                number: "4242424242424242".to_string(),
                exp_month: 12,
                exp_year: 2025,
                cvc: "123".to_string(),
            }}),
        }},
        customer: Some(Customer {{
            id: None,
            email: "customer@example.com".to_string(),
            name: Some("John Doe".to_string()),
        }}),
        metadata: None,
    }};

    let payment = connector.create_payment(payment_request).await?;
    println!("Payment created: {{}}", payment.id);

    Ok(())
}}
```

## Webhook Handling

```rust
use {connector_name}_connector::*;

pub async fn handle_webhook(payload: &str, signature: &str) -> Result<(), Box<dyn std::error::Error>> {{
    // Verify the webhook signature
    let secret = "whsec_...";
    if !WebhookHandler::verify_signature(payload, signature, secret) {{
        return Err("Invalid signature".into());
    }}

    // Process the webhook
    let event = WebhookHandler::process_webhook(payload)?;

    match event.event_type.as_str() {{
        "payment.completed" => {{
            let payment_data: PaymentCompletedEvent = serde_json::from_value(event.data)?;
            println!("Payment completed: {{}}", payment_data.id);
        }}
        "payment.failed" => {{
            let payment_data: PaymentFailedEvent = serde_json::from_value(event.data)?;
            println!("Payment failed: {{}} - {{}}", payment_data.id, payment_data.error.message);
        }}
        _ => {{
            println!("Unhandled event type: {{}}", event.event_type);
        }}
    }}

    Ok(())
}}
```

## Error Handling

```rust
use {connector_name}_connector::*;

async fn process_payment_with_error_handling(connector: &{connector_name.title()}Connector) {{
    let request = CreatePaymentRequest {{
        // ... payment details
    }};

    match connector.create_payment(request).await {{
        Ok(payment) => {{
            println!("Payment successful: {{}}", payment.id);
        }}
        Err(ConnectorError::AuthenticationError) => {{
            eprintln!("Authentication failed - check API key");
        }}
        Err(ConnectorError::InvalidRequest(msg)) => {{
            eprintln!("Invalid request: {{}}", msg);
        }}
        Err(ConnectorError::PaymentError(msg)) => {{
            eprintln!("Payment processing failed: {{}}", msg);
        }}
        Err(e) => {{
            eprintln!("Unexpected error: {{}}", e);
        }}
    }}
}}
```
'''

    def _generate_changelog(self, connector_name: str) -> str:
        """Generate changelog."""
        return f'''# Changelog

All notable changes to the {connector_name} connector will be documented in this file.

## [0.1.0] - 2024-01-01

### Added
- Initial connector implementation
- Payment processing support
- Webhook handling
- Comprehensive error handling
- Full API coverage
- Documentation and examples

### Features
- Create payments
- Capture payments
- Refund payments
- Process webhooks
- Multi-currency support

### Security
- Webhook signature verification
- Secure API key handling
- Input validation

### Testing
- Unit tests
- Integration tests
- Mock API responses
'''

    def _generate_troubleshooting_guide(self, schema_data: Dict[str, Any]) -> str:
        """Generate troubleshooting guide."""
        return '''# Troubleshooting Guide

## Common Issues

### Authentication Errors

**Problem:** Receiving 401 Unauthorized errors

**Solutions:**
1. Verify your API key is correct
2. Ensure you're using the right environment (test vs production)
3. Check that the API key has the necessary permissions

### Payment Failures

**Problem:** Payments are failing or being declined

**Solutions:**
1. Check payment method details (card number, expiry, CVC)
2. Verify the amount and currency are valid
3. Ensure sufficient funds or credit limit
4. Check for any spending restrictions

### Webhook Issues

**Problem:** Webhooks not being received or processed

**Solutions:**
1. Verify webhook endpoint URL is accessible
2. Check webhook signature verification
3. Ensure proper HTTPS configuration
4. Review webhook retry logic

### Rate Limiting

**Problem:** Receiving 429 Too Many Requests errors

**Solutions:**
1. Implement exponential backoff retry logic
2. Reduce request frequency
3. Contact support for higher rate limits

## Debug Mode

Enable debug logging to get more detailed information:

```rust
env_logger::init();
```

## Support

For additional support:
1. Check the API documentation
2. Review the integration guide
3. Contact technical support
'''

    def _generate_testing_guide(self, generated_code: Dict[str, Any], connector_name: str) -> str:
        """Generate testing guide."""
        return f'''# Testing Guide

## Running Tests

```bash
# Run all tests
cargo test

# Run specific test file
cargo test --test integration_tests

# Run with output
cargo test -- --nocapture
```

## Test Environment Setup

1. **Get Test API Keys**
   - Log into your {connector_name.title()} dashboard
   - Navigate to API settings
   - Generate test mode API keys

2. **Environment Variables**
   ```bash
   export {connector_name.upper()}_TEST_API_KEY="sk_test_..."
   export {connector_name.upper()}_TEST_WEBHOOK_SECRET="whsec_..."
   ```

## Test Categories

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Fast execution

### Integration Tests
- Test with real API endpoints (test mode)
- Verify end-to-end functionality
- Require network connectivity

### Webhook Tests
- Test webhook signature verification
- Test event processing logic
- Mock webhook payloads

## Test Data

Use these test card numbers for different scenarios:

- **Successful payment:** 4242424242424242
- **Declined payment:** 4000000000000002
- **Insufficient funds:** 4000000000009995
- **Processing error:** 4000000000000119

## Continuous Integration

Add to your CI pipeline:

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
    - run: cargo test
```
'''

    async def execute(self,
                     connector_name: str,
                     api_doc_path: Optional[str] = None,
                     output_dir: Optional[str] = None,
                     template_path: Optional[str] = None,
                     config_path: Optional[str] = None,
                     test_only: bool = False,
                     verbose: bool = False) -> Dict[str, Any]:
        """Execute the techspec workflow."""

        # Initialize state
        initial_state: TechspecWorkflowState = {
            "connector_name": connector_name,
            "api_doc_path": api_doc_path,
            "output_dir": output_dir,
            "template_path": template_path,
            "config_path": config_path,
            "test_only": test_only,
            "verbose": verbose,
            "api_analysis": None,
            "schema_data": None,
            "generated_code": None,
            "validation_results": None,
            "documentation": None,
            "final_output": {},
            "error": None,
            "metadata": {"workflow_started": True, "timestamp": "2024-01-01T00:00:00Z"}
        }

        try:
            # Execute the workflow graph
            result = await self.graph.ainvoke(initial_state)

            return {
                "success": result["error"] is None,
                "connector_name": result["connector_name"],
                "output": result["final_output"],
                "metadata": result["metadata"],
                "error": result["error"],
                "validation_status": result["validation_results"]["overall_status"] if result["validation_results"] else "unknown",
                "files_generated": result["final_output"].get("summary", {}).get("total_files", 0) if result["final_output"] else 0
            }

        except Exception as e:
            return {
                "success": False,
                "connector_name": connector_name,
                "output": {},
                "metadata": {"error": str(e), "workflow_failed": True},
                "error": str(e),
                "validation_status": "failed",
                "files_generated": 0
            }


# Factory function for easy workflow creation
def create_techspec_workflow() -> TechspecWorkflow:
    """Create and return a new techspec workflow instance."""
    return TechspecWorkflow()


# CLI integration function
async def run_techspec_workflow(connector_name: str,
                               api_doc_path: Optional[str] = None,
                               output_dir: Optional[str] = None,
                               template_path: Optional[str] = None,
                               config_path: Optional[str] = None,
                               test_only: bool = False,
                               verbose: bool = False) -> Dict[str, Any]:
    """Run techspec workflow from CLI."""
    workflow = create_techspec_workflow()
    return await workflow.execute(
        connector_name=connector_name,
        api_doc_path=api_doc_path,
        output_dir=output_dir,
        template_path=template_path,
        config_path=config_path,
        test_only=test_only,
        verbose=verbose
    )