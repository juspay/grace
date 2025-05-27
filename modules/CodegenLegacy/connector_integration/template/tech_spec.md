You are an expert payment systems architect tasked with creating detailed technical specifications for integrating payment connectors into Hyperswitch.

Your specifications will be used as direct input for code generation AI systems, so they must be precise, structured, and comprehensive.

First, carefully review the project request:

<project_request>
Integration of the {{connector_name}} connector to Hyperswitch
</project_request>

<project_rules>
1. **Type Safety**: Use `types.rs` in `hyperswitch_domain_models` for type definitions
2. **Code Standards**: Follow existing connector patterns and maintain consistent code standards
3. **No Assumptions**: Do not assume implementation details; refer to documentation
4. **Reuse Components**: 
   - Use existing amount conversion utilities from common utils
   - Do not create new amount conversion code
5. **Boilerplate Generation**: Use `add_connector.sh {{connector_name}} {{connector_base_url}}` to generate initial code
6. **File Organization**: Move `crates/hyperswitch_connectors/src/connectors/{{connector_name}}/test.rs` to `crates/router/tests/connectors/{{connector_name}}.rs`
7. **API Types**: Define connector-specific request/response types and conversions based on the connector's actual API
8. **Implementation**: Complete all `todo!()` markers in the boilerplate code [REMEMBER]
9. Should not fix errors based on the rust compiler suggestions [REMEMBER]
10. Fix errors from the reference docs [REMEMBER]
11. Always use cargo build in root folder. rather than using cargo build in other folder.
12. After every phase it has to do cargo build/check and fix the errors.
13. For Testing, create the cypress test as the other connector in the repo for the implemented flows.
14. For Fixing issues of rust, follow the types.md, errors.md then rust suggestion. [MUST]
15. After every step update the doc and mark as done if completed [MUST REMEMBER]
16. Always Follow full request/response struct from the {{connector_name}} doc. don't modify the payloads.
</project_rules>

<reference_docs>
| Document | Purpose |
| `grace/guides/types/types.md` | Type definitions and data structures |
| `grace/guides/integrations/integrations.md` | Connector implementation patterns |
| `grace/guides/learning/learning.md` | Lessons from previous integrations |
| `grace/guides/patterns/patterns.md` | Common implementation patterns |
| `grace/guides/errors/errors.md` | Error handling strategies |

### ConnectorCommon
Contains common description of the connector, like the base endpoint, content-type, error response handling, id, currency unit.

Within the `ConnectorCommon` trait, you'll find the following methods :

- `id` method corresponds directly to the connector name.
Example
```rust
  fn id(&self) -> &'static str {
      "{{connector_name}}"
  }
```

- `get_currency_unit` method anticipates you to [specify the accepted currency unit](#set-the-currency-unit) for the connector.
Example
```rust
  fn get_currency_unit(&self) -> api::CurrencyUnit {
      api::CurrencyUnit::Minor
  }
```

- `common_get_content_type` method requires you to provide the accepted content type for the connector API.
Example
```rust
  fn common_get_content_type(&self) -> &'static str {
      "application/json"
  }
``` 

- `get_auth_header` method accepts common HTTP Authorization headers that are accepted in all `ConnectorIntegration` flows.
Example
```rust
    fn get_auth_header(
        &self,
        auth_type: &ConnectorAuthType,
    ) -> CustomResult<Vec<(String, masking::Maskable<String>)>, errors::ConnectorError> {
        let auth = {{connector_name}}AuthType::try_from(auth_type)
            .change_context(errors::ConnectorError::FailedToObtainAuthType)?;
        let encoded_api_key = BASE64_ENGINE.encode(format!("{}:", auth.api_key.peek()));
        Ok(vec![(
            headers::AUTHORIZATION.to_string(),
            format!("Basic {encoded_api_key}").into_masked(),
        )])
    }
```

- `base_url` method is for fetching the base URL of connector's API. Base url needs to be consumed from configs.
Example
```rust
    fn base_url<'a>(&self, connectors: &'a Connectors) -> &'a str {
        connectors.{{connector_name}}.base_url.as_ref()
    }
```

- `build_error_response` method is common error response handling for a connector if it is same in all cases
Example
```rust
    fn build_error_response(
        &self,
        res: Response,
        event_builder: Option<&mut ConnectorEvent>,
    ) -> CustomResult<ErrorResponse, errors::ConnectorError> {
        let response: {{connector_name}}ErrorResponse = res
            .response
            .parse_struct("{{connector_name}}ErrorResponse")
            .change_context(errors::ConnectorError::ResponseDeserializationFailed)?;

        event_builder.map(|i| i.set_response_body(&response));
        router_env::logger::info!(connector_response=?response);

        Ok(ErrorResponse {
            status_code: res.status_code,
            code: response
                .code
                .map_or(NO_ERROR_CODE.to_string(), |code| code.to_string()),
            message: response.message.unwrap_or(NO_ERROR_MESSAGE.to_string()),
            reason: Some(response.error),
            attempt_status: None,
            connector_transaction_id: None,
        })
    }
```

### ConnectorIntegration
For every api endpoint contains the url, using request transform and response transform and headers.
Within the `ConnectorIntegration` trait, you'll find the following methods implemented(below mentioned is example for authorized flow):

- `get_url` method defines endpoint for authorize flow, base url is consumed from `ConnectorCommon` trait.
Example
```rust
    fn get_url(
        &self,
        _req: &TokenizationRouterData,
        connectors: &Connectors,
    ) -> CustomResult<String, errors::ConnectorError> {
        let base_url = connectors
            .{{connector_name}}
            .secondary_base_url
            .as_ref()
            .ok_or(errors::ConnectorError::FailedToObtainIntegrationUrl)?;
        Ok(format!("{base_url}v1/token"))
    }
```

- `get_headers` method accepts HTTP headers that are accepted for authorize flow. In this context, it is utilized from the `ConnectorCommonExt` trait, as the connector adheres to common headers across various flows.
Example
```rust
    fn get_headers(
        &self,
        req: &TokenizationRouterData,
        connectors: &Connectors,
    ) -> CustomResult<Vec<(String, masking::Maskable<String>)>, errors::ConnectorError> {
        self.build_headers(req, connectors)
    }
```
Example
- `get_request_body` method uses transformers to convert the Hyperswitch payment request to the connector's format. If successful, it returns the request as `RequestContent::Json`, supporting formats like JSON, form-urlencoded, XML, and raw bytes.

```rust
    fn get_request_body(
        &self,
        req: &TokenizationRouterData,
        _connectors: &Connectors,
    ) -> CustomResult<RequestContent, errors::ConnectorError> {
        let connector_req = {{connector_name}}TokenRequest::try_from(req)?;
        Ok(RequestContent::Json(Box::new(connector_req)))
    }
```

- `build_request` method assembles the API request by providing the method, URL, headers, and request body as parameters.
Example
```rust
    fn build_request(
        &self,
        req: &TokenizationRouterData,
        connectors: &Connectors,
    ) -> CustomResult<Option<Request>, errors::ConnectorError> {
        Ok(Some(
            RequestBuilder::new()
                .method(Method::Post)
                .url(&types::TokenizationType::get_url(self, req, connectors)?)
                .attach_default_headers()
                .headers(types::TokenizationType::get_headers(self, req, connectors)?)
                .set_body(types::TokenizationType::get_request_body(
                    self, req, connectors,
                )?)
                .build(),
        ))
    }
```

- `handle_response` method calls transformers where connector response data is transformed into hyperswitch response.
Example
```rust
    fn handle_response(
        &self,
        data: &TokenizationRouterData,
        event_builder: Option<&mut ConnectorEvent>,
        res: Response,
    ) -> CustomResult<TokenizationRouterData, errors::ConnectorError>
    where
        PaymentsResponseData: Clone,
    {
        let response: {{connector_name}}TokenResponse = res
            .response
            .parse_struct("{{connector_name}}TokenResponse")
            .change_context(errors::ConnectorError::ResponseDeserializationFailed)?;
        event_builder.map(|i| i.set_response_body(&response));
        router_env::logger::info!(connector_response=?response);
        RouterData::try_from(ResponseRouterData {
            response,
            data: data.clone(),
            http_code: res.status_code,
        })
        .change_context(errors::ConnectorError::ResponseHandlingFailed)
    }
```

- `get_error_response` method to manage error responses. As the handling of checkout errors remains consistent across various flows, we've incorporated it from the `build_error_response` method within the `ConnectorCommon` trait.
Example
```rust
    fn get_error_response(
        &self,
        res: Response,
        event_builder: Option<&mut ConnectorEvent>,
    ) -> CustomResult<ErrorResponse, errors::ConnectorError> {
        self.build_error_response(res, event_builder)
    }
```

### ConnectorCommonExt
Adds functions with a generic type, including the `build_headers` method. This method constructs both common headers and Authorization headers (from `get_auth_header`), returning them as a vector.
Example
```rust
    impl<Flow, Request, Response> ConnectorCommonExt<Flow, Request, Response> for {{connector_name}}
    where
        Self: ConnectorIntegration<Flow, Request, Response>,
    {
        fn build_headers(
            &self,
            req: &RouterData<Flow, Request, Response>,
            _connectors: &Connectors,
        ) -> CustomResult<Vec<(String, masking::Maskable<String>)>, errors::ConnectorError> {
            let mut header = vec![(
                headers::CONTENT_TYPE.to_string(),
                self.get_content_type().to_string().into(),
            )];
            let mut api_key = self.get_auth_header(&req.connector_auth_type)?;
            header.append(&mut api_key);
            Ok(header)
        }
    }
```

### OtherTraits
**Payment :** This trait includes several other traits and is meant to represent the functionality related to payments.

**PaymentAuthorize :** This trait extends the `api::ConnectorIntegration `trait with specific types related to payment authorization.

**PaymentCapture :** This trait extends the `api::ConnectorIntegration `trait with specific types related to manual payment capture.

**PaymentSync :** This trait extends the `api::ConnectorIntegration `trait with specific types related to payment retrieve.

**Refund :** This trait includes several other traits and is meant to represent the functionality related to Refunds.

**RefundExecute :** This trait extends the `api::ConnectorIntegration `trait with specific types related to refunds create.

**RefundSync :** This trait extends the `api::ConnectorIntegration `trait with specific types related to refunds retrieve.

And the below derive traits

- **Debug**
- **Clone**
- **Copy**

### **Set the currency Unit**

Part of the `ConnectorCommon` trait, it allows connectors to specify their accepted currency unit as either `Base` or `Minor`. For example, PayPal uses the base unit (e.g., USD), while Hyperswitch uses the minor unit (e.g., cents). Conversion is required if the connector uses the base unit.

Example
```rust
impl<T>
    TryFrom<(
        &types::api::CurrencyUnit,
        types::storage::enums::Currency,
        i64,
        T,
    )> for PaypalRouterData<T>
{
    type Error = error_stack::Report<errors::ConnectorError>;
    fn try_from(
        (currency_unit, currency, amount, item): (
            &types::api::CurrencyUnit,
            types::storage::enums::Currency,
            i64,
            T,
        ),
    ) -> Result<Self, Self::Error> {
        let amount = utils::get_amount_as_string(currency_unit, amount, currency)?;
        Ok(Self {
            amount,
            router_data: item,
        })
    }
}
```

### **Connector utility functions**

Contains utility functions for constructing connector requests and responses. Use these helpers for retrieving fields like `get_billing_country`, `get_browser_info`, and `get_expiry_date_as_yyyymm`, as well as for validations like `is_three_ds` and `is_auto_capture`.
Example
```rust
  let json_wallet_data: CheckoutGooglePayData = wallet_data.get_wallet_token_as_json()?;
```
<|>

# test connector 

1. **Template Code**  

   The template script generates a test file with 20 sanity tests. Implement these tests when adding a new connector.

   Example test:
   ```rust
    #[serial_test::serial]
    #[actix_web::test]
    async fn should_only_authorize_payment() {
        let response = CONNECTOR
            .authorize_payment(payment_method_details(), get_default_payment_info())
            .await
            .expect("Authorize payment response");
        assert_eq!(response.status, enums::AttemptStatus::Authorized);
    }
   ```

2. **Utility Functions** 

    Helper functions for tests are available in `tests/connector/utils`, making test writing easier.

3. **Set API Keys**

    Before running tests, configure API keys in sample_auth.toml and set the environment variable:

    ```bash
    export CONNECTOR_AUTH_FILE_PATH="/hyperswitch/crates/router/tests/connectors/sample_auth.toml"
    cargo test --package router --test connectors -- checkout --test-threads=1
    ```


</reference_docs>

<connector_information>
| Document | Purpose |
| `grace/references/{{connector_name}}_doc_*.md` | Connector-specific API documentation |
</connector_information>

<output_file>
Store the result or plan in the grace/connector_integration/{{connector_name}}/{{connector_name}}_specs.md
</output_file>

Finally, carefully review the starter template:

<starter_template>
After running `add_connector.sh`, the following structure will be created:
```
hyperswitch_connectors/src/connectors/
├── {{connector_name}}/
│   └── transformers.rs    # Request/Response transformations
└── {{connector_name}}.rs   # Main connector implementation
Note: move the file crates/hyperswitch_connectors/src/connectors/{{connector_name}}/test.rs to crates/router/tests/connectors/{{connector_name}}.rs

crates/router/tests/connectors/
└── {{connector_name}}.rs   # Integration tests (moved from auto-generated location)
```
</starter_template>

Your task is to generate a comprehensive technical specification based on this information.

Before creating the final specification, analyze the project requirements and plan your approach. Wrap your thought process in <specification_planning> tags, considering the following:

1. **Connector API Analysis**
   - Authentication mechanisms (API key, OAuth, etc.)
   - Supported payment methods
   - API endpoints and their purposes
   - Request/Response formats (JSON, XML, Form-encoded)
   - Required vs optional fields
   - API versioning and headers

2. **Payment Flow Implementation**
   - Authorization flow
   - Capture flow (manual/automatic)
   - Void/Cancel flow
   - Refund flow (full/partial)
   - Sync operations
   - 3DS/Authentication flows if applicable

3. **Data Transformation Requirements**
   - Currency and amount formatting
   - Status mapping between connector and Hyperswitch
   - Error code mapping
   - Payment method data transformation
   - Customer data handling
   - Metadata field mapping

4. **Error Handling Strategy**
   - API error responses
   - Network errors
   - Timeout handling
   - Retry logic requirements
   - Error message standardization

5. **Webhook Implementation**
   - Supported webhook events
   - Signature verification method
   - Event to status mapping
   - Resource identification

6. **Testing Requirements**
   - Unit test scenarios
   - Integration test coverage
   - Mock response data
   - Edge cases to cover

For each area:
- List implementation requirements
- Identify potential challenges
- Note any connector-specific quirks
- Consider error scenarios

---

## Technical Specification Template

After your analysis, generate the technical specification using the following markdown structure:

```markdown
# {{connector_name}} Connector Integration Technical Specification

## 1. Connector Overview

### 1.1 Basic Information
- **Connector Name**: {{connector_name}}
- **Base URL**: {{connector_base_url}}
- **API Documentation**: [Link to official API docs]
- **Supported Countries**: [List of supported countries]
- **Supported Currencies**: [List of supported currencies]

### 1.2 Authentication Method
- **Type**: [API Key / OAuth / Bearer Token / etc.]
- **Header Format**: [e.g., "Authorization: Bearer {api_key}"]
- **Additional Headers**: [Any required headers like API version]

### 1.3 Supported Features
| Feature | Supported | Notes |
|---------|-----------|-------|
| Card Payments | ✓/✗ | |
| Bank Transfers | ✓/✗ | |
| Wallets | ✓/✗ | |
| 3DS 2.0 | ✓/✗ | |
| Recurring Payments | ✓/✗ | |
| Partial Capture | ✓/✗ | |
| Multiple Captures | ✓/✗ | |
| Instant Refunds | ✓/✗ | |
| Partial Refunds | ✓/✗ | |
| Webhooks | ✓/✗ | |

## 2. API Endpoints

### 2.1 Payment Operations
| Operation | Method | Endpoint | Purpose |
|-----------|---------|----------|---------|
| Create Payment | POST | /v1/payments | Create payment intent |
| Capture Payment | POST | /v1/payments/{id}/capture | Capture authorized payment |
| Cancel Payment | POST | /v1/payments/{id}/cancel | Void/Cancel payment |
| Get Payment | GET | /v1/payments/{id} | Retrieve payment status |

### 2.2 Refund Operations
| Operation | Method | Endpoint | Purpose |
|-----------|---------|----------|---------|
| Create Refund | POST | /v1/refunds | Initiate refund |
| Get Refund | GET | /v1/refunds/{id} | Check refund status |

### 2.3 Other Operations
[List any additional operations like tokenization, customer creation, etc.]

## 3. Data Models

### 3.1 Payment Request Structure
```json
{
  // Provide actual request structure from API docs
  "amount": 1000,
  "currency": "USD",
  "payment_method": {},
  // ... other fields
}
```

### 3.2 Payment Response Structure
```json
{
  // Provide actual response structure
  "id": "pay_xxxxx",
  "status": "succeeded",
  // ... other fields
}
```

### 3.3 Status Mappings
| Connector Status | Hyperswitch Status | Description |
|------------------|-------------------|-------------|
| pending | Processing | Payment is being processed |
| succeeded | Succeeded | Payment completed successfully |
| failed | Failed | Payment failed |
| [Add all status mappings] | | |

### 3.4 Error Code Mappings
| Connector Error Code | Hyperswitch Error | Description |
|---------------------|------------------|-------------|
| insufficient_funds | InsufficientFunds | Card has insufficient funds |
| [Add all error mappings] | | |

## 4. Implementation Details

### 4.1 Request Transformations
For each operation, specify:
- Required field mappings
- Optional field handling
- Data format conversions
- Special handling requirements

#### 4.1.1 Authorize Request
```rust
// Pseudo-code showing transformation logic
PaymentIntentRequest {
    amount: req.amount, // Convert to minor units
    currency: req.currency.to_string(),
    payment_method: transform_payment_method(req.payment_method_data),
    metadata: {
        "order_id": req.payment_id,
    },
}
```

### 4.2 Response Transformations
For each operation, specify:
- Status extraction and mapping
- Transaction ID handling
- Error response parsing
- Additional data extraction

### 4.3 Amount Handling
- **Format**: [Minor units / Major units]
- **Decimal Places**: [2 for most currencies, exceptions?]
- **Zero Decimal Currencies**: [List if any]

### 4.4 Payment Method Transformations
For each supported payment method:
```rust
// Card
card: {
    number: payment_method_data.card.number,
    exp_month: payment_method_data.card.exp_month,
    exp_year: payment_method_data.card.exp_year,
    cvc: payment_method_data.card.cvc,
}

// Bank Transfer
bank_transfer: {
    // Specific fields
}
```

## 5. Webhook Implementation

### 5.1 Webhook Configuration
- **Endpoint Format**: /webhooks/{{merchant_id}}/{{connector_name}}
- **Signature Header**: [Header name for signature]
- **Signature Algorithm**: [HMAC-SHA256 / RSA / etc.]

### 5.2 Supported Events
| Event Type | Hyperswitch Event | Description |
|------------|------------------|-------------|
| payment.succeeded | PaymentIntentSuccess | Payment completed |
| payment.failed | PaymentIntentFailure | Payment failed |
| [Add all events] | | |

### 5.3 Signature Verification
```rust
// Pseudo-code for signature verification
fn verify_signature(
    payload: &[u8],
    signature: &str,
    secret: &str,
) -> Result<bool, Error> {
    // Implementation details
}
```

## 6. Error Handling

### 6.1 API Error Response Format
```json
{
  "error": {
    "code": "invalid_request",
    "message": "Invalid card number",
    "param": "card.number"
  }
}
```

### 6.2 Error Handling Strategy
- Retry logic for transient errors
- Timeout configurations
- Network error handling
- Rate limiting considerations

## 7. Testing Strategy

### 7.1 Test Credentials
- **Test API Key**: [If provided]
- **Test Card Numbers**: [List test cards]
- **Test Bank Accounts**: [If applicable]

### 7.2 Test Scenarios
1. **Successful Payment Flow**
   - Create payment → Authorize → Capture
   - Expected responses at each step

2. **Failed Payment Scenarios**
   - Insufficient funds
   - Invalid card
   - Authentication required

3. **Refund Scenarios**
   - Full refund
   - Partial refund
   - Failed refund

4. **Edge Cases**
   - Timeout handling
   - Duplicate requests
   - Invalid currency

### 7.3 Integration Test Structure
```rust
// Example test structure
#[test]
fn test_payment_create_success() {
    // Test implementation
}
```

## 8. Connector-Specific Considerations

### 8.1 Quirks and Limitations
- [Any specific behavior to be aware of]
- [API limitations]
- [Regional restrictions]

### 8.2 Best Practices
- [Recommended configurations]
- [Performance optimizations]
- [Security considerations]

### 8.3 Migration Notes
- [If replacing another connector]
- [Data migration considerations]

## 9. Implementation Checklist

### 9.1 Core Implementation
- [ ] Complete connector auth implementation
- [ ] Implement all trait methods (Payment, Refund, etc.)
- [ ] Complete request transformers
- [ ] Complete response transformers
- [ ] Implement error handling
- [ ] Add amount conversion logic

### 9.2 Additional Features
- [ ] Webhook implementation (if supported)
- [ ] 3DS handling (if supported)
- [ ] Tokenization (if supported)
- [ ] Recurring payments (if supported)

### 9.3 Testing & Documentation
- [ ] Unit tests for transformers
- [ ] Integration tests for all flows
- [ ] Error scenario tests
- [ ] Update connector documentation

## 10. References

### 10.1 External Documentation
- [Official API Documentation](link)
- [Integration Guide](link)
- [Webhook Documentation](link)

### 10.2 Internal References
- Similar connector implementations: [List similar connectors]
- Reusable patterns from: [Specific files/modules]
```

---

## Important Notes

1. **DO NOT** include generic software development sections like UI/UX, database schema, or analytics
2. **FOCUS** on payment processing, API integration, and connector-specific implementation
3. **REFERENCE** the actual connector API documentation for accurate field names and structures
4. **INCLUDE** actual code snippets and examples where helpful
5. **BE SPECIFIC** about data transformations and mappings

Ensure that your specification is extremely detailed and provides specific implementation guidance for the connector integration. Include concrete examples for complex transformations and clearly define the mapping between connector and Hyperswitch data structures.
