You are an expert payment systems architect tasked with creating detailed technical specifications for integrating payment connectors into the UCS (Universal Connector Service) system.

Your specifications will be used as direct input for code generation AI systems, so they must be precise, structured, and comprehensive for the UCS architecture.

First, carefully review the project request:

<project_request>
Integration of the {{connector_name}} connector to UCS connector-service
</project_request>

<project_rules>
1. **UCS Architecture**: Use UCS-specific patterns (RouterDataV2, ConnectorIntegrationV2, domain-types)
2. **gRPC-First**: All communication is gRPC-based, not REST
3. **Type Safety**: Use domain_types crate for all type definitions
4. **Code Standards**: Follow UCS connector patterns and maintain consistency
5. **No Assumptions**: Do not assume implementation details; refer to documentation
6. **Reuse Components**: 
   - Use existing amount conversion utilities from common_utils
   - Do not create new amount conversion code
7. **File Organization**: Follow UCS directory structure
   ```
   backend/connector-integration/src/connectors/
   ├── {{connector_name}}.rs
   └── {{connector_name}}/
       └── transformers.rs
   ```
8. **API Types**: Define connector-specific request/response types based on actual API
9. **Complete Implementation**: Handle all payment methods and flows the connector supports
10. **UCS Testing**: Create gRPC integration tests for all implemented flows
11. **Error Handling**: Map all connector errors to UCS error types
12. **Payment Methods**: Support ALL payment methods the connector offers (cards, wallets, bank transfers, BNPL, etc.)
13. **Webhook Support**: Implement complete webhook handling if supported
14. **Resumable Development**: Structure for easy continuation if partially implemented
15. **Documentation**: Include comprehensive implementation notes
16. **🆕 Tech Spec Validation**: RECOMMENDED (but optional) - Include structured YAML sections for API validation testing:
   - api_config with test_url
   - auth with credential requirements and header formats
   - Complete flow specifications with test_example request bodies
   - Response structure with field names and status mappings

   **YAML is preferred** because it enables easy parsing and tech spec credibility validation.
   **If YAML not included**, AI will extract validation information from prose/Markdown using natural language understanding.

   Either format works - YAML is easier to parse, prose requires NLP extraction.
</project_rules>

<reference_docs>
| Document | Purpose |
| `grace-ucs/guides/types/types.md` | UCS type definitions and data structures |
| `grace-ucs/guides/patterns/patterns.md` | UCS implementation patterns |
| `grace-ucs/guides/learnings/learnings.md` | Lessons from previous UCS integrations |
| `grace-ucs/guides/errors/errors.md` | UCS error handling strategies |

### UCS ConnectorCommon
Contains common description of the connector for UCS architecture:

```rust
impl ConnectorCommon for {{connector_name}} {
    fn id(&self) -> &'static str {
        "{{connector_name}}"
    }
    
    fn base_url<'a>(&self, connectors: &'a Connectors) -> &'a str {
        connectors.{{connector_name}}.base_url.as_ref()
    }
    
    fn get_currency_unit(&self) -> api::CurrencyUnit {
        api::CurrencyUnit::Minor // or Base based on connector API
    }
    
    fn common_get_content_type(&self) -> &'static str {
        "application/json"
    }
    
    fn build_error_response(
        &self,
        res: Response,
        event_builder: Option<&mut ConnectorEvent>,
    ) -> CustomResult<ErrorResponse, errors::ConnectorError> {
        // UCS-specific error handling
    }
}
```

### UCS ConnectorIntegrationV2
For every API endpoint in UCS architecture:

```rust
impl ConnectorIntegrationV2<Flow, Request, Response> for {{connector_name}} {
    fn get_headers(
        &self,
        req: &RouterDataV2<Flow, Request, Response>,
        connectors: &Connectors,
    ) -> CustomResult<Vec<(String, Maskable<String>)>, errors::ConnectorError> {
        // UCS header implementation
    }
    
    fn get_url(
        &self,
        req: &RouterDataV2<Flow, Request, Response>,
        connectors: &Connectors,
    ) -> CustomResult<String, errors::ConnectorError> {
        // UCS URL building
    }
    
    fn get_request_body(
        &self,
        req: &RouterDataV2<Flow, Request, Response>,
        _connectors: &Connectors,
    ) -> CustomResult<RequestContent, errors::ConnectorError> {
        // UCS request transformation
    }
    
    fn build_request(
        &self,
        req: &RouterDataV2<Flow, Request, Response>,
        connectors: &Connectors,
    ) -> CustomResult<Option<RequestDetails>, errors::ConnectorError> {
        // UCS request building
    }
    
    fn handle_response(
        &self,
        data: &RouterDataV2<Flow, Request, Response>,
        event_builder: Option<&mut ConnectorEvent>,
        res: Response,
    ) -> CustomResult<RouterDataV2<Flow, Request, Response>, errors::ConnectorError> {
        // UCS response handling
    }
    
    fn get_error_response(
        &self,
        res: Response,
        event_builder: Option<&mut ConnectorEvent>,
    ) -> CustomResult<ErrorResponse, errors::ConnectorError> {
        // UCS error handling
    }
}
```

### UCS Flow Types
All flows that should be implemented:
- **Authorize**: Payment authorization
- **Capture**: Payment capture
- **Void**: Payment cancellation
- **Refund**: Payment refund
- **PSync**: Payment status sync
- **RSync**: Refund status sync
- **CreateOrder**: Multi-step payment initiation (if supported)
- **CreateSessionToken**: Session token creation (if supported)
- **SetupMandate**: Recurring payment setup (if supported)
- **IncomingWebhook**: Webhook handling (if supported)
- **DefendDispute**: Dispute handling (if supported)

### UCS Payment Method Support
Support ALL payment methods the connector offers:
- **Cards**: All card networks (Visa, Mastercard, Amex, etc.)
- **Wallets**: Apple Pay, Google Pay, PayPal, regional wallets
- **Bank Transfers**: ACH, SEPA, local bank transfers
- **BNPL**: Klarna, Affirm, Afterpay, regional BNPL
- **Bank Redirects**: iDEAL, Giropay, Sofort, etc.
- **Cash/Vouchers**: Boleto, OXXO, convenience store payments
- **Crypto**: Bitcoin, Ethereum (if supported)
- **Regional Methods**: UPI, Alipay, WeChat Pay, etc.

### UCS Testing
Create comprehensive gRPC integration tests:
```rust
// File: backend/grpc-server/tests/{{connector_name}}_test.rs
// Test all flows and payment methods through gRPC interface
```
</reference_docs>

<connector_information>
| Document | Purpose |
| `grace-ucs/references/{{connector_name}}_doc_*.md` | Connector-specific API documentation |
</connector_information>

<output_file>
Store the result in grace-ucs/connector_integration/{{connector_name}}/{{connector_name}}_specs.md
</output_file>

## UCS Technical Specification Template

Generate the technical specification using the following structure:

```markdown
# {{connector_name}} UCS Connector Integration Technical Specification

## 1. UCS Connector Overview

### 1.1 Basic Information
- **Connector Name**: {{connector_name}}
- **Base URL**: {{connector_base_url}}
- **API Documentation**: [Link to official API docs]
- **Supported Countries**: [List of supported countries]
- **Supported Currencies**: [List of supported currencies]
- **UCS Architecture**: gRPC-based stateless connector

### 1.2 UCS Authentication Method
- **Type**: [API Key / OAuth / Bearer Token / HMAC / etc.]
- **Header Format**: [e.g., "Authorization: Bearer {api_key}"]
- **Additional Headers**: [Any required headers]
- **UCS Auth Type**: [HeaderKey / BodyKey / SignatureKey]

### 1.3 UCS Supported Features
| Feature | Supported | Implementation Notes |
|---------|-----------|---------------------|
| Card Payments | ✓/✗ | All networks: Visa, MC, Amex |
| Apple Pay | ✓/✗ | Encrypted payment data |
| Google Pay | ✓/✗ | Token-based payments |
| PayPal | ✓/✗ | Redirect flow |
| Bank Transfers | ✓/✗ | ACH, SEPA, local methods |
| BNPL Providers | ✓/✗ | Klarna, Affirm, Afterpay |
| Bank Redirects | ✓/✗ | iDEAL, Giropay, etc. |
| Cash/Vouchers | ✓/✗ | Boleto, OXXO, etc. |
| 3DS 2.0 | ✓/✗ | Challenge/frictionless |
| Recurring Payments | ✓/✗ | Mandate setup |
| Partial Capture | ✓/✗ | Multiple captures |
| Partial Refunds | ✓/✗ | Refund flexibility |
| Webhooks | ✓/✗ | Real-time notifications |
| Disputes | ✓/✗ | Chargeback handling |

## 2. UCS API Endpoints

### 2.1 Payment Operations
| Operation | Method | Endpoint | UCS Flow |
|-----------|---------|----------|----------|
| Create Payment | POST | /v1/payments | Authorize |
| Capture Payment | POST | /v1/payments/{id}/capture | Capture |
| Cancel Payment | POST | /v1/payments/{id}/cancel | Void |
| Get Payment | GET | /v1/payments/{id} | PSync |

### 2.2 Refund Operations
| Operation | Method | Endpoint | UCS Flow |
|-----------|---------|----------|----------|
| Create Refund | POST | /v1/refunds | Refund |
| Get Refund | GET | /v1/refunds/{id} | RSync |

### 2.3 Advanced Operations
| Operation | Method | Endpoint | UCS Flow |
|-----------|---------|----------|----------|
| Create Order | POST | /v1/orders | CreateOrder |
| Session Token | POST | /v1/sessions | CreateSessionToken |
| Setup Mandate | POST | /v1/mandates | SetupMandate |

## 3. UCS Data Models

### 3.1 Payment Request Structure
```json
{
  "amount": 1000,
  "currency": "USD",
  "payment_method": {
    "type": "card",
    "card": {
      "number": "4111111111111111",
      "exp_month": "12",
      "exp_year": "2025",
      "cvc": "123"
    }
  },
  "customer": {
    "email": "customer@example.com"
  },
  "billing_address": {},
  "metadata": {}
}
```

### 3.2 Payment Response Structure
```json
{
  "id": "pay_xxxxx",
  "status": "succeeded",
  "amount": 1000,
  "currency": "USD",
  "gateway_reference": "ref_xxxxx",
  "redirect_url": null,
  "metadata": {}
}
```

### 3.3 UCS Status Mappings
| Connector Status | UCS AttemptStatus | Description |
|------------------|-------------------|-------------|
| pending | Pending | Payment being processed |
| authorized | Authorized | Payment authorized |
| captured | Charged | Payment captured |
| succeeded | Charged | Payment completed |
| failed | Failure | Payment failed |
| requires_action | AuthenticationPending | 3DS required |
| cancelled | Voided | Payment cancelled |

### 3.4 UCS Error Code Mappings
| Connector Error | UCS Error | Description |
|----------------|-----------|-------------|
| insufficient_funds | InsufficientFunds | Card declined |
| invalid_card | InvalidCardDetails | Card validation failed |
| authentication_required | AuthenticationRequired | 3DS needed |

## 4. UCS Implementation Details

### 4.1 RouterDataV2 Usage
```rust
// UCS uses RouterDataV2 for all operations
type AuthorizeRouterData = RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>;
type CaptureRouterData = RouterDataV2<Capture, PaymentsCaptureData, PaymentsResponseData>;
type VoidRouterData = RouterDataV2<Void, PaymentVoidData, PaymentsResponseData>;
type RefundRouterData = RouterDataV2<Refund, RefundsData, RefundsResponseData>;
type SyncRouterData = RouterDataV2<PSync, PaymentsSyncData, PaymentsResponseData>;
```

### 4.2 Payment Method Transformations
```rust
// Handle ALL payment methods in UCS
match payment_method_data {
    PaymentMethodData::Card(card) => {
        // Card payment handling
    }
    PaymentMethodData::Wallet(wallet_data) => match wallet_data {
        WalletData::ApplePay(apple_pay) => {
            // Apple Pay handling
        }
        WalletData::GooglePay(google_pay) => {
            // Google Pay handling  
        }
        // All other wallet types
    }
    PaymentMethodData::BankTransfer(bank_data) => {
        // Bank transfer handling
    }
    PaymentMethodData::BuyNowPayLater(bnpl_data) => {
        // BNPL handling
    }
    // All other payment method types
}
```

### 4.3 UCS Amount Handling
```rust
// UCS amount conversion
use common_utils::types::{MinorUnit, StringMinorUnit};
use domain_types::utils;

let amount = item.request.amount; // MinorUnit
let currency = item.request.currency;

// Convert based on connector requirements
let connector_amount = match self.get_currency_unit() {
    api::CurrencyUnit::Base => {
        utils::to_currency_base_unit(amount, currency)?
    }
    api::CurrencyUnit::Minor => {
        amount.to_string()
    }
};
```

## 5. UCS Webhook Implementation

### 5.1 Webhook Configuration
- **Endpoint**: gRPC webhook service
- **Signature Verification**: [Algorithm used]
- **Event Mapping**: Connector events to UCS events

### 5.2 UCS Webhook Events
| Connector Event | UCS IncomingWebhookEvent | Description |
|----------------|-------------------------|-------------|
| payment.authorized | PaymentIntentAuthorizationSuccess | Payment authorized |
| payment.captured | PaymentIntentSuccess | Payment captured |
| payment.failed | PaymentIntentFailure | Payment failed |
| refund.succeeded | RefundSuccess | Refund completed |

### 5.3 UCS Webhook Handler
```rust
impl IncomingWebhook for {{connector_name}} {
    fn get_webhook_object_reference_id(
        &self,
        request: &IncomingWebhookRequestDetails<'_>,
    ) -> CustomResult<ObjectReferenceId, errors::ConnectorError> {
        // Extract payment/refund ID
    }
    
    fn get_webhook_event_type(
        &self,
        request: &IncomingWebhookRequestDetails<'_>,
    ) -> CustomResult<IncomingWebhookEvent, errors::ConnectorError> {
        // Map events to UCS types
    }
}
```

## 6. UCS Error Handling

### 6.1 UCS Error Response Format
```rust
impl ConnectorCommon for {{connector_name}} {
    fn build_error_response(
        &self,
        res: Response,
        event_builder: Option<&mut ConnectorEvent>,
    ) -> CustomResult<ErrorResponse, errors::ConnectorError> {
        // Parse connector error response
        // Map to UCS ErrorResponse
        // Include all required fields
    }
}
```

## 7. UCS Testing Strategy

### 7.1 gRPC Integration Tests
```rust
// File: backend/grpc-server/tests/{{connector_name}}_test.rs

#[tokio::test]
async fn test_payment_authorize_success() {
    // Test authorization via gRPC
}

#[tokio::test]
async fn test_payment_capture() {
    // Test capture via gRPC
}

#[tokio::test]
async fn test_all_payment_methods() {
    // Test all supported payment methods
}
```

### 7.2 Test Coverage Requirements
- All payment methods supported by connector
- All flows (authorize, capture, void, refund, sync)
- Error scenarios for each flow
- Webhook event handling (if supported)
- 3DS authentication flows (if supported)
- Multi-currency support

## 8. UCS Connector-Specific Considerations

### 8.1 Implementation State Tracking
- **State 1**: Basic structure and auth implemented
- **State 2**: Core payment flows (authorize, capture, void)
- **State 3**: Refund flows and sync operations
- **State 4**: All payment methods implemented
- **State 5**: Webhook and advanced features
- **State 6**: Production-ready with full test coverage

### 8.2 Resumable Development Notes
- Clear modular structure for easy continuation
- Comprehensive documentation for each implemented feature
- Test cases for regression prevention
- Error handling for graceful degradation

## 9. UCS Implementation Checklist

### 9.1 Core UCS Implementation
- [ ] ConnectorCommon trait implementation
- [ ] ConnectorIntegrationV2 for Authorize flow
- [ ] ConnectorIntegrationV2 for Capture flow
- [ ] ConnectorIntegrationV2 for Void flow
- [ ] ConnectorIntegrationV2 for Refund flow
- [ ] ConnectorIntegrationV2 for PSync flow
- [ ] ConnectorIntegrationV2 for RSync flow
- [ ] UCS error handling and mapping

### 9.2 Payment Method Support
- [ ] Card payments (all networks)
- [ ] Apple Pay integration
- [ ] Google Pay integration
- [ ] PayPal integration
- [ ] Bank transfer methods
- [ ] BNPL provider integrations
- [ ] Bank redirect methods
- [ ] Cash/voucher methods
- [ ] Regional payment methods

### 9.3 Advanced UCS Features
- [ ] Webhook implementation (IncomingWebhook trait)
- [ ] 3DS authentication handling
- [ ] Recurring payment setup (SetupMandate)
- [ ] Multi-step payment flows (CreateOrder)
- [ ] Session token management
- [ ] Dispute handling (if supported)

### 9.4 UCS Testing & Quality
- [ ] gRPC integration tests for all flows
- [ ] Payment method specific test cases
- [ ] Error scenario testing
- [ ] Webhook event testing
- [ ] Performance testing
- [ ] Code documentation
- [ ] Implementation state documentation

## 10. Tech Spec Validation YAML (Optional but Recommended)

**Purpose:** These YAML sections enable automated tech spec credibility validation by testing the spec against the real connector API before implementation.

**Format Options:**
- ✅ **Preferred**: Include structured YAML sections below (easy parsing, minimal errors)
- ✅ **Alternative**: Skip YAML and describe in prose - AI will extract via natural language understanding

### 10.1 API Configuration
```yaml
api_config:
  # Test/sandbox environment URL for validation
  test_url: "https://api.sandbox.{{connector_name}}.com"
  production_url: "https://api.{{connector_name}}.com"  # For reference only
```

### 10.2 Authentication Configuration
```yaml
auth:
  # Define all authentication headers/parameters
  headers:
    - name: "Authorization"
      format: "Bearer {api_key}"  # {placeholders} for credentials
      required: true
      description: "Primary API key authentication"

    - name: "X-API-Secret"  # If secondary credential needed
      format: "{api_secret}"
      required: false
      description: "Optional secondary credential"

    - name: "X-Merchant-ID"  # If additional identifier needed
      format: "{key1}"
      required: false
      description: "Optional merchant identifier"
```

### 10.3 Flow Test Configurations

For each supported flow, provide complete test configuration:

#### Authorize Flow
```yaml
authorize:
  method: "POST"
  path: "/v1/payments"
  request:
    content_type: "application/json"  # or "application/x-www-form-urlencoded"
    # CRITICAL: Provide complete working example request body
    test_example: |
      {
        "amount": 1000,
        "currency": "USD",
        "payment_method": {
          "type": "card",
          "card": {
            "number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123"
          }
        },
        "capture_method": "manual",
        "description": "GRACE-UCS validation test"
      }
  response:
    success_status_codes: [200, 201]
    id_field: "id"  # Field name containing payment ID
    status_field: "status"  # Field name containing payment status
    required_fields: ["id", "status", "amount"]  # Fields that must be present
    status_mappings:
      # Map connector status values to UCS types
      "requires_capture": "Authorized"
      "processing": "Processing"
      "succeeded": "Charged"
      "failed": "Failed"
```

#### Capture Flow
```yaml
capture:
  method: "POST"
  path: "/v1/payments/{payment_id}/capture"  # {payment_id} from authorize
  url_params:
    - payment_id: "From authorize response"  # Indicate dependency
  request:
    content_type: "application/json"
    test_example: |
      {
        "amount": 1000
      }
  response:
    success_status_codes: [200]
    id_field: "id"
    status_field: "status"
    status_mappings:
      "succeeded": "Charged"
      "processing": "Processing"
```

#### Void Flow
```yaml
void:
  method: "POST"
  path: "/v1/payments/{payment_id}/cancel"
  url_params:
    - payment_id: "From fresh authorize"
  request:
    content_type: "application/json"
    test_example: null  # If no body required
  response:
    success_status_codes: [200]
    status_field: "status"
    status_mappings:
      "canceled": "Voided"
```

#### Refund Flow
```yaml
refund:
  method: "POST"
  path: "/v1/refunds"
  request:
    content_type: "application/json"
    test_example: |
      {
        "payment_id": "{payment_id}",
        "amount": 1000,
        "reason": "requested_by_customer"
      }
  response:
    success_status_codes: [200, 201]
    id_field: "id"
    status_field: "status"
    status_mappings:
      "succeeded": "Success"
      "pending": "Pending"
      "failed": "Failed"
```

#### Payment Sync Flow
```yaml
psync:
  method: "GET"
  path: "/v1/payments/{payment_id}"
  url_params:
    - payment_id: "From authorize"
  request:
    content_type: null  # GET request - no body
    test_example: null
  response:
    success_status_codes: [200]
    id_field: "id"
    status_field: "status"
    status_mappings:
      "requires_capture": "Authorized"
      "succeeded": "Charged"
      "canceled": "Voided"
```

#### Refund Sync Flow
```yaml
rsync:
  method: "GET"
  path: "/v1/refunds/{refund_id}"
  url_params:
    - refund_id: "From refund"
  request:
    content_type: null
    test_example: null
  response:
    success_status_codes: [200]
    id_field: "id"
    status_field: "status"
    status_mappings:
      "succeeded": "Success"
      "pending": "Pending"
      "failed": "Failed"
```

### 10.4 Validation Notes

**When YAML is provided:**
- AI extracts all information directly from structured YAML
- Generates curl test scripts automatically
- Validates tech spec against real API before implementation
- High confidence in spec accuracy

**When YAML is NOT provided:**
- AI extracts information from prose/Markdown descriptions using NLP
- Same validation capabilities, but extraction is more complex
- Recommended to provide clear examples in prose

**For validation to work, spec must include:**
1. ✅ Test environment URL
2. ✅ Auth header format (with {placeholder} for credentials)
3. ✅ Complete working request body examples for each flow
4. ✅ Response field names (id_field, status_field)
5. ✅ Status value mappings to UCS types
6. ✅ Expected success HTTP status codes

---

## 11. References

### 11.1 External Documentation
- [Connector API Documentation](link)
- [Payment Methods Guide](link)
- [Webhook Documentation](link)

### 11.2 UCS Internal References
- grace-ucs/guides/connector_integration_guide.md
- grace-ucs/guides/patterns/patterns.md
- grace-ucs/guides/types/types.md
- Similar UCS connectors: [List examples]

### 11.3 Tech Spec Validation
- testing/tech-spec-validation/README.md - Complete validation guide
- testing/tech-spec-validation/curl_generator.md - Curl generation from spec
- testing/tech-spec-validation/validation_rules.md - Validation criteria

---

**Important UCS Notes:**

1. **Focus on UCS Architecture**: Use RouterDataV2, ConnectorIntegrationV2, domain-types
2. **gRPC Integration**: All testing through gRPC interfaces
3. **Complete Payment Method Support**: Handle ALL methods the connector supports
4. **Resumable Implementation**: Structure for easy continuation
5. **Production-Ready**: Include comprehensive error handling and testing
6. **Type Safety**: Use UCS type system consistently throughout
7. **🆕 Validation First**: YAML sections enable tech spec validation before implementation
```

---

This UCS technical specification template ensures comprehensive connector integration planning specifically for the UCS architecture, with support for all payment methods and resumable development.