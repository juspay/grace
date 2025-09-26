# Connector Type Mappings - Summary Guide

## Overview

This guide summarizes type transformations between Hyperswitch's generic payment models and connector-specific formats. Each connector follows a similar pattern but with unique requirements.

## Core Type Transformation Pattern

### 1. Router Data Wrapper
Every connector uses a wrapper type to pair Hyperswitch data with formatted amounts:
```rust
pub struct ConnectorRouterData<T> {
    pub amount: AmountType, // MinorUnit, StringMinorUnit, f64, etc.
    pub router_data: T,
}
```

### 2. Authentication Types
```rust
// Common patterns
pub struct ConnectorAuthType {
    pub api_key: Secret<String>,
    pub merchant_id: Secret<String>,  // or merchant_account, entity_id
    pub api_secret: Secret<String>,   // optional for some
}
```

**Auth Type Mappings**:
- `ConnectorAuthType::HeaderKey` → API key in headers
- `ConnectorAuthType::BodyKey` → Multiple credentials
- `ConnectorAuthType::SignatureKey` → HMAC/signature-based auth

### 3. Amount Types
Different connectors expect different amount formats:
- **Minor Units** (cents): `MinorUnit`, `StringMinorUnit`
- **Major Units** (dollars): `StringMajorUnit`, `FloatMajorUnit`, `f64`
- **String Format**: Some APIs require amounts as strings

**Conversion Functions**:
```rust
// Minor to Major
utils::to_currency_base_unit(minor_amount_i64, currency)
// Amount formatting
utils::get_amount_as_f64(currency_unit, amount, currency)
// String conversion
StringMinorUnit::from(amount_i64)
```

**AmountConvertor Context**:
Be careful with MinorUnit vs StringMajorUnit conversions and make sure you understand the context of AmountConvertor.

## Common Request Transformations

### Payment Request Structure
```rust
pub struct ConnectorPaymentsRequest {
    // Common fields across connectors
    amount: AmountType,
    currency: Currency,
    payment_method: PaymentMethodDetails,
    reference: String, // connector_request_reference_id
    return_url: Option<String>,
    
    // Connector-specific fields
    merchant_account: Option<String>,
    browser_info: Option<BrowserInfo>,
    billing_address: Option<Address>,
    metadata: Option<HashMap<String, Value>>,
}
```

### Cancel Request Structure
```rust
pub struct ConnectorCancelRequest {
    // Use PaymentsCancelData, not PaymentsCaptureData for cancel operations
    transaction_id: String, // connector_transaction_id
    cancellation_reason: Option<String>,
    // Connector-specific fields
}
```

### Payment Method Types
```rust
pub enum PaymentMethodDetails {
    Card(CardDetails),
    Wallet(WalletDetails),
    BankRedirect(BankRedirectDetails),
    BankDebit(BankDebitDetails),
    PayLater(PayLaterDetails),
    Mandate(MandateDetails),
}
```

**Card Details**:
```rust
pub struct CardDetails {
    number: cards::CardNumber, // Hyperswitch type
    expiry_month: Secret<String>,
    expiry_year: Secret<String>,
    cvc: Secret<String>,
    card_holder_name: Secret<String>,
}
```

**Type mismatch**: Hyperswitch uses CardNumber but many connectors expect Secret<String>

**Wallet Types**:
- GooglePay → Base64 token or structured data
- ApplePay → Token or decrypted card data
- PayPal → Success/cancel URLs
- Others: AliPay, MBWay, SamsungPay

**Bank Redirects**:
- iDEAL, Sofort, EPS, Giropay
- Each may require issuer/bank selection

## Common Response Transformations

### Payment Response Structure
```rust
pub struct ConnectorPaymentsResponse {
    id: String, // Connector transaction ID
    status: ConnectorStatus,
    amount: Option<AmountType>,
    currency: Option<Currency>,
    
    // Optional fields
    redirect_url: Option<String>,
    reference_id: Option<String>,
    mandate_reference: Option<String>,
    network_transaction_id: Option<String>,
    error_details: Option<ErrorInfo>,
}
```

### Status Mappings

**Payment Status Mapping Pattern**:
```rust
Connector Status → Hyperswitch AttemptStatus
- "succeeded/approved/captured" → Charged
- "authorized" → Authorized (if manual capture) or Charged (if auto)
- "failed/declined/refused" → Failure
- "pending/processing" → Pending
- "requires_action/3ds_required" → AuthenticationPending
- "cancelled/voided" → Voided
```

**Refund Status Mapping**:
```rust
Connector Status → Hyperswitch RefundStatus
- "succeeded/completed" → Success
- "failed/declined" → Failure
- "pending/processing" → Pending
```

### Response ID Types
```rust
pub enum ResponseId {
    ConnectorTransactionId(String),
    EncodedData(String),
    NoResponseId,
}
```

## Special Flow Transformations

### 3D Secure (3DS)
```rust
// Request
pub struct ThreeDSecureData {
    browser_info: BrowserInfo,
    return_url: String,
    // Connector-specific 3DS fields
}

// Response
pub struct ThreeDSecureResponse {
    redirect_url: String,
    redirect_form: Option<RedirectForm>,
    session_data: Option<String>, // Stored in metadata
}
```

### Mandate/Tokenization
```rust
// Setup
pub struct SetupMandateRequest {
    customer_id: String,
    payment_method: PaymentMethodData,
    validation_mode: Option<String>,
}

// Usage
pub struct MandatePaymentInfo {
    mandate_id: String, // connector_mandate_id
    original_amount: Option<i64>,
}
```

### Webhook Events
```rust
// Common webhook event mappings
WebhookEventType → IncomingWebhookEvent
- "payment.authorized" → PaymentIntentSuccess
- "payment.captured" → PaymentIntentSuccess
- "refund.succeeded" → RefundSuccess
- "dispute.created" → DisputeOpened
```

## Key Type Locations in Hyperswitch

### From hyperswitch_domain_models
- `router_data::RouterData` - Main data carrier
- `router_request_types::{PaymentsAuthorizeData, RefundsData}`
- `router_response_types::{PaymentsResponseData, RefundsResponseData}`
- `payment_method_data::{PaymentMethodData, Card, WalletData}`

### From common_utils
- `pii::{Email, Secret}` - Sensitive data handling
- `types::{MinorUnit, StringMinorUnit}` - Amount types
- `request::{RequestContent, Method}` - HTTP request building

### From api_models/common_enums
- `enums::{AttemptStatus, RefundStatus, Currency}`
- `payments::{PaymentMethodType, PaymentMethod}`
- `webhooks::{IncomingWebhookEvent, ObjectReferenceId}`

## Transformation Patterns

### 1. TryFrom Pattern (Avoiding Orphan Rule)
```rust
// Always use ResponseRouterData wrapper
impl TryFrom<ResponseRouterData<F, ConnectorResp, Req, HyperswitchResp>>
    for RouterData<F, Req, HyperswitchResp>
{
    fn try_from(item: ResponseRouterData<...>) -> Result<Self, Error> {
        Ok(Self {
            status: map_status(item.response.status),
            response: Ok(HyperswitchResp {
                resource_id: ResponseId::ConnectorTransactionId(item.response.id),
                // Map other fields
            }),
            ..item.data // Spread original RouterData
        })
    }
}
```

### 2. Payment Method Transformation
```rust
match payment_method_data {
    PaymentMethodData::Card(card) => {
        ConnectorCard {
            number: card.card_number,
            exp_month: card.card_exp_month,
            exp_year: format_expiry_year(card.card_exp_year),
            cvv: card.card_cvc,
        }
    }
    PaymentMethodData::Wallet(wallet) => match wallet {
        WalletData::GooglePay(gpay) => // Handle Google Pay token
        WalletData::ApplePay(apple) => // Handle Apple Pay token
        _ => Err(NotImplemented("wallet type"))
    }
    PaymentMethodData::BankRedirect(bank) => // Handle bank redirects
    _ => Err(NotImplemented("payment method"))
}
```

### 3. Address Transformation
```rust
// Hyperswitch Address → Connector Address
Address {
    first_name: address.get_first_name()?,
    last_name: address.get_last_name()?,
    line1: address.get_line1()?,
    city: address.get_city()?,
    state: address.get_state()?,
    zip: address.get_zip()?,
    country: address.get_country()?,
}
```

### 4. Error Response Transformation
```rust
pub struct ConnectorErrorResponse {
    code: String,
    message: String,
    reason: Option<String>,
}

// Current ErrorResponse struct
pub struct ErrorResponse {
    pub code: String,
    pub message: String,
    pub reason: Option<String>,
    pub status_code: u16,
    pub attempt_status: Option<common_enums::enums::AttemptStatus>,
    pub connector_transaction_id: Option<String>,
    pub network_decline_code: Option<String>,
    pub network_advice_code: Option<String>,
    pub network_error_message: Option<String>,
}

// Transform to Hyperswitch ErrorResponse
ErrorResponse {
    status_code: res.status_code,
    code: error.code,
    message: error.message.clone(),
    reason: error.reason,
    attempt_status: Some(AttemptStatus::Failure),
    connector_transaction_id: None,
    network_decline_code: None,
    network_advice_code: None,
    network_error_message: None,
}
```

## Connector-Specific Patterns

### Two-Step Flows (e.g., Airwallex)
1. **PreProcessing**: Create payment intent → Returns intent_id
2. **Authorize**: Confirm payment using intent_id

### SOAP/XML Connectors (e.g., Bambora APAC)
- Serialize to XML strings
- Parse XML responses to structs
- Handle nested SOAP envelopes

### Split Payments (e.g., Adyen)
- Additional `splits` field in requests
- Split data in responses

### Instant Payments (e.g., Adyenplatform)
- Priority field mapping
- Real-time status tracking

## Common Enums

### Currency Units
```rust
pub enum CurrencyUnit {
    Minor, // Amounts in cents
    Base,  // Amounts in dollars
}
```

### Capture Methods
```rust
match capture_method {
    CaptureMethod::Automatic => "Sale",
    CaptureMethod::Manual => "Authorization",
}
```

### Payment Flows
```rust
pub enum PaymentFlow {
    Authorize,
    Capture,
    Void,
    PSync,    // Payment status sync
    RSync,    // Refund status sync
    Execute,  // Complete payment
    Preprocessing, // Setup before payment
}
```

## Best Practices

1. **Type Safety**: Use `Secret<T>` for sensitive data
2. **Amount Handling**: Always verify currency unit expectations
3. **Status Mapping**: Consider capture method when mapping statuses
4. **Error Context**: Preserve connector error details
5. **Metadata Storage**: Use for flow-specific data (3DS sessions, etc.)
6. **Null Handling**: Use `Option<T>` for optional fields
7. **String Formatting**: Match connector's expected formats (dates, amounts)

## Quick Reference

### Required Imports for Transformers
```rust
use common_utils::{
    ext_traits::ByteSliceExt,
    pii::{Email, Secret},
    types::{MinorUnit, StringMinorUnit},
};
use hyperswitch_domain_models::{
    payment_method_data::{Card, PaymentMethodData, WalletData},
    router_data::RouterData,
    router_request_types::PaymentsAuthorizeData,
    router_response_types::PaymentsResponseData,
};
use crate::types::{ResponseRouterData, ResponseId};
```

This guide provides a comprehensive overview of type transformations across all connectors, making it easier to implement new connectors or debug existing ones.
