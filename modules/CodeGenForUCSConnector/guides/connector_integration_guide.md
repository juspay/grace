# UCS Connector Integration: Comprehensive Step-by-Step Guide

This guide provides a complete, resumable process for integrating payment connectors into the UCS (Universal Connector Service) system. It supports all payment methods and flows, and can be used to continue partial implementations.

> **Important:** This guide is UCS-specific. The architecture differs significantly from traditional Hyperswitch implementations.

## 🏗️ UCS Architecture Overview

### Key Components
```rust
// Core UCS imports for all connectors
use domain_types::{
    connector_flow::{Authorize, Capture, Void, Refund, PSync, RSync},
    connector_types::{
        PaymentsAuthorizeData, PaymentsCaptureData, PaymentVoidData,
        RefundsData, PaymentsSyncData, RefundSyncData,
        PaymentsResponseData, RefundsResponseData, RequestDetails, ResponseId
    },
    router_data_v2::RouterDataV2,
    router_response_types::Response,
};
use interfaces::connector_integration_v2::ConnectorIntegrationV2;
```

### UCS-Specific Patterns
- **RouterDataV2**: Enhanced type-safe data handling
- **ConnectorIntegrationV2**: Modern trait-based integration
- **Domain Types**: Centralized domain modeling
- **gRPC-first**: All communication via Protocol Buffers
- **Stateless**: No database dependencies

## 🎯 Connector Implementation States

### State Assessment
Before starting, determine your current implementation state:

1. **Fresh Start**: No implementation exists
2. **Partial Core**: Basic auth and authorize flow implemented
3. **Core Complete**: All basic flows working (auth, capture, void, refund)
4. **Extended**: Advanced flows and multiple payment methods
5. **Near Complete**: Only specific flows or payment methods missing
6. **Debug/Fix**: Implementation exists but has issues

## 📋 Complete Flow Coverage

### Core Payment Flows (Priority 1)
- **Authorize**: Initial payment authorization
- **Capture**: Capture authorized amounts
- **Void**: Cancel authorized payments
- **Refund**: Process refunds (full/partial)
- **PSync**: Payment status synchronization
- **RSync**: Refund status synchronization

### Advanced Flows (Priority 2)
- **CreateOrder**: Multi-step payment initiation
- **CreateSessionToken**: Secure session management
- **SetupMandate**: Recurring payment setup
- **DefendDispute**: Handle chargeback disputes
- **SubmitEvidence**: Submit dispute evidence

### Webhook Integration (Priority 3)
- **IncomingWebhook**: Real-time payment notifications
- **WebhookSourceVerification**: Signature validation
- **EventMapping**: Webhook event to status mapping

## 💳 Payment Method Support

### Card Payments
```rust
PaymentMethodData::Card(card_data) => {
    // Handle all card networks: Visa, Mastercard, Amex, Discover, etc.
    // Support 3DS authentication
    // Handle CVV verification
}
```

### Digital Wallets
```rust
PaymentMethodData::Wallet(wallet_data) => match wallet_data {
    WalletData::ApplePay(_) => // Apple Pay implementation
    WalletData::GooglePay(_) => // Google Pay implementation
    WalletData::PaypalRedirect(_) => // PayPal implementation
    // ... other wallets
}
```

### Bank Transfers
```rust
PaymentMethodData::BankTransfer(bank_data) => match bank_data {
    BankTransferData::AchBankTransfer => // ACH implementation
    BankTransferData::SepaBank => // SEPA implementation
    BankTransferData::Bacs => // BACS implementation
    // ... other bank transfer methods
}
```

### Buy Now Pay Later
```rust
PaymentMethodData::BuyNowPayLater(bnpl_data) => match bnpl_data {
    BuyNowPayLaterData::KlarnaRedirect => // Klarna implementation
    BuyNowPayLaterData::AffirmRedirect => // Affirm implementation
    BuyNowPayLaterData::AfterpayClearpayRedirect => // Afterpay implementation
    // ... other BNPL providers
}
```

## 🛠️ Implementation Process

### Phase 1: Preparation and Planning

#### Step 1.1: Analyze Current State
If resuming partial implementation:
```bash
# AI Command: "analyze current state of [ConnectorName] in UCS"
# The AI will examine existing code and identify:
# - Implemented flows
# - Supported payment methods  
# - Missing functionality
# - Code quality issues
```

#### Step 1.2: Create/Update Technical Specification
```bash
# For new implementation:
# Use: grace-ucs/connector_integration/template/tech_spec.md

# For continuing implementation:
# AI will update existing spec with missing components
```

#### Step 1.3: Implementation Planning
```bash
# AI will create detailed plan based on:
# - Current implementation state
# - Missing functionality
# - Priority of remaining work
# Use: grace-ucs/connector_integration/template/planner_steps.md
```

### Phase 2: Tech Spec Credibility Validation 🆕

**MANDATORY phase before implementation - validates tech spec against real API**

#### Step 2.1: Provide Test Credentials

After tech spec is generated, AI will request minimal credentials:

```
🔐 Tech Spec Credibility Validation

Connector: {{connector_name}}
Test URL: {{extracted_from_tech_spec}}

Please provide test credentials:
{
  "api_key": "sk_test_xxxxx",
  "api_secret": "optional_if_needed",
  "key1": "optional_additional"
}

IMPORTANT: Use test/sandbox credentials only!
```

**User provides only 3 values** - everything else comes from tech spec.

#### Step 2.2: Curl Test Generation

AI automatically generates 6 curl test scripts by extracting from tech spec:

- `01_authorize.sh` - Tests authorization endpoint
- `02_capture.sh` - Tests capture endpoint
- `03_void.sh` - Tests void/cancel endpoint
- `04_refund.sh` - Tests refund endpoint
- `05_psync.sh` - Tests payment status retrieval
- `06_rsync.sh` - Tests refund status retrieval

Each script contains:
- Base URL from `api_config.test_url`
- Endpoint path from flow spec
- Auth headers from `auth.headers` with user credentials
- Request body from `flow.request.test_example`

#### Step 2.3: Test Execution

Tests run sequentially against **real connector API**:

```bash
🧪 Running tech spec validation tests...

01_authorize.sh  → Creates payment, saves payment_id
02_capture.sh    → Captures using payment_id
03_void.sh       → Voids fresh authorization
04_refund.sh     → Refunds captured payment
05_psync.sh      → Retrieves payment status
06_rsync.sh      → Retrieves refund status
```

#### Step 2.4: Response Validation

For each test, AI validates:

✅ **HTTP Status** - Matches `success_status_codes`
✅ **Response Structure** - Contains `required_fields`
✅ **Field Names** - `id_field` and `status_field` exist
✅ **Status Mappings** - All actual statuses have mappings

**Common Issues Detected:**
- 404 → Wrong endpoint path in tech spec
- 401 → Wrong auth format in tech spec
- 400 → Wrong request body format
- 422 → Missing required field
- Missing field → Wrong field name in tech spec

#### Step 2.5: Credibility Report

AI generates detailed report:

```markdown
# Tech Spec Credibility Report

## Summary
✅ Passed: 5/6 flows
❌ Failed: 1/6 flow

## Issues Found

### Critical
1. Void endpoint path incorrect
   - Tech spec: /v1/payments/{id}/void
   - Actual: /v1/payments/{id}/cancel
   - Auto-fix: ✅ Available

## Credibility Score
Before fixes: 83%
After fixes: 100% (projected)
```

#### Step 2.6: Feedback Loop

**If all tests pass:**
```
✅ Tech Spec Credibility: VALIDATED
Proceeding to implementation...
```

**If any test fails:**
```
⚠️  Validation Failed (Attempt 1/3)

Choose action:
[A] Auto-fix - AI updates tech spec and re-validates
[M] Manual - You update tech spec, AI re-validates
[P] Proceed - Continue despite issues (NOT recommended)
[C] Cancel - Stop for review

Your choice:
```

**Auto-fix process:**
1. AI analyzes actual API responses
2. Updates tech spec with corrections
3. Regenerates curl scripts
4. Re-runs all tests
5. Shows updated results
6. Max 3 attempts

#### Step 2.7: Success Criteria

Tech spec validated when:
- ✅ All 6 flows return 2xx status codes
- ✅ All required fields present
- ✅ All statuses have mappings
- ✅ Authentication works
- ✅ No structural mismatches

**Only proceed to implementation after validation!**

#### Output Files

- `testing/tech-spec-validation/{{connector}}/credibility_report.md`
- `testing/tech-spec-validation/{{connector}}/responses/*.json`
- Validated tech spec ready for implementation

---

### Phase 3: Core Implementation

#### Step 2.1: Connector Structure Setup
```rust
// File: backend/connector-integration/src/connectors/connector_name.rs

#[derive(Debug, Clone)]
pub struct ConnectorName;

impl ConnectorCommon for ConnectorName {
    fn id(&self) -> &'static str {
        "connector_name"
    }
    
    fn base_url<'a>(&self, connectors: &'a Connectors) -> &'a str {
        connectors.connector_name.base_url.as_ref()
    }
    
    fn get_currency_unit(&self) -> api::CurrencyUnit {
        api::CurrencyUnit::Minor // or Base, depending on connector
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

#### Step 2.2: Authentication Implementation
```rust
#[derive(Debug, Clone)]
pub struct ConnectorNameAuthType {
    pub api_key: SecretSerdeValue,
    // Add other auth fields as needed
}

impl TryFrom<&ConnectorAuthType> for ConnectorNameAuthType {
    type Error = Error;
    
    fn try_from(auth_type: &ConnectorAuthType) -> Result<Self, Self::Error> {
        // Implementation for auth type conversion
    }
}
```

### Phase 3: Flow Implementation

> **📖 Pattern Reference:** For detailed implementation patterns, see:
> - **Authorization Flow**: `guides/patterns/pattern_authorize.md`
> - **Capture Flow**: `guides/patterns/pattern_capture.md`
> - **Refund Flow**: `guides/patterns/pattern_refund.md`
> - **Void Flow**: `guides/patterns/pattern_void.md`
> - **Psync Flow**: `guides/patterns/pattern_psync.md`
> - **Future flows**: Additional pattern files will be added for void, refund, sync, webhook, and dispute flows

#### Step 3.1: Authorize Flow
```rust
impl ConnectorIntegrationV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>
    for ConnectorName
{
    fn get_headers(
        &self,
        req: &RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>,
        connectors: &Connectors,
    ) -> CustomResult<Vec<(String, Maskable<String>)>, errors::ConnectorError> {
        // Implementation
    }
    
    fn get_content_type(&self) -> &'static str {
        self.common_get_content_type()
    }
    
    fn get_url(
        &self,
        req: &RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>,
        connectors: &Connectors,
    ) -> CustomResult<String, errors::ConnectorError> {
        // Build connector-specific URL
    }
    
    fn get_request_body(
        &self,
        req: &RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>,
        _connectors: &Connectors,
    ) -> CustomResult<RequestContent, errors::ConnectorError> {
        // Transform UCS data to connector format
        let connector_req = transformers::ConnectorNamePaymentsRequest::try_from(req)?;
        Ok(RequestContent::Json(Box::new(connector_req)))
    }
    
    fn build_request(
        &self,
        req: &RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>,
        connectors: &Connectors,
    ) -> CustomResult<Option<RequestDetails>, errors::ConnectorError> {
        // Build complete HTTP request
    }
    
    fn handle_response(
        &self,
        data: &RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>,
        event_builder: Option<&mut ConnectorEvent>,
        res: Response,
    ) -> CustomResult<RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>, errors::ConnectorError> {
        // Handle connector response and transform back to UCS format
    }
    
    fn get_error_response(
        &self,
        res: Response,
        event_builder: Option<&mut ConnectorEvent>,
    ) -> CustomResult<ErrorResponse, errors::ConnectorError> {
        self.build_error_response(res, event_builder)
    }
}
```

#### Step 3.2: Payment Method Handling
```rust
// In transformers.rs
impl TryFrom<&RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>>
    for ConnectorNamePaymentsRequest
{
    type Error = Error;
    
    fn try_from(
        item: &RouterDataV2<Authorize, PaymentsAuthorizeData, PaymentsResponseData>,
    ) -> Result<Self, Self::Error> {
        match item.request.payment_method_data.clone() {
            PaymentMethodData::Card(req_card) => {
                // Handle card payments
                Self::build_card_request(item, req_card)
            }
            PaymentMethodData::Wallet(wallet_data) => {
                // Handle wallet payments
                Self::build_wallet_request(item, wallet_data)
            }
            PaymentMethodData::BankTransfer(bank_data) => {
                // Handle bank transfers
                Self::build_bank_transfer_request(item, bank_data)
            }
            PaymentMethodData::BuyNowPayLater(bnpl_data) => {
                // Handle BNPL
                Self::build_bnpl_request(item, bnpl_data)
            }
            // Add all other payment method types
            _ => Err(errors::ConnectorError::NotImplemented(
                utils::get_unimplemented_payment_method_error_message("connector_name")
            ).into())
        }
    }
}
```

### Phase 4: Advanced Features

#### Step 4.1: Webhook Implementation
```rust
impl IncomingWebhook for ConnectorName {
    fn get_webhook_object_reference_id(
        &self,
        request: &IncomingWebhookRequestDetails<'_>,
    ) -> CustomResult<ObjectReferenceId, errors::ConnectorError> {
        // Extract payment/refund ID from webhook
    }
    
    fn get_webhook_event_type(
        &self,
        request: &IncomingWebhookRequestDetails<'_>,
    ) -> CustomResult<IncomingWebhookEvent, errors::ConnectorError> {
        // Map connector webhook events to UCS events
    }
    
    fn get_webhook_resource_object(
        &self,
        request: &IncomingWebhookRequestDetails<'_>,
    ) -> CustomResult<Box<dyn masking::ErasedMaskSerialize>, errors::ConnectorError> {
        // Parse webhook payload
    }
    
    fn get_dispute_details(
        &self,
        request: &IncomingWebhookRequestDetails<'_>,
    ) -> CustomResult<DisputePayload, errors::ConnectorError> {
        // Handle dispute webhooks if supported
    }
}
```

## 🧪 Testing Strategy

### Unit Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_payment_authorize_success() {
        // Test successful authorization for all payment methods
    }
    
    #[test]
    fn test_payment_authorize_failure() {
        // Test failure scenarios
    }
    
    // Add tests for all flows and payment methods
}
```

### Integration Tests
```rust
// File: backend/grpc-server/tests/connector_name_test.rs
// Comprehensive gRPC integration tests
```

## 🔄 Resuming Partial Implementation

### Common Resume Scenarios

#### "I have authorize working, need to add capture"
```bash
# AI Command: "add capture flow to existing [ConnectorName] connector in UCS"
# AI will:
# 1. Analyze existing authorize implementation
# 2. Use patterns from guides/patterns/pattern_capture.md
# 3. Create capture flow following same patterns
# 4. Ensure consistency with existing code style
```

#### "Need to add wallet support"
```bash
# AI Command: "add [WalletType] support to [ConnectorName] connector in UCS"
# AI will:
# 1. Analyze existing payment method handling
# 2. Add wallet-specific transformations
# 3. Update request/response structures
```

#### "Webhook implementation missing"
```bash
# AI Command: "implement webhook handling for [ConnectorName] connector in UCS"
# AI will:
# 1. Create webhook trait implementation
# 2. Add signature verification
# 3. Map webhook events to UCS events
```

## 🚨 Common UCS Pitfalls

### 1. RouterData vs RouterDataV2
```rust
// WRONG (traditional Hyperswitch)
RouterData<Flow, Request, Response>

// CORRECT (UCS)
RouterDataV2<Flow, Request, Response>
```

### 2. Trait Implementation
```rust
// WRONG (traditional)
ConnectorIntegration<Flow, Request, Response>

// CORRECT (UCS)
ConnectorIntegrationV2<Flow, Request, Response>
```

### 3. Error Handling
```rust
// UCS uses domain_types errors, not hyperswitch_domain_models
use domain_types::errors;
```

### 4. Import Paths
```rust
// UCS-specific imports
use domain_types::*;
use interfaces::connector_integration_v2::*;
// NOT hyperswitch_interfaces or hyperswitch_domain_models
```

## 📊 Implementation Checklist

### Core Implementation ✅
- [ ] Connector structure and auth
- [ ] Authorize flow
- [ ] Capture flow  
- [ ] Void flow
- [ ] Refund flow
- [ ] Payment sync
- [ ] Refund sync
- [ ] Error handling

### Payment Methods ✅
- [ ] Card payments (all networks)
- [ ] Digital wallets
- [ ] Bank transfers
- [ ] Buy Now Pay Later
- [ ] Crypto payments
- [ ] Regional methods
- [ ] Cash/voucher methods

### Advanced Features ✅
- [ ] Webhook implementation
- [ ] 3DS authentication
- [ ] Recurring/mandate setup
- [ ] Dispute handling
- [ ] Multi-currency support
- [ ] Partial capture/refund

### Quality & Testing ✅
- [ ] Unit tests for all flows
- [ ] Integration tests
- [ ] Error scenario testing
- [ ] Performance testing
- [ ] Documentation updates
- [ ] Code review ready

## 🎯 Success Metrics

A complete UCS connector implementation should:
1. **Support all relevant payment methods** for the connector
2. **Handle all core flows** (auth, capture, void, refund, sync)
3. **Process webhooks** if supported by connector
4. **Have comprehensive test coverage** (>90%)
5. **Follow UCS patterns** consistently
6. **Handle errors gracefully** with proper mapping
7. **Be production-ready** with proper logging and metrics

## 🔄 Continuous Integration

The UCS connector can be continuously improved:
- **Add new payment methods** as connector supports them
- **Implement new flows** as they become available
- **Optimize performance** based on usage patterns
- **Enhance error handling** based on production data
- **Update for API changes** as connector evolves

Remember: GRACE-UCS makes connector development resumable at any stage. You can always continue where you left off!