# Connector Errors - AI Debugging Guide

## Import & Module Errors

### E0432: Unresolved Import
**Pattern:** `unresolved import` / `no X in module Y`
**Fix:** Check correct module path or add missing dependency to Cargo.toml
- Type aliases: Use `crate::types::TypeName` instead of direct paths
- External crates: Add to `[dependencies]` in Cargo.toml
- Common paths:
  - `hyperswitch_interfaces::consts` for constants (NO_ERROR_CODE)
  - `crate::utils` for traits and type aliases
  - `hyperswitch_domain_models::types` for domain types
  - `api_models` is separate crate, not in `hyperswitch_interfaces`
  - `common_utils::id_type` not `hyperswitch_domain_models::id_type`
  - Missing import: `base64::Engine` for base64 encoding operations
  - Missing import: `crate::utils::ExtTraits` for extended trait functionality
  - Missing import: `crate::utils::RefundsRequestData` for refund operations
  - Use `RouterData` from `hyperswitch_domain_models::router_data::RouterData`, not from other modules

### E0405/E0412: Type/Trait Not Found
**Pattern:** `cannot find type/trait X in scope`
**Fix:** Import from correct module:
- `RouterData`: `hyperswitch_domain_models::router_data::RouterData`
- Flow types: `hyperswitch_interfaces::api::{Authorize, PSync, Capture, Execute, RSync}`
- Request types: `hyperswitch_domain_models::router_request_types::{PaymentsAuthorizeData, RefundsData}`
- Traits: `hyperswitch_interfaces::types::{Capturable, Refundable}`
- `ConnectorTransactionIdType`: `hyperswitch_domain_models::types`

### E0433: Failed to Resolve
**Pattern:** `could not find X in Y`
**Fix:** Module doesn't exist where expected
- `api_models` is not in `hyperswitch_interfaces`, import directly

## Method & Field Errors

### E0599: Method Not Found
**Pattern:** `no method named X found`
**Fix:** Import required trait:
- Address methods: `use crate::utils::AddressDetailsData` (get_full_name, get_country)
- RouterData methods: `use crate::utils::RouterData as _` (get_webhook_url, get_email_for_connector)
- Request data methods: `use crate::utils::{PaymentsAuthorizeRequestData, RefundsRequestData}`
- Parse methods: `use common_utils::ext_traits::ByteSliceExt`
- String masking: `use masking::PeekInterface` (use `peek()` not `expose()` on references)
- Amount methods: `get_amount_as_i64()` on MinorUnit/StringMinorUnit
- Incorrect function name: Use `get_ip_address_as_optional()` not `get_optional_ip()`

### E0609: Field Not Found
**Pattern:** `no field X on type Y`
**Fix:** 
- For `RouterData` in `TryFrom`: Access via `item.response.field` not `item.field`
- For `ResponseRouterData`: Use `item.data` for original RouterData, `item.response` for response

### E0624: Private Function/Method
**Pattern:** `associated function is private`
**Fix:** Use public constructors
- `StringMinorUnit`: Use `From<i64>` or `From<&str>`, not private `new()`

## Type Mismatch Errors

### E0308: Type Mismatch
**Common cases:**
- `Email` vs `Secret<String, EmailStrategy>`: Use `get_email_for_connector()` on RouterData
- `Box<Option<T>>` expected: Wrap with `Box::new(Option<T>)`
- `HashMap<String, String>` vs `Map<String, Value>`: Convert JSON values to strings
- Amount types: Use consistent `i64` for minor units or proper conversion functions
- `MinorUnit` vs `StringMinorUnit`: Convert with `StringMinorUnit::from(amount.get_amount_as_i64().to_string())`

### E0277: Trait Bound Not Satisfied
**Common missing traits:**
- `Serialize`: Add `#[derive(serde::Serialize)]`
- `Default`: Add `#[derive(Default)]` or `#[default]` variant for enums
- `ErasedMaskSerialize`: Ensure struct derives `Serialize`
- Orphan rule: Use `crate::types::ResponseRouterData` wrapper for `TryFrom` implementations
- `Display` for ResponseId: Use `get_connector_transaction_id()` to get String

### E0117: Orphan Rule Violation
**Pattern:** `only traits defined in the current crate can be implemented`
**Fix:** Use `crate::types::ResponseRouterData` wrapper in TryFrom implementations

### E0107: Wrong Number of Generic Arguments
**Pattern:** `type alias takes X generic arguments but Y were supplied`
**Fix:** Check type alias definition and match generic count

### E0063: Missing Fields
**Pattern:** `missing fields in initializer`
**Fix:** Provide all required fields or set optional ones to `None`

## Connector-Specific Patterns

### RequestContent Variants
- Empty body: `RequestContent::Empty` (not `None` or `NoContent`)
- JSON: `RequestContent::Json(Box::new(serializable_struct))`
- Form: `RequestContent::FormUrlEncoded(HashMap<String, String>)`
- For signature with empty body: `RequestContent::Json(serde_json::Value::Null)`

### Amount Handling
- Use `CurrencyUnit::Minor` with `i64` amounts
- `StringMinorUnit`: Use public `From` implementations, not private `new()`
- Convert via `get_amount_as_i64()` when needed
- For major units: Use utility functions from `crate::utils`

### Response Handling
- Use `parse_struct::<T>()` on byte responses (requires `ByteSliceExt`)
- Handle `Result` types before accessing fields
- For redirects: Convert form fields to `HashMap<String, String>`
- ResponseId to String: Use `get_connector_transaction_id()`

### Authentication
- Test errors: Set `CONNECTOR_AUTH_FILE_PATH` environment variable
- Point to valid auth TOML with connector credentials

## Common Type Locations

### Request/Response Types
- `PaymentsAuthorizeData`: `hyperswitch_domain_models::router_request_types`
- `PaymentsResponseData`: `hyperswitch_domain_models::router_response_types`
- `RouterData`: `hyperswitch_domain_models::router_data`
- `ResponseRouterData`: `crate::types` (local wrapper)
- `AccessTokenResponseRouterData`: `hyperswitch_domain_models::types`
- `MandateReference`: `hyperswitch_domain_models::router_response_types`

### Trait Locations
- `ConnectorIntegration`: `hyperswitch_interfaces::api`
- `RouterRequest`: `hyperswitch_interfaces::api`
- Request data traits: `crate::utils`
- `AccessTokenAuthType`: `hyperswitch_interfaces::api::payments`
- `ResponseRouterDataCommon`: `hyperswitch_interfaces::types`

## Build Pattern

### Headers & Signatures
```rust
// For signature: serialize concrete struct to string
let request_str = serde_json::to_string(&concrete_struct)?;
// For body: box the struct
let request_content = RequestContent::Json(Box::new(concrete_struct));
// Use common_get_content_type() in build_request if get_headers is empty
```

### TryFrom Pattern
```rust
// Always use ResponseRouterData wrapper to avoid orphan rule
impl TryFrom<ResponseRouterData<F, ConnectorResp, Req, DomainResp>> 
    for RouterData<F, Req, DomainResp>
where
    Req: api::RouterRequest, // Add trait bounds if needed
{
    fn try_from(item: ResponseRouterData<...>) -> Result<Self, Error> {
        Ok(Self {
            response: Ok(/* construct DomainResp from item.response */),
            ..item.data // spread original RouterData fields
        })
    }
}
```

## Error Prevention
- No XML tags or metadata in file content
- Import traits before using their methods
- Use correct enum variants (check actual definition)
- Handle Results before field access
- Check field location (response vs data) in transformers
- Remove duplicate imports (E0252)
- Provide type annotations when compiler can't infer (E0283)
