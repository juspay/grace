# Tech Spec Generation

Instructions for generating a UCS connector technical specification from API documentation.

This is a multi-stage process: **Scrape -> Generate -> Enhance -> Field Analysis**.

---

## Input

One of the following:

1. **URLs** -- API documentation URLs to scrape (uses [link_fetcher.md](link_fetcher.md))
2. **Pre-scraped markdown files** -- Already in `references/{connector_name}/`
3. **A mix** -- Some URLs + some existing files

## Output

A complete technical specification at:
```
references/{connector_name}/technical_specification.md
```

---

## Stage 1: Scrape Documentation

**Skip this stage if you already have markdown files in `references/{connector_name}/`.**

Follow [link_fetcher.md](link_fetcher.md) to scrape all provided API documentation URLs into markdown files. Save output to `references/{connector_name}/`.

Ensure you capture documentation for:
- Authentication methods
- All payment-related endpoints (create, capture, void, refund)
- Status/sync endpoints
- Webhook setup and event types
- Error response formats
- Supported payment methods

---

## Stage 2: Generate Tech Spec

Read all scraped markdown files from `references/{connector_name}/` and generate a structured technical specification.

### Extraction Guidelines

- Extract ALL available endpoints from the documentation
- Maintain exact 1:1 correspondence between source content and documentation
- Do not modify, enhance, or assume any missing information
- Structure only what is explicitly present in the source material
- Cover all API flows mentioned in the documentation, not just specific ones

### Required Sections

The generated tech spec must follow this structure:

```markdown
# {ConnectorName} UCS Connector Integration Technical Specification

## 1. UCS Connector Overview

### 1.1 Basic Information
- **Connector Name**: {connector_name}
- **Base URL**: {base_url}
- **API Documentation**: [Link]
- **Supported Countries**: [List]
- **Supported Currencies**: [List]
- **UCS Architecture**: gRPC-based stateless connector

### 1.2 UCS Authentication Method
- **Type**: [API Key / OAuth / Bearer Token / HMAC / etc.]
- **Header Format**: [e.g., "Authorization: Bearer {api_key}"]
- **Additional Headers**: [Any required headers]
- **UCS Auth Type**: [HeaderKey / BodyKey / SignatureKey]

### 1.3 UCS Supported Features
| Feature | Supported | Implementation Notes |
|---------|-----------|---------------------|
| Card Payments | Y/N | All networks: Visa, MC, Amex |

> **Note**: Use Y/N notation in generated tech specs for unambiguous plain-text compatibility.
| Apple Pay | Y/N | Encrypted payment data |
| Google Pay | Y/N | Token-based payments |
| Bank Transfers | Y/N | ACH, SEPA, local methods |
| BNPL Providers | Y/N | Klarna, Affirm, Afterpay |
| Bank Redirects | Y/N | iDEAL, Giropay, etc. |
| Webhooks | Y/N | Real-time notifications |
| 3DS 2.0 | Y/N | Challenge/frictionless |
| Recurring Payments | Y/N | Mandate setup |
| Partial Capture | Y/N | Multiple captures |
| Partial Refunds | Y/N | Refund flexibility |
| Disputes | Y/N | Chargeback handling |

## 2. UCS API Endpoints

### 2.1 Payment Operations
| Operation | Method | Endpoint | UCS Flow |
|-----------|--------|----------|----------|
| Create Payment | POST | /v1/payments | Authorize |
| Capture Payment | POST | /v1/payments/{id}/capture | Capture |
| Cancel Payment | POST | /v1/payments/{id}/cancel | Void |
| Get Payment | GET | /v1/payments/{id} | PSync |

### 2.2 Refund Operations
| Operation | Method | Endpoint | UCS Flow |
|-----------|--------|----------|----------|
| Create Refund | POST | /v1/refunds | Refund |
| Get Refund | GET | /v1/refunds/{id} | RSync |

## 3. UCS Data Models

### 3.1 Request/Response for Each Endpoint
For EVERY endpoint, include:
- Exact endpoint URL/path
- HTTP method
- All headers
- Complete request payload structure (as documented)
- Complete response payload structure (as documented)
- cURL examples (if present)
- Error responses (if documented)

### 3.2 UCS Status Mappings
| Connector Status | UCS AttemptStatus | Description |
|------------------|-------------------|-------------|
| (map all documented statuses) |

### 3.3 UCS Error Code Mappings
| Connector Error | UCS Error | Description |
|----------------|-----------|-------------|
| (map all documented error codes) |

## 4. UCS Implementation Details

### 4.1 Amount Handling
- Currency unit: Minor or Base (based on connector API)
- Use existing common_utils for conversion (do NOT create custom code)

### 4.2 Payment Method Transformations
- Document how each payment method's data maps to connector API fields

## 5. UCS Webhook Implementation
- Webhook endpoint configuration
- Signature verification algorithm
- Event type mappings to UCS events

## 6. UCS Testing Strategy
- Required test cases per flow
- Required test cases per payment method
```

### Key Rules for Generation

1. **Use exact field names, values, and structures** from the source documentation
2. **Preserve original JSON formatting and data types**
3. **Include all optional and required parameters** as marked in the docs
4. **Maintain original error codes and messages**
5. **Do not fill gaps or make educated guesses**
6. If information is partially available, document only what is explicitly provided
7. Use "Not specified in source documentation" for clearly missing but relevant information

---

## Stage 3: Enhance (Recommended)

After generating the initial tech spec, cross-reference it against the scraped markdown files to fill gaps.

### Enhancement Process

1. Read the generated `technical_specification.md`
2. Identify gaps (missing endpoints, incomplete request/response bodies, undocumented parameters)
3. For each scraped file in `references/{connector_name}/`:
   a. Read the file completely
   b. Extract any information missing from the tech spec:
      - API endpoints and their methods
      - Request parameters and body structure
      - Response formats and status codes (make the response body a 1:1 copy)
      - Authentication mechanisms
      - Error codes and handling
      - Rate limits and constraints
   c. Update `technical_specification.md` with the missing information
   d. Validate that request-response pairs are complete and accurate
4. After processing all files, verify:
   - Every API endpoint has complete request AND response documentation
   - All parameters are documented with types and descriptions
   - Response status codes are mapped to their scenarios
   - Authentication flows are fully described
   - Error handling covers all documented error codes

### Enhancement Output

- Updated `technical_specification.md` with all gaps filled
- A brief summary listing:
  - Information added from each source file
  - Any inconsistencies found and resolved
  - Remaining gaps that could not be filled from available documentation

---

## Stage 4: Field Analysis (Optional)

For complex connectors with multi-step flows, run field dependency analysis to trace where each API field originates.

Follow [field_analysis.md](field_analysis.md) for the full process.

### What This Adds

For each flow that depends on a previous flow (e.g., Capture depends on Authorize), the field analysis maps:
- Which fields in the Capture request come from the Authorize response
- Which fields are user-provided vs. system-generated
- Which fields are ambiguous and need manual verification

This information is appended to the tech spec as an "API Field Dependencies" section, which significantly improves the quality of generated connector code.

---

## Worked Example (Trimmed)

Below is a trimmed example of what a generated tech spec looks like, based on the Finix connector:

```markdown
# Finix UCS Connector Integration Technical Specification

## 1. UCS Connector Overview

### 1.1 Basic Information
- **Connector Name**: Finix
- **Base URL (Sandbox)**: https://finix.sandbox-payments-api.com
- **Base URL (Production)**: https://finix.live-payments-api.com
- **API Documentation**: https://docs.finix.com

### 1.2 UCS Authentication Method
- **Type**: HTTP Basic Authentication
- **Username**: API User ID (e.g., US_EXAMPLE_USER_ID_12345)
- **Password**: Secret Key (e.g., 00000000-0000-0000-0000-000000000000)
- **Required Headers**: Content-Type: application/json, Finix-Version: 2022-02-01

## 2. UCS API Endpoints

### 2.1 Payment Operations
| Operation | Method | Endpoint | UCS Flow |
|-----------|--------|----------|----------|
| Create Authorization | POST | /authorizations | Authorize |
| Capture Authorization | POST | /authorizations/{id}/capture | Capture |
| Void Authorization | POST | /authorizations/{id}/void | Void |
| Get Authorization | GET | /authorizations/{id} | PSync |

## 3. UCS Data Models

### 3.1 Create Authorization (Authorize Flow)

**Request Body:**
{
  "amount": 100,
  "currency": "USD",
  "merchant": "MU_EXAMPLE_MERCHANT_ID",
  "source": "PI_EXAMPLE_INSTRUMENT_ID",
  "tags": { "order_number": "21DFASJSAKAS" }
}

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| amount | integer (int64) | Yes | Total amount in cents |
| currency | string | Yes | ISO 4217 currency code |
| merchant | string | Yes | Merchant ID |
| source | string | Yes | Payment Instrument ID |
| tags | object/null | No | Custom metadata (up to 50 pairs) |

(... continue for all endpoints ...)
```
