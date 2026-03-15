# Connector Implementation Checklist

Post-implementation validation checklist for UCS connector integrations. Run through this after completing a connector to verify completeness and correctness.

---

## How to Use

After implementing a connector (via `integrate_connector.md`, `add_flow.md`, or `add_pm.md`), go through each section below. For each item:

- **Pass** -- The requirement is met
- **Fail** -- The requirement is not met (fix before marking complete)
- **N/A** -- Not applicable for this connector (document why)

---

## 1. Build

- [ ] `cargo build` succeeds with zero errors
- [ ] No warnings related to connector code (unused imports, dead code, etc.)
- [ ] All new files are in the correct directory structure:
  ```
  backend/connector-integration/src/connectors/{connector_name}.rs
  backend/connector-integration/src/connectors/{connector_name}/transformers.rs
  ```

## 2. Foundation

- [ ] `ConnectorCommon` trait implemented with correct `id()`, `base_url()`, `get_currency_unit()`
- [ ] `common_get_content_type()` returns the correct content type for this connector's API
- [ ] `build_error_response()` handles all documented error response formats
- [ ] Connector registered in the connector enum / mod.rs
- [ ] All code uses `RouterDataV2`, NOT legacy `RouterData`
- [ ] Imports use `domain_types` crate (NOT `hyperswitch_domain_models`)

## 3. Flows

For each implemented flow, verify:

### Authorize
- [ ] `ConnectorIntegrationV2<Authorize, ...>` implemented
- [ ] `get_headers()` includes all required authentication and content-type headers
- [ ] `get_url()` builds the correct endpoint URL
- [ ] `get_request_body()` transforms UCS `PaymentsAuthorizeData` to connector format
- [ ] `handle_response()` correctly maps connector response to UCS `PaymentsResponseData`
- [ ] `get_error_response()` handles error cases
- [ ] Status mapping: connector statuses correctly mapped to UCS `AttemptStatus`

### PSync (Payment Status Sync)
- [ ] `ConnectorIntegrationV2<PSync, ...>` implemented
- [ ] Uses correct GET endpoint with transaction ID
- [ ] Response parsing handles all possible payment states

### Capture
- [ ] `ConnectorIntegrationV2<Capture, ...>` implemented
- [ ] Correctly references the authorization ID from the previous Authorize response
- [ ] Supports partial capture (if documented by connector)

### Refund
- [ ] `ConnectorIntegrationV2<Refund, ...>` implemented
- [ ] Correctly references the payment/capture ID
- [ ] Supports partial refund (if documented by connector)

### RSync (Refund Status Sync)
- [ ] `ConnectorIntegrationV2<RSync, ...>` implemented
- [ ] Uses correct GET endpoint with refund ID
- [ ] Response parsing handles all possible refund states

### Void
- [ ] `ConnectorIntegrationV2<Void, ...>` implemented
- [ ] Correctly references the authorization ID
- [ ] Status mapping handles void/cancel states

## 4. Type Correctness

- [ ] Request types match API documentation exactly (field names, types, optionality)
- [ ] Response types capture ALL documented fields (not just the ones currently used)
- [ ] Serde serialization attributes are correct (`rename`, `skip_serializing_if`, etc.)
- [ ] Enum variants cover all documented values (status codes, error types, etc.)
- [ ] Amount conversion uses existing `common_utils` (NO custom amount conversion code)
- [ ] All amount fields use `MinorUnit` type (not raw `i64`/`f64`/`u64`)
- [ ] Currency unit (`CurrencyUnit::Minor` or `CurrencyUnit::Base`) matches connector API docs
- [ ] Date/time formats match connector expectations

## 5. Error Handling

- [ ] All documented error codes mapped to UCS error types
- [ ] `build_error_response` parses the connector's actual error response format
- [ ] Error response includes: `status_code`, `code`, `message`, `reason`
- [ ] Graceful handling of unexpected/undocumented errors (no panics)
- [ ] Network errors and timeouts handled appropriately

## 6. Macros

- [ ] `create_all_prerequisites!` macro used correctly with proper flow list
- [ ] `macro_connector_implementation!` configured for all implemented flows
- [ ] Resource common data selection is correct:
  - `PaymentFlowData` for payment flows (Authorize, Capture, Void, PSync)
  - `RefundFlowData` for refund flows (Refund, RSync)
  - `DisputeFlowData` for dispute flows (if applicable)
- [ ] Request/Response type naming conventions followed (flow-specific per UCS-004):
  - `{ConnectorName}AuthorizeRequest`, `{ConnectorName}AuthorizeResponse` (not generic "Payments")
  - `{ConnectorName}CaptureRequest`, `{ConnectorName}CaptureResponse`
  - `{ConnectorName}RefundRequest`, `{ConnectorName}RefundResponse`
- [ ] `amount_converters` field declared in `create_all_prerequisites!` for all payment flows

## 7. Payment Methods

For each supported payment method:

- [ ] Card payments: All documented card networks supported (Visa, Mastercard, Amex, etc.)
- [ ] Wallets: Apple Pay, Google Pay, PayPal, etc. (as documented)
- [ ] Bank Transfers: ACH, SEPA, etc. (as documented)
- [ ] Bank Redirects: iDEAL, Giropay, etc. (as documented)
- [ ] BNPL: Klarna, Affirm, etc. (as documented)
- [ ] Payment method data correctly transformed from UCS format to connector format
- [ ] 3DS/authentication flow handled (if supported)

## 8. Webhooks

- [ ] `IncomingWebhook` trait implemented (if connector supports webhooks)
- [ ] `get_webhook_object_reference_id` extracts payment/refund ID correctly
- [ ] `get_webhook_event_type` maps all connector events to UCS events
- [ ] Webhook signature verification implemented
- [ ] Webhook body parsing handles all documented event types

## 9. Tests

- [ ] Integration test file exists at correct path
- [ ] Tests cover all implemented flows (Authorize, Capture, Void, Refund, Sync)
- [ ] Tests cover error scenarios (invalid card, insufficient funds, etc.)
- [ ] Tests cover supported payment methods
- [ ] Webhook event tests (if applicable)

## 10. Tech Spec Alignment

- [ ] Implementation matches the technical specification in `references/{connector_name}/technical_specification.md`
- [ ] All endpoints listed in the tech spec are implemented
- [ ] Status mappings match the tech spec
- [ ] Error mappings match the tech spec
- [ ] No undocumented assumptions made during implementation

## 11. Security Review

- [ ] No hardcoded API keys, tokens, or credentials in connector code
- [ ] All sensitive fields (card number, CVV, expiry) masked using `Maskable` / `Secret`
- [ ] No PCI-sensitive data logged or included in error messages
- [ ] Webhook signature verification implemented (if webhooks supported)
- [ ] Authentication credentials extracted from `ConnectorSpecificConfig`, not hardcoded
- [ ] Error responses do not leak raw connector error details to end users

---

## 12. ConnectorSpecificConfig Registration

- [ ] Enum variant added to `ConnectorSpecificConfig` in `router_data.rs`
- [ ] Added to `extract_base_url!` macro in `router_data.rs`
- [ ] Added to `connector_key!` macro in `router_data.rs`
- [ ] `ForeignTryFrom<(&ConnectorAuthType, &ConnectorEnum)>` match arm added in `router_data.rs`
- [ ] Added to `dummy_auth()` in `field-probe/src/main.rs`
- [ ] Added to `all_connectors()` in `field-probe/src/main.rs`
- [ ] Auth field types match the connector's authentication pattern (HeaderKey, BodyKey, SignatureKey)
- [ ] `base_url: Option<String>` field included in the enum variant

## Summary

After completing the checklist:

| Section | Result |
|---------|--------|
| Build | Pass/Fail |
| Foundation | Pass/Fail |
| Flows | Pass/Fail |
| Type Correctness | Pass/Fail |
| Error Handling | Pass/Fail |
| Macros | Pass/Fail |
| Payment Methods | Pass/Fail |
| Webhooks | Pass/Fail/N/A |
| Tests | Pass/Fail |
| Tech Spec Alignment | Pass/Fail |
| Security Review | Pass/Fail |
| ConnectorSpecificConfig | Pass/Fail |

**Overall: PASS / FAIL**

If any section fails, fix the issues and re-validate before marking the connector as complete.
