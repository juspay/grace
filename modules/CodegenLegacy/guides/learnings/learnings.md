# Connector Development Learnings - Comprehensive Guide

## Core Concepts

### 1. Type System & Imports

#### Common Import Patterns
```rust
// Core types
use hyperswitch_domain_models::router_data::RouterData;
use hyperswitch_interfaces::api::{self, ConnectorCommon, ConnectorIntegration};
use common_utils::{pii::Email, types::{MinorUnit, StringMinorUnit}};

// Type aliases to avoid confusion
use hyperswitch_domain_models::types as hyperswitch_types;
use hyperswitch_interfaces::types as connector_types;
use crate::types::ResponseRouterData; // Local wrapper for TryFrom
```

#### Key Type Locations
- **RouterData wrappers**: `hyperswitch_domain_models::types` (PaymentsAuthorizeRouterData, etc.)
- **Request/Response types**: `hyperswitch_domain_models::router_request_types` and `router_response_types`
- **Flow types**: `hyperswitch_interfaces::api` (Authorize, PSync, Capture, Execute, RSync)
- **Traits**: `hyperswitch_interfaces::types` (Capturable, Refundable)
- **ResponseRouterData**: `crate::types` (local wrapper to avoid orphan rule)
- **Constants**: `hyperswitch_interfaces::consts` (NO_ERROR_CODE, NO_ERROR_MESSAGE)
- **id_type module**: `common_utils::id_type` (not `hyperswitch_domain_models::id_type`)

### 2. Authentication Patterns

#### HTTP Basic Auth
```rust
let auth_string = format!("{}:{}", username.expose(), password.expose());
let encoded = base64::engine::general_purpose::STANDARD.encode(auth_string.as_bytes());
Ok(vec![(headers::AUTHORIZATION.to_string(), format!("Basic {encoded}").into_masked())])
```

#### Bearer Token
```rust
Ok(vec![(headers::AUTHORIZATION.to_string(), format!("Bearer {}", api_key.expose()).into_masked())])
```

#### HMAC Signature
```rust
// Use peek() for references, expose() for owned values
let signature = crypto::HmacSha256::sign_message(
    secret_key.peek().as_bytes(), // peek() for &Secret<String>
    message.as_bytes(),
)?;
let signature_hex = hex::encode(signature);
```

#### Dlocal HMAC Pattern
```rust
// Build headers in ConnectorCommonExt::build_headers
fn build_headers(&self, req: &RouterData<...>, _connectors: &Connectors) -> CustomResult<Vec<(String, Maskable<String>)>, errors::ConnectorError> {
    let auth = DlocalAuthType::try_from(&req.connector_auth_type)?;
    let timestamp = date_time::now();
    
    // Get request body string
    let request_content = self.get_request_body(req, _connectors)?;
    let body_string = match request_content {
        Some(RequestContent::Json(body)) => body.peek().to_string(),
        Some(RequestContent::FormUrlEncoded(form)) => form.peek().to_string(),
        _ => String::new(),
    };
    
    // Build signature: X-Login + X-Date + RequestBody
    let to_sign = format!("{}{}{}", auth.x_login, timestamp, body_string);
    let signature = crypto::HmacSha256::sign_message(
        auth.secret_key.peek().as_bytes(),
        to_sign.as_bytes(),
    )?;
    
    let headers = vec![
        ("X-Login".to_string(), auth.x_login.into_masked()),
        ("X-Trans-Key".to_string(), auth.x_trans_key.into_masked()),
        ("X-Date".to_string(), timestamp.to_string().into()),
        ("X-Version".to_string(), "2.1".into()),
        ("Authorization".to_string(), format!("V2-HMAC-SHA256, Signature: {}", hex::encode(signature)).into()),
    ];
    Ok(headers)
}
```

#### Key Learning: Always use `PeekInterface` for `&Secret<T>` to avoid move errors.

### 3. Amount Handling

#### Currency Units
- **Minor Units** (cents): Use `MinorUnit` or `StringMinorUnit`
  - `get_currency_unit()` returns `api::CurrencyUnit::Minor`
- **Major Units** (dollars): Use `StringMajorUnit` or `FloatMajorUnit`
  - `get_currency_unit()` returns `api::CurrencyUnit::Base`

#### Conversion Patterns
```rust
// Minor to Major (i64 cents to f64 dollars)
let amount_f64 = utils::to_currency_base_unit(minor_amount_i64, currency)?;

// Using helper struct for amount conversion
pub struct ConnectorRouterData<T> {
    pub amount: MinorUnit, // Or appropriate type
    pub router_data: T,
}

// StringMinorUnit construction (new() is private)
// DON'T: StringMinorUnit::new(amount_string)
// DO: StringMinorUnit::from(amount_i64) or StringMinorUnit::from(amount_string)
```

#### Bambora/Airwallex Pattern
```rust
// In transformers.rs
impl TryFrom<(&api::CurrencyUnit, Currency, i64, &PaymentsAuthorizeRouterData)> 
    for BamboraRouterData<&PaymentsAuthorizeRouterData> {
    fn try_from((currency_unit, currency, amount, item): (&api::CurrencyUnit, Currency, i64, &PaymentsAuthorizeRouterData)) -> Result<Self, Self::Error> {
        Ok(Self {
            amount: utils::get_amount_as_f64(currency_unit, amount, currency)?, // Converts to f64
            router_data: item,
        })
    }
}
```

#### Key Learning: Connector's `get_currency_unit()` should match what the API expects, not Hyperswitch's internal representation.

### 4. Request/Response Transformations

#### TryFrom Pattern (Avoiding Orphan Rule)
```rust
// Use local ResponseRouterData wrapper
impl TryFrom<ResponseRouterData<F, ConnectorResponse, Req, DomainResponse>>
    for RouterData<F, Req, DomainResponse>
{
    fn try_from(item: ResponseRouterData<...>) -> Result<Self, Error> {
        Ok(Self {
            response: Ok(DomainResponse {
                // Map from item.response (connector-specific)
            }),
            ..item.data // Spread original RouterData fields
        })
    }
}
```

#### Request Body Construction
```rust
// 1. Create concrete request struct
let connector_req = ConnectorPaymentsRequest::try_from(&connector_router_data)?;

// 2. For signature: serialize to string
let request_str = serde_json::to_string(&connector_req)?;

// 3. For body: box the struct
Ok(RequestContent::Json(Box::new(connector_req)))
```

#### Empty Request Body Patterns
```rust
// For GET requests
// Simply don't call .set_body() on RequestBuilder

// For POST with no body
Ok(RequestContent::Empty)

// For POST with empty JSON object (e.g., Airwallex login)
#[derive(Debug, Serialize)]
pub struct EmptyRequest {}
Ok(RequestContent::Json(Box::new(EmptyRequest {})))
```

### 5. Common Patterns & Best Practices

#### Connector Metadata Usage
```rust
// For merchant-specific config beyond auth
let gateway_token = req.connector_meta_data
    .as_ref()
    .and_then(|meta| meta.peek().as_object())
    .and_then(|obj| obj.get("gateway_token"))
    .and_then(|token| token.as_str())
    .ok_or(errors::ConnectorError::MissingRequiredField { 
        field_name: "gateway_token" 
    })?;

// Storing intermediate data
#[derive(Debug, Serialize, Deserialize)]
pub struct ConnectorMeta {
    pub authorize_id: Option<String>,
    pub capture_id: Option<String>,
    pub three_d_session_data: Option<String>,
}
```

#### Transaction Token Management
- Store connector transaction IDs as `ConnectorTransactionId`
- Use for subsequent operations (capture, refund, sync)
- Pattern: Authorize → token → Use in Capture/Refund/Sync URLs

```rust
// Getting transaction ID for sync
let payment_id = req.request.get_connector_transaction_id()?;

// Getting transaction ID from ResponseId
let payment_id_str = req.request.connector_transaction_id
    .get_connector_transaction_id()
    .change_context(errors::ConnectorError::MissingConnectorTransactionID)?;
```

#### Status Mapping
```rust
// Multi-field status determination (Spreedly pattern)
match (transaction_type.as_str(), succeeded) {
    ("Authorize", true) => AttemptStatus::Authorized,
    ("Capture", true) => AttemptStatus::Charged,
    (_, false) => AttemptStatus::Failure,
    _ => AttemptStatus::Pending,
}

// Enum-based mapping (common pattern)
impl From<ConnectorPaymentStatus> for AttemptStatus {
    fn from(status: ConnectorPaymentStatus) -> Self {
        match status {
            ConnectorPaymentStatus::Succeeded => Self::Charged,
            ConnectorPaymentStatus::Authorized => Self::Authorized,
            ConnectorPaymentStatus::Failed => Self::Failure,
            ConnectorPaymentStatus::Pending => Self::Pending,
        }
    }
}
```

### 6. Common Pitfalls & Solutions

#### Type/Trait Not Found
- **Problem**: `cannot find type X in scope`
- **Solution**: Check correct module path, use full paths or proper imports
- **Example**: `PaymentIdType` is in `api_models::payments`, not `hyperswitch_domain_models::types`

#### Method Not Found
- **Problem**: `no method named get_email_for_connector`
- **Solution**: Import required trait: `use crate::utils::RouterData as _;`
- **Example Methods**:
  - `get_billing_address()`, `get_optional_billing_full_name()` - from `RouterData` trait
  - `get_full_name()`, `get_country()` - from `AddressDetailsData` trait
  - `get_connector_refund_id()` - from `RefundsRequestData` trait
  - `parse_struct()` - from `ByteSliceExt` trait

#### Field Access in TryFrom
- **Problem**: Accessing `item.id` instead of `item.response.id`
- **Solution**: Use `item.response` for connector data, `item.data` for original RouterData
- **Pattern**:
  ```rust
  resource_id: ResponseId::ConnectorTransactionId(item.response.id.clone()),
  connector_response_reference_id: item.response.order_id.clone(),
  ..item.data // Spread from original RouterData
  ```

#### StringMinorUnit Construction
- **Problem**: `StringMinorUnit::new()` is private
- **Solution**: Use `From` implementations: `StringMinorUnit::from(value)`

#### RequestContent for Empty Body
- **Problem**: No variant `RequestContent::None` or `RequestContent::NoContent`
- **Solution**: Use `RequestContent::Empty` or don't call `set_body()`

#### Boxed Options
- **Problem**: `expected Box<Option<T>>, found Option<_>`
- **Solution**: Wrap with `Box::new()`: `redirection_data: Box::new(None)`

### 7. Webhook Implementation

#### HMAC Verification Pattern
```rust
fn verify_webhook_source(&self, request: &IncomingWebhookRequestDetails<'_>, 
    secrets: &ConnectorWebhookSecrets) -> CustomResult<(), ConnectorError> {
    let signature = get_header_key_value("x-signature", request.headers)?;
    let expected = crypto::HmacSha256::sign_message(
        webhook_secret.expose().as_bytes(),
        request.body.as_bytes(),
    )?;
    let expected_str = hex::encode(expected);
    
    if signature != expected_str {
        return Err(ConnectorError::WebhookSourceVerificationFailed.into());
    }
    Ok(())
}
```

#### Event Type Mapping
```rust
fn get_webhook_event_type(&self, request: &IncomingWebhookRequestDetails<'_>) -> CustomResult<IncomingWebhookEvent, ConnectorError> {
    let webhook: ConnectorWebhook = request.body.parse_struct("ConnectorWebhook")?;
    
    match webhook.event_type.as_str() {
        "payment.authorized" => Ok(IncomingWebhookEvent::PaymentIntentAuthorizationSuccess),
        "payment.captured" => Ok(IncomingWebhookEvent::PaymentIntentSuccess),
        "refund.completed" => Ok(IncomingWebhookEvent::RefundSuccess),
        _ => Ok(IncomingWebhookEvent::EventNotSupported),
    }
}
```

### 8. Architecture Insights

#### Two-File Pattern
- **Main file** (`connector.rs`): Logic and trait implementations
- **Transformers** (`connector/transformers.rs`): Data structures and conversions

#### Helper Struct Pattern
```rust
pub struct ConnectorRouterData<T> {
    pub amount: MinorUnit,
    pub router_data: T,
}

impl<T> From<(MinorUnit, T)> for ConnectorRouterData<T> {
    fn from((amount, router_data): (MinorUnit, T)) -> Self {
        Self { amount, router_data }
    }
}
```

#### Name Splitting Pattern
```rust
let parts: Vec<&str> = name.peek().split_whitespace().collect();
let first_name = parts.first().map(|s| Secret::new(s.to_string()))
    .unwrap_or_else(|| Secret::new("".to_string()));
let last_name = if parts.len() > 1 {
    Some(Secret::new(parts[1..].join(" ")))
} else {
    None
}.unwrap_or_else(|| Secret::new("".to_string()));
```

#### ConnectorSpecifications Pattern
```rust
lazy_static! {
    static ref CONNECTOR_SUPPORTED_PAYMENT_METHODS: SupportedPaymentMethods = 
        SupportedPaymentMethods(HashMap::from([
            (enums::PaymentMethod::Card, 
             PaymentMethodDetails {
                 payment_method_type: vec![
                     PaymentMethodTypeDetails {
                         payment_method_type: enums::PaymentMethodType::Credit,
                         card_networks: vec![enums::CardNetwork::Visa, enums::CardNetwork::Mastercard],
                         // ... other details
                     }
                 ],
             }
            ),
        ]));
}

impl ConnectorSpecifications for Connector {
    fn get_supported_payment_methods(&self) -> Option<&'static SupportedPaymentMethods> {
        Some(&*CONNECTOR_SUPPORTED_PAYMENT_METHODS)
    }
}
```

## Connector-Specific Patterns

### Airwallex (Two-Step Flow)
```rust
// PreProcessing: Create payment intent
let intent_request = AirwallexIntentRequest {
    amount: utils::to_currency_base_unit(req.request.amount, req.request.currency)?,
    currency: req.request.currency,
    // ...
};
// Returns intent_id stored in RouterData.reference_id

// Authorize: Confirm payment intent
fn get_url(&self, req: &PaymentsAuthorizeRouterData, connectors: &Connectors) -> CustomResult<String, ConnectorError> {
    let intent_id = req.reference_id.clone()
        .ok_or(errors::ConnectorError::MissingRequiredField { field_name: "reference_id" })?;
    Ok(format!("{}/payment_intents/{}/confirm", self.base_url(connectors)?, intent_id))
}
```

### Bambora (3DS Handling)
```rust
// Response enum for 3DS
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(untagged)]
pub enum BamboraResponse {
    Response(BamboraPaymentsResponse),
    ThreeDResponse(BamboraThreeDResponse),
}

// CompleteAuthorize for 3DS
fn get_url(&self, req: &PaymentsCompleteAuthorizeRouterData, connectors: &Connectors) -> CustomResult<String, ConnectorError> {
    let three_d_session_data = req.request.connector_meta
        .as_ref()
        .and_then(|meta| meta.peek().get("three_d_session_data"))
        .ok_or(errors::ConnectorError::MissingRequiredField { field_name: "three_d_session_data" })?;
    
    Ok(format!("{}/v1/payments/{}/continue", self.base_url(connectors)?, three_d_session_data))
}
```

### Access Token Flow Pattern
```rust
// AccessTokenAuth implementation
impl ConnectorIntegration<AccessTokenAuth, AccessTokenRequestData, AccessToken> for Connector {
    fn build_request(&self, req: &RefreshTokenRouterData, connectors: &Connectors) -> CustomResult<Option<Request>, ConnectorError> {
        Ok(Some(
            RequestBuilder::new()
                .method(Method::Post)
                .url(&self.get_url(req, connectors)?)
                .attach_default_headers()
                .headers(vec![
                    ("X-API-KEY".to_string(), auth.api_key.expose().into_masked()),
                    ("X-CLIENT-ID".to_string(), auth.client_id.expose().into_masked()),
                ])
                .set_body(RequestContent::Json(Box::new(EmptyRequest {})))
                .build(),
        ))
    }
    
    fn handle_response(&self, data: &RefreshTokenRouterData, res: Response) -> CustomResult<RefreshTokenRouterData, ConnectorError> {
        let response: AirwallexAuthUpdateResponse = res.response.parse_struct("AirwallexAuthUpdateResponse")?;
        
        Ok(RefreshTokenRouterData {
            response: Ok(AccessToken {
                token: response.token,
                expires: response.expires_at - date_time::now().whole_seconds(),
            }),
            access_token: Some(AccessToken {
                token: response.token,
                expires: response.expires_at - date_time::now().whole_seconds(),
            }),
            ..data.clone()
        })
    }
}
```

## Quick Reference Checklist

### When Starting a New Connector
1. ✓ Check authentication method (Basic, Bearer, HMAC, OAuth)
2. ✓ Verify amount units (Minor vs Major)
3. ✓ Check request format (JSON vs Form-encoded)
4. ✓ Note API versioning in URLs (e.g., `/v1/`)
5. ✓ Identify transaction ID patterns
6. ✓ Map all status codes/strings
7. ✓ Check webhook verification method
8. ✓ Check for two-step flows (create intent → confirm)
9. ✓ Verify 3DS requirements
10. ✓ Check refund/void endpoint patterns

### Common Fixes
- **Import errors**: Use full module paths or correct aliases
- **Method not found**: Import required traits from `crate::utils`
- **Type mismatch**: Check if using correct Secret/Email types
- **Amount issues**: Verify currency unit expectations
- **Auth failures**: Check Base64 encoding, header format
- **Webhook failures**: Verify signature algorithm, message construction
- **Missing fields**: Check for required metadata or transaction IDs

### Testing Considerations
- Mock any required metadata (gateway tokens, etc.)
- Use test cards (usually 4111111111111111)
- Include complete address/email data
- Test all flows: authorize, capture, refund, void, sync
- Test both success and failure scenarios
- Test 3DS flows if supported
- Verify webhook handling

## Key Takeaways

1. **Type Safety**: Use appropriate types (Secret, Email) for sensitive data
2. **Error Context**: Always add context to errors for debugging
3. **Simplicity**: Don't over-engineer; match API simplicity
4. **Consistency**: Follow established patterns from other connectors
5. **Documentation**: Read API docs thoroughly before implementation
6. **Testing**: Test entire payment lifecycle with realistic data
7. **Pattern Recognition**: Most connectors follow similar patterns - identify and reuse
8. **Trait Imports**: Many methods come from traits that need explicit imports