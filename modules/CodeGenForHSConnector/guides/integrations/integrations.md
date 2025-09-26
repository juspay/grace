# Hyperswitch Connector Integration Guide

## Overview

A Hyperswitch connector integrates external payment processors. Each connector follows a standard two-file structure:
1. **`[connector_name].rs`** - Main logic and trait implementations
2. **`[connector_name]/transformers.rs`** - Data structures and transformations

## Quick Start

```bash
sh scripts/add_connector.sh [connector_name_lowercase] [base_url]
```

This creates boilerplate files in `crates/hyperswitch_connectors/src/connectors/`.

## Core Structure

### 1. Main Logic File (`[connector_name].rs`)

#### Required Components

```rust
// Module declaration
pub mod transformers;
use transformers as [connector_name];

// Connector struct
#[derive(Clone)]
pub struct [ConnectorName] {
    amount_converter: &'static (dyn AmountConvertor<Output = MinorUnit> + Sync),
}

impl [ConnectorName] {
    pub fn new() -> &'static Self {
        &Self {
            amount_converter: &MinorUnitForConnector, // Or &StringMajorUnitForConnector
        }
    }
}
```

#### Key Trait Implementations

##### ConnectorCommon
```rust
impl ConnectorCommon for [ConnectorName] {
    fn id(&self) -> &'static str { "[connector_name]" }
    
    fn get_currency_unit(&self) -> api::CurrencyUnit {
        api::CurrencyUnit::Minor // Or ::Base
    }
    
    fn common_get_content_type(&self) -> &'static str {
        "application/json" // Or "application/x-www-form-urlencoded"
    }
    
    fn base_url<'a>(&self, connectors: &Connectors) -> CustomResult<Url, errors::ConnectorError> {
        helpers::get_connector_url(connectors, self.id())
    }
    
    fn get_auth_header(&self, auth_type: &ConnectorAuthType) -> CustomResult<Vec<(String, Request)>, errors::ConnectorError> {
        let auth = [connector_name]::[ConnectorName]AuthType::try_from(auth_type)?;
        // Return auth headers based on connector's auth method
    }
    
    fn build_error_response(&self, res: Response, event_builder: Option<&mut ConnectorEventBuilder>) -> CustomResult<ErrorResponse, errors::ConnectorError> {
        let response: [connector_name]::[ConnectorName]ErrorResponse = res.response.parse_struct("[ConnectorName]ErrorResponse")?;
        // Map to ErrorResponse
    }
}
```

##### ConnectorIntegration for Each Flow
```rust
impl ConnectorIntegration<api::Authorize, PaymentsAuthorizeData, PaymentsResponseData> for [ConnectorName] {
    fn get_headers(&self, req: &PaymentsAuthorizeRouterData, connectors: &Connectors) -> CustomResult<Vec<(String, Request)>, errors::ConnectorError> {
        self.build_headers(req, connectors)
    }
    
    fn get_content_type(&self) -> &'static str {
        self.common_get_content_type()
    }
    
    fn get_url(&self, req: &PaymentsAuthorizeRouterData, connectors: &Connectors) -> CustomResult<String, errors::ConnectorError> {
        Ok(format!("{}/payments", self.base_url(connectors)?))
    }
    
    fn get_request_body(&self, req: &PaymentsAuthorizeRouterData, connectors: &Connectors) -> CustomResult<RequestContent, errors::ConnectorError> {
        let connector_router_data = [connector_name]::[ConnectorName]RouterData::from((
            self.amount_converter.convert(req.request.minor_amount, req.request.currency)?,
            req,
        ));
        let req_obj = [connector_name]::[ConnectorName]PaymentsRequest::try_from(&connector_router_data)?;
        Ok(RequestContent::Json(Box::new(req_obj)))
    }
    
    fn build_request(&self, req: &PaymentsAuthorizeRouterData, connectors: &Connectors) -> CustomResult<Option<Request>, errors::ConnectorError> {
        Ok(Some(
            RequestBuilder::new()
                .method(Method::Post)
                .url(&types::PaymentsAuthorizeType::get_url(self, req, connectors)?)
                .attach_default_headers()
                .headers(types::PaymentsAuthorizeType::get_headers(self, req, connectors)?)
                .set_body(types::PaymentsAuthorizeType::get_request_body(self, req, connectors)?)
                .build(),
        ))
    }
    
    fn handle_response(&self, data: &PaymentsAuthorizeRouterData, event_builder: Option<&mut ConnectorEventBuilder>, res: Response) -> CustomResult<PaymentsAuthorizeRouterData, errors::ConnectorError> {
        let response: [connector_name]::[ConnectorName]PaymentsResponse = res.response.parse_struct("[ConnectorName]PaymentsResponse")?;
        event_builder.map(|i| i.set_response_body(&response));
        RouterData::try_from(ResponseRouterData {
            response,
            data: data.clone(),
            http_code: res.status_code,
        })
    }
}
```

### 2. Transformers File (`[connector_name]/transformers.rs`)

#### Required Components

##### Helper Struct
```rust
#[derive(Debug, Serialize)]
pub struct [ConnectorName]RouterData<T> {
    pub amount: MinorUnit, // Or appropriate amount type
    pub router_data: T,
}

impl<T> From<(MinorUnit, T)> for [ConnectorName]RouterData<T> {
    fn from((amount, router_data): (MinorUnit, T)) -> Self {
        Self { amount, router_data }
    }
}
```

##### Authentication Type
```rust
pub struct [ConnectorName]AuthType {
    pub(super) api_key: Secret<String>,
    pub(super) merchant_id: Secret<String>,
}

impl TryFrom<&ConnectorAuthType> for [ConnectorName]AuthType {
    type Error = error_stack::Report<errors::ConnectorError>;
    
    fn try_from(auth_type: &ConnectorAuthType) -> Result<Self, Self::Error> {
        match auth_type {
            ConnectorAuthType::BodyKey { api_key, key1 } => Ok(Self {
                api_key: api_key.clone(),
                merchant_id: key1.clone(),
            }),
            _ => Err(errors::ConnectorError::FailedToObtainAuthType)?,
        }
    }
}
```

##### Request Structures
```rust
#[derive(Debug, Clone, Serialize)]
pub struct [ConnectorName]PaymentsRequest {
    amount: MinorUnit,
    currency: enums::Currency,
    #[serde(flatten)]
    payment_method: PaymentMethodData,
    // Other fields as per API
}

impl TryFrom<&[ConnectorName]RouterData<&PaymentsAuthorizeRouterData>> for [ConnectorName]PaymentsRequest {
    type Error = error_stack::Report<errors::ConnectorError>;
    
    fn try_from(item: &[ConnectorName]RouterData<&PaymentsAuthorizeRouterData>) -> Result<Self, Self::Error> {
        let payment_method = match &item.router_data.request.payment_method_data {
            PaymentMethodData::Card(card) => PaymentMethodData::Card(CardData {
                number: card.card_number.clone(),
                expiry_month: card.card_exp_month.clone(),
                expiry_year: card.card_exp_year.clone(),
                cvv: card.card_cvc.clone(),
            }),
            PaymentMethodData::Wallet(wallet_data) => // Handle wallet types
            PaymentMethodData::BankRedirect(bank_data) => // Handle bank redirects
            _ => Err(errors::ConnectorError::NotImplemented("Payment method"))?,
        };
        
        Ok(Self {
            amount: item.amount.clone(),
            currency: item.router_data.request.currency,
            payment_method,
        })
    }
}
```

##### Response Structures
```rust
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct [ConnectorName]PaymentsResponse {
    id: String,
    status: PaymentStatus,
    amount: MinorUnit,
    // Other fields as per API
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PaymentStatus {
    Succeeded,
    Failed,
    Pending,
    Authorized,
}

impl From<PaymentStatus> for enums::AttemptStatus {
    fn from(status: PaymentStatus) -> Self {
        match status {
            PaymentStatus::Succeeded => Self::Charged,
            PaymentStatus::Failed => Self::Failure,
            PaymentStatus::Pending => Self::Pending,
            PaymentStatus::Authorized => Self::Authorized,
        }
    }
}

impl<F, T> TryFrom<ResponseRouterData<F, [ConnectorName]PaymentsResponse, T, PaymentsResponseData>>
    for RouterData<F, T, PaymentsResponseData>
{
    type Error = error_stack::Report<errors::ConnectorError>;
    
    fn try_from(item: ResponseRouterData<F, [ConnectorName]PaymentsResponse, T, PaymentsResponseData>) -> Result<Self, Self::Error> {
        Ok(Self {
            status: enums::AttemptStatus::from(item.response.status.clone()),
            response: Ok(PaymentsResponseData::TransactionResponse {
                resource_id: ResponseId::ConnectorTransactionId(item.response.id.clone()),
                redirection_data: Box::new(None),
                mandate_reference: Box::new(None),
                connector_metadata: None,
                network_txn_id: None,
                connector_response_reference_id: None,
                incremental_authorization_allowed: None,
                charge_id: None,
            }),
            ..item.data
        })
    }
}
```

## Common Patterns

### Authentication Methods

#### Basic Auth
```rust
let auth_string = format!("{}:{}", username.expose(), password.expose());
let encoded = base64::engine::general_purpose::STANDARD.encode(auth_string.as_bytes());
Ok(vec![(headers::AUTHORIZATION.to_string(), format!("Basic {encoded}").into_masked())])
```

#### Bearer Token
```rust
Ok(vec![(headers::AUTHORIZATION.to_string(), format!("Bearer {}", api_key.expose()).into_masked())])
```

#### Custom Headers
```rust
Ok(vec![("X-API-KEY".to_string(), api_key.expose().into_masked())])
```

#### Signature-Based
```rust
// HMAC-SHA256 example
let message = format!("{}{}{}", timestamp, method, path);
let signature = crypto::HmacSha256::sign_message(
    secret.expose().as_bytes(),
    message.as_bytes(),
)?;
let signature_hex = hex::encode(signature);
```

### Amount Handling

#### Minor Units (cents)
- Use `MinorUnitForConnector` or `StringMinorUnitForConnector`
- Currency unit: `api::CurrencyUnit::Minor`

#### Major Units (dollars)
- Use `StringMajorUnitForConnector` or `FloatMajorUnitForConnector`
- Currency unit: `api::CurrencyUnit::Base`

### Payment Method Handling

```rust
match &item.router_data.request.payment_method_data {
    PaymentMethodData::Card(card) => {
        // Handle card payments
    }
    PaymentMethodData::Wallet(wallet) => match wallet {
        WalletData::GooglePay(gpay) => // Handle Google Pay
        WalletData::ApplePay(apple) => // Handle Apple Pay
        WalletData::Paypal(_) => // Handle PayPal
        _ => Err(errors::ConnectorError::NotImplemented("Wallet type"))?,
    }
    PaymentMethodData::BankRedirect(redirect) => match redirect {
        BankRedirectData::Ideal { .. } => // Handle iDEAL
        BankRedirectData::Sofort { .. } => // Handle Sofort
        _ => Err(errors::ConnectorError::NotImplemented("Bank redirect"))?,
    }
    PaymentMethodData::PayLater(paylater) => match paylater {
        PayLaterData::Klarna { .. } => // Handle Klarna
        _ => Err(errors::ConnectorError::NotImplemented("PayLater method"))?,
    }
    _ => Err(errors::ConnectorError::NotImplemented("Payment method"))?,
}
```

### Webhook Implementation

```rust
impl webhooks::IncomingWebhook for [ConnectorName] {
    fn get_webhook_source_verification_algorithm(&self, _request: &IncomingWebhookRequestDetails<'_>) -> CustomResult<Box<dyn crypto::VerifySignature + Send>, errors::ConnectorError> {
        Ok(Box::new(crypto::HmacSha256))
    }
    
    fn get_webhook_source_verification_signature(&self, request: &IncomingWebhookRequestDetails<'_>, connector_webhook_secrets: &api_models::webhooks::ConnectorWebhookSecrets) -> CustomResult<Vec<u8>, errors::ConnectorError> {
        let signature = get_header_key_value("x-signature", request.headers)?;
        hex::decode(signature).change_context(errors::ConnectorError::WebhookSignatureNotFound)
    }
    
    fn get_webhook_source_verification_message(&self, request: &IncomingWebhookRequestDetails<'_>, merchant_id: &id_type::MerchantId, connector_webhook_secrets: &api_models::webhooks::ConnectorWebhookSecrets) -> CustomResult<Vec<u8>, errors::ConnectorError> {
        Ok(request.body.as_bytes().to_vec())
    }
    
    fn get_webhook_object_reference_id(&self, request: &IncomingWebhookRequestDetails<'_>) -> CustomResult<api_models::webhooks::ObjectReferenceId, errors::ConnectorError> {
        let webhook: [ConnectorName]Webhook = request.body.parse_struct("[ConnectorName]Webhook")?;
        match webhook.event_type {
            WebhookEventType::PaymentAuthorized => Ok(ObjectReferenceId::PaymentId(PaymentIdType::ConnectorTransactionId(webhook.transaction_id))),
            WebhookEventType::RefundCompleted => Ok(ObjectReferenceId::RefundId(RefundIdType::ConnectorRefundId(webhook.refund_id))),
        }
    }
}
```

## Integration Workflow

### 1. API Analysis
- Authentication mechanism
- Endpoints and paths
- Request/response formats
- Error structures
- Amount units
- Webhook verification

### 2. Implementation Steps
1. Generate boilerplate: `sh scripts/add_connector.sh [name] [url]`
2. Implement transformers:
   - Define request/response structs
   - Implement TryFrom conversions
   - Map status enums
3. Implement main logic:
   - ConnectorCommon trait
   - ConnectorIntegration for each flow
   - Webhook handling if supported
4. Update enums in `crates/common_enums/src/connector_enums.rs`
5. Add configuration to `crates/connector_configs/toml/development.toml`
6. Write tests in `crates/router/tests/connectors/`

### 3. Testing
- Add credentials to `crates/router/tests/connectors/sample_auth.toml`
- Run: `cargo test --package router --test connectors -- [connector_name]`

## Common Types Reference

### From hyperswitch_domain_models
- `router_data::RouterData` - Main data carrier
- `router_request_types::{PaymentsAuthorizeData, RefundsData}`
- `router_response_types::{PaymentsResponseData, RefundsResponseData}`
- `payment_method_data::{PaymentMethodData, Card, WalletData}`

### From common_utils
- `pii::{Email, Secret}` - For sensitive data
- `types::{MinorUnit, StringMinorUnit}` - Amount types
- `request::{RequestContent, RequestBuilder}` - Request building

### From hyperswitch_interfaces
- `api::{ConnectorCommon, ConnectorIntegration}` - Core traits
- `errors::ConnectorError` - Error types

## Error Handling

### Common Errors
- `MissingRequiredField` - Required field not provided
- `NotImplemented` - Feature/payment method not supported
- `InvalidDataFormat` - Parsing/conversion failure
- `RequestEncodingFailed` - Serialization failure

### Error Response
```rust
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct [ConnectorName]ErrorResponse {
    pub code: String,
    pub message: String,
    pub reason: Option<String>,
}
```

## Best Practices

1. **Separation of Concerns**: Keep data structures in transformers, logic in main file
2. **Type Safety**: Use appropriate types (Secret, Email, etc.) for sensitive data
3. **Error Context**: Add context to errors for debugging
4. **Idempotency**: Include idempotency keys where supported
5. **Metadata Storage**: Use connector_metadata for flow-specific data
6. **Status Mapping**: Map all possible connector statuses to Hyperswitch enums
7. **Payment Method Support**: Implement only supported payment methods, return NotImplemented for others

## Key Differences Between Connectors

- **Currency Units**: Minor (cents) vs Base (dollars)
- **Authentication**: Basic, Bearer, API Key, Signature-based
- **Request Format**: JSON vs Form-encoded
- **Flow Patterns**: Direct vs Two-step (create intent, then confirm)
- **Webhook Verification**: HMAC-SHA256, SHA1, custom endpoints
- **3DS Handling**: Redirect vs SDK integration
- **Mandate Support**: Token storage patterns vary
