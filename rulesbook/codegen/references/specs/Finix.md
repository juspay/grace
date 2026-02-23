# Finix API Documentation

---

## Connector Information

**Connector Name:** Finix

**Base URLs:**
- **Sandbox:** `https://finix.sandbox-payments-api.com`
- **Live (Production):** `https://finix.live-payments-api.com`

**Additional URLs:**
- **Documentation:** `https://docs.finix.com`
- **Support Email:** `support@finix.com`

---

## Authentication Details

**Authentication Method:** HTTP Basic Authentication

**Authentication Parameters:**
- **Username:** API User ID (e.g., `USsRhsHYZGBPnQw8CByJyEQW`)
- **Password:** Secret Key (e.g., `8a14c2f9-d94b-4c72-8f5c-a62908e5b30e`)

**Sandbox Credentials:**
| Parameter | Value |
|-----------|-------|
| Sandbox Username | `USsRhsHYZGBPnQw8CByJyEQW` |
| Sandbox Password | `8a14c2f9-d94b-4c72-8f5c-a62908e5b30e` |

**Required Headers:**
- `Content-Type: application/json`
- `Finix-Version: 2022-02-01`

---

## Complete Endpoint Inventory

### 1. Create an Authorization

**Endpoint:** `POST /authorizations`

**Description:** Create an `Authorization` to process a transaction (also known as a card hold).

**Request Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Finix-Version | string | Yes | Specify the API version. Default: `2022-02-01` |
| Content-Type | string | Yes | Must be `application/json` |

**Request Body:**
```json
{
  "amount": 100,
  "currency": "USD",
  "merchant": "MUsVtN9pH65nGw61H7Nv8Apo",
  "source": "PIkxmtueemLD6dN9ZoWGHT44",
  "tags": {
    "order_number": "21DFASJSAKAS"
  }
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| amount | integer (int64) | Yes | Total amount to be debited in cents (e.g., 100 cents = $1.00) |
| currency | string | Yes | ISO 4217 3-letter currency code |
| merchant | string | Yes | ID of the `Merchant` the Authorization was created under |
| source | string | Yes | ID of the `Payment Instrument` where funds get debited |
| tags | object or null | No | Up to 50 `key: value` pairs for custom metadata |

**cURL Example:**
```bash
curl -i -X POST \
  -u USfdccsr1Z5iVbXDyYt7hjZZ:313636f3-fac2-45a7-bff7-a334b93e7bda \
  https://finix.sandbox-payments-api.com/authorizations \
  -H 'Content-Type: application/json' \
  -H 'Finix-Version: 2022-02-01' \
  -d '{
    "amount": 100,
    "currency": "USD",
    "merchant": "MUsVtN9pH65nGw61H7Nv8Apo",
    "source": "PIkxmtueemLD6dN9ZoWGHT44",
    "tags": {
      "order_number": "21DFASJSAKAS"
    }
  }'
```

**Response Codes:** 201, 400, 401, 402, 403, 404, 406, 422

**Response Headers:**
| Header | Type | Description |
|--------|------|-------------|
| date | string | Date and time of the API request |
| finix-apiuser-role | string | Role of the user who sent the API request. Enum: `ROLE_ADMIN`, `ROLE_PLATFORM`, `ROLE_PARTNER`, `ROLE_MERCHANT` |
| x-request-id | string | Unique identifier for the API request |

**Response Body (201):**
```json
{
  "id": "AUsJgTPyNKUKbkTk4mzq2aoM",
  "created_at": "2025-10-27T15:55:36.29Z",
  "updated_at": "2025-10-27T15:55:36.29Z",
  "3ds_redirect_url": null,
  "additional_buyer_charges": null,
  "additional_healthcare_data": null,
  "additional_purchase_data": null,
  "address_verification": "POSTAL_CODE_AND_STREET_MATCH",
  "amount": 100,
  "amount_requested": 100,
  "application": "APc9vhYcPsRuTSpKD9KpMtPe",
  "currency": "USD",
  "expires_at": "2025-11-03T15:55:36.29Z",
  "failure_code": null,
  "failure_message": null,
  "idempotency_id": null,
  "ip_address_details": null,
  "is_void": false,
  "merchant": "MUmfEGv5bMpSJ9k5TFRUjkmm",
  "merchant_identity": "ID6UfSm1d4WPiWgLYmbyeo3H",
  "messages": [],
  "raw": null,
  "receipt_last_printed_at": null,
  "security_code_verification": "MATCHED",
  "source": "PIkxmtueemLD6dN9ZoWGHT44",
  "state": "SUCCEEDED",
  "supplemental_fee": null,
  "tags": {
    "order_number": "21DFASJSAKAS"
  },
  "trace_id": "0504c0cc-7665-4555-90c3-c460330acf2e",
  "transfer": null,
  "void_state": "UNATTEMPTED",
  "_links": {
    "self": { … },
    "application": { … },
    "merchant_identity": { … }
  }
}
```

**Response Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | ID of the `Authorization` resource |
| created_at | string (date-time) | Timestamp when the object was created |
| updated_at | string (date-time) | Timestamp when the object was last updated |
| 3ds_redirect_url | string or null | Redirect URL for 3DS transactions |
| additional_buyer_charges | object or null | Additional buyer charges details |
| additional_healthcare_data | object or null | Healthcare data details |
| additional_purchase_data | object or null | Purchase data for Level 2/3 Processing |
| address_verification | string or null | Results of Address Verification checks |
| amount | integer (int64) | Total amount to be debited in cents |
| amount_requested | integer | Amount attempted when partial authorization enabled |
| application | string | ID of the `Application` resource |
| card_present_details | object or null | Details for card present transactions |
| currency | string | ISO 4217 3-letter currency code |
| device | string or null | ID of the activated device |
| expires_at | string (date-time) | Authorization expiration time |
| failure_code | string or null | Code of the failure |
| failure_message | string or null | Human-readable description of decline |
| identity | string | ID of buyer 'Identity' for card present authorization |
| idempotency_id | string or null | ID for idempotent requests |
| ip_address_details | object | IP address details (null except for ROLE_PLATFORM) |
| is_void | boolean | Whether the Authorization has been voided |
| merchant | string | ID of the `Merchant` resource |
| merchant_identity | string | ID of the `Identity` resource used by the Merchant |
| messages | Array of strings or null | Additional details (typically null) |
| raw | object or null or string or null | Raw response from the processor |
| receipt_last_printed_at | string or null (date-time) | Timestamp when receipt was last printed |
| security_code_verification | string or null | Results of Security Code Verification check |
| source | string | ID of the `Payment Instrument` where funds get debited |
| state | string | State of the Authorization. Enum: `CANCELED`, `PENDING`, `FAILED`, `SUCCEEDED`, `UNKNOWN` |
| supplemental_fee | string or null | Amount in cents for additional fee |
| tags | object or null | Custom metadata key-value pairs |
| trace_id | string | Trace ID for end-to-end tracking |
| transfer | string or null | ID of the `transfer` resource created when Authorization succeeds |
| void_state | string | Details if Authorization has been voided |
| _links | object | HATEOAS links |

---

### 2. List Authorizations

**Endpoint:** `GET /authorizations`

**Description:** Retrieve a list of `Authorizations`.

**Request Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Finix-Version | string | Yes | Specify the API version. Default: `2022-02-01` |

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| after_cursor | string | Return every resource created after the cursor value |
| amount.gt | integer | Filter by an amount greater than |
| amount.gte | integer | Filter by an amount greater than or equal |
| amount.lt | integer | Filter by an amount less than |
| amount.lte | integer | Filter by an amount less than or equal |
| amount | integer | Filter by an amount equal to the given value |
| before_cursor | string | Return every resource created before the cursor value |
| created_at.gte | string (date-time) | Filter where `created_at` is after the given date |
| created_at.lte | string (date-time) | Filter where `created_at` is before the given date |
| currency | string | Filter by the currency of the resource |
| device | string | Filter by the device's ID |
| idempotency_id | string | Filter by Idempotency ID |
| instrument_account_last4 | string | Filter Transactions by the last 4 digits of the bank account |
| instrument_bin | string | Filter by Bank Identification Number (BIN) - first 6 digits |
| instrument_brand_type | string | Filter by card brand |
| instrument_card_last4 | string | Filter by the payment card last 4 digits |
| instrument_name | string | Filter Transactions by the `name` of the `Payment Instrument` |
| is_void | boolean | Show only voided authorizations |
| limit | integer | The numbers of items to return |
| merchant_id | string | Filter by `Merchant` ID |
| merchant_identity_name | string | Filter Transactions by name of the `Identity` |
| merchant_mid | string | Filter by Merchant Identification Number (MID) |
| merchant_processor_id | string | Filter by `Processor` ID |
| state | any | Filter by transaction state. Enum: `SUCCEEDED`, `FAILED`, `PENDING`, `CANCELED` |
| tags.key | string | Filter by the tag's key |
| tags.value | string | Filter by the tag's value |
| trace_id | string | Filter by `trace_id` |
| updated_at.gte | string (date-time) | Filter where `updated_at` is after the given date |
| updated_at.lte | string (date-time) | Filter where `updated_at` is before the given date |

**cURL Example:**
```bash
curl "https://finix.sandbox-payments-api.com/authorizations" \
    -H "Finix-Version: 2022-02-01" \
    -u USfdccsr1Z5iVbXDyYt7hjZZ:313636f3-fac2-45a7-bff7-a334b93e7bda
```

**Response Codes:** 200, 401, 403, 404, 406

**Response Headers:**
| Header | Type | Description |
|--------|------|-------------|
| date | string | Date and time of the API request |
| finix-apiuser-role | string | Role of the user who sent the API request |
| x-request-id | string | Unique identifier for the API request |

**Response Body (200):**
```json
{
  "_embedded": {
    "authorizations": [ … ]
  },
  "_links": {
    "self": { … },
    "next": { … },
    "last": { … }
  },
  "page": {
    "offset": 0,
    "limit": 20,
    "count": 633397
  }
}
```

**Response Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| _embedded | object | Contains list of `Authorization` objects |
| _embedded.authorizations | array | Array of Authorization objects |
| _links | object | Pagination links |
| _links.self | object | Link to current page |
| _links.next | object | Link to next page |
| _links.last | object | Link to last page |
| page | object | Page details |
| page.offset | integer | Current offset |
| page.limit | integer | Number of items per page |
| page.count | integer | Total count of items |

---

### 3. Fetch an Authorization

**Endpoint:** `GET /authorizations/{authorization_id}`

**Description:** Retrieve the details of a previously created `Authorization`.

**Request Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Finix-Version | string | Yes | Specify the API version. Default: `2022-02-01` |

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| authorization_id | string | Yes | ID of `Authorization` to fetch |

**cURL Example:**
```bash
curl -i -X GET \
  -u USfdccsr1Z5iVbXDyYt7hjZZ:313636f3-fac2-45a7-bff7-a334b93e7bda \
  https://finix.sandbox-payments-api.com/authorizations/AUg8unYpnWBEY1AdVUDkdQYJ
```

**Response Codes:** 200

**Response Headers:**
| Header | Type | Description |
|--------|------|-------------|
| date | string | Date and time of the API request |
| finix-apiuser-role | string | Role of the user who sent the API request |
| x-request-id | string | Unique identifier for the API request |

**Response Body (200):**
```json
{
  "id": "AUsJgTPyNKUKbkTk4mzq2aoM",
  "created_at": "2025-10-27T15:55:36.29Z",
  "updated_at": "2025-10-27T15:55:36.29Z",
  "3ds_redirect_url": null,
  "additional_buyer_charges": null,
  "additional_healthcare_data": null,
  "additional_purchase_data": null,
  "address_verification": "POSTAL_CODE_AND_STREET_MATCH",
  "amount": 100,
  "amount_requested": 100,
  "application": "APc9vhYcPsRuTSpKD9KpMtPe",
  "currency": "USD",
  "expires_at": "2025-11-03T15:55:36.29Z",
  "failure_code": null,
  "failure_message": null,
  "idempotency_id": null,
  "ip_address_details": null,
  "is_void": false,
  "merchant": "MUmfEGv5bMpSJ9k5TFRUjkmm",
  "merchant_identity": "ID6UfSm1d4WPiWgLYmbyeo3H",
  "messages": [],
  "raw": null,
  "receipt_last_printed_at": null,
  "security_code_verification": "MATCHED",
  "source": "PIkxmtueemLD6dN9ZoWGHT44",
  "state": "SUCCEEDED",
  "supplemental_fee": null,
  "tags": {
    "order_number": "21DFASJSAKAS"
  },
  "trace_id": "0504c0cc-7665-4555-90c3-c460330acf2e",
  "transfer": null,
  "void_state": "UNATTEMPTED",
  "_links": {
    "self": { … },
    "application": { … },
    "merchant_identity": { … }
  }
}
```

---

### 4. Capture an Authorization

**Endpoint:** `PUT /authorizations/{authorization_id}`

**Description:** Use a PUT request to capture an `Authorization`. If captured successfully, the `transfer` field of the `Authorization` will contain the ID of the `Transfer` resource that moves funds.

**Request Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Finix-Version | string | Yes | Specify the API version. Default: `2022-02-01` |
| Content-Type | string | Yes | Must be `application/json` |

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| authorization_id | string | Yes | ID of `Authorization` to capture |

**Request Body:**
```json
{
  "capture_amount": 100,
  "fee": 0
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| capture_amount | integer (int64) | Yes | The amount of the `Authorization` you would like to capture in cents. Must be less than or equal to the `amount` of the `Authorization` |
| fee | integer (int64) | No | The minimum amount of the `Authorization` you'd like to collect as your fee in cents. Defaults to zero (must be less than or equal to the `amount`). If the fees applied by the 'Fee Profile' are higher than the value passed in 'fee', 'fee' will not be applied and have no effect. If the fees applied by the 'Fee Profile' are lower than the value passed in 'fee', an additional fee is be applied, in addition to the fees generated by the `Fee Profile` |
| split_transfers | Array of objects or null | No | Split transfer configuration |

**cURL Example:**
```bash
curl -i -X PUT \
  -u USfdccsr1Z5iVbXDyYt7hjZZ:313636f3-fac2-45a7-bff7-a334b93e7bda \
  https://finix.sandbox-payments-api.com/authorizations/AUg8unYpnWBEY1AdVUDkdQYJ \
  -H 'Content-Type: application/json' \
  -H 'Finix-Version: 2022-02-01' \
  -d '{
    "capture_amount": 100,
    "fee": 0
  }'
```

**Response Codes:** 200, 400, 401, 403, 406, 422

**Response Headers:**
| Header | Type | Description |
|--------|------|-------------|
| date | string | Date and time of the API request |
| finix-apiuser-role | string | Role of the user who sent the API request. Enum: `ROLE_ADMIN`, `ROLE_PLATFORM`, `ROLE_PARTNER`, `ROLE_MERCHANT` |
| x-request-id | string | Unique identifier for the API request |

**Response Body (200):**
```json
{
  "id": "AUcmwpCN6yKJ2HGot6X4YSv7",
  "created_at": "2025-04-30T20:31:12.63Z",
  "updated_at": "2025-07-22T16:28:00.67Z",
  "3ds_redirect_url": null,
  "additional_buyer_charges": null,
  "additional_healthcare_data": null,
  "additional_purchase_data": null,
  "address_verification": "POSTAL_CODE_AND_STREET_MATCH",
  "amount": 100,
  "amount_requested": 100,
  "application": "APc9vhYcPsRuTSpKD9KpMtPe",
  "currency": "USD",
  "expires_at": "2025-05-07T20:31:12.63Z",
  "failure_code": null,
  "failure_message": null,
  "idempotency_id": null,
  "is_void": false,
  "merchant": "MU7noQ1wdgdAeAfymw2rfBMq",
  "merchant_identity": "IDjvxGeXBLKH1V9YnWm1CS4n",
  "messages": [],
  "raw": null,
  "receipt_last_printed_at": null,
  "security_code_verification": "MATCHED",
  "source": "PIkxmtueemLD6dN9ZoWGHT44",
  "state": "SUCCEEDED",
  "supplemental_fee": null,
  "tags": {},
  "trace_id": "836faa82-15e4-4945-8923-94253464ddc4",
  "transfer": "TRfbdBWj2Ww6a2j7XfiqEoV4",
  "void_state": "UNATTEMPTED",
  "_links": {
    "self": { … },
    "application": { … },
    "transfer": { … },
    "merchant_identity": { … }
  }
}
```

---

### 5. Void an Authorization

**Endpoint:** `PUT /authorizations/{authorization_id_void_to}`

**Description:** Use a PUT request to void an `Authorization`. If voided successfully, funds get released, and the transaction is incomplete. Additionally, a voided `Authorization` can no longer be captured. Depending on the cardholder's issuing bank, voids can take up to seven days to remove the `Authorization` hold.

**Request Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Finix-Version | string | Yes | Specify the API version. Default: `2022-02-01` |
| Content-Type | string | Yes | Must be `application/json` |

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| authorization_id_void_to | string | Yes | ID of `Authorization` to void |

**Request Body:**
```json
{
  "void_me": true
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| void_me | boolean | Yes | Set to **True** to void the `Authorization` |

**cURL Example:**
```bash
curl -i -X PUT \
  -u USfdccsr1Z5iVbXDyYt7hjZZ:313636f3-fac2-45a7-bff7-a334b93e7bda \
  https://finix.sandbox-payments-api.com/authorizations/AUnubzehgQfqcvJpoxhqja7k \
  -H 'Content-Type: application/json' \
  -H 'Finix-Version: 2022-02-01' \
  -d '{
    "void_me": true
  }'
```

**Response Codes:** 200, 401, 403, 406, 422

**Response Headers:**
| Header | Type | Description |
|--------|------|-------------|
| date | string | Date and time of the API request |
| finix-apiuser-role | string | Role of the user who sent the API request. Enum: `ROLE_ADMIN`, `ROLE_PLATFORM`, `ROLE_PARTNER`, `ROLE_MERCHANT` |
| x-request-id | string | Unique identifier for the API request |

**Response Body (200):**
```json
{
  "id": "AUcmwpCN6yKJ2HGot6X4YSv7",
  "created_at": "2025-04-30T20:31:12.63Z",
  "updated_at": "2025-07-22T16:28:00.67Z",
  "3ds_redirect_url": null,
  "additional_buyer_charges": null,
  "additional_healthcare_data": null,
  "additional_purchase_data": null,
  "address_verification": "POSTAL_CODE_AND_STREET_MATCH",
  "amount": 100,
  "amount_requested": 100,
  "application": "APc9vhYcPsRuTSpKD9KpMtPe",
  "currency": "USD",
  "expires_at": "2025-05-07T20:31:12.63Z",
  "failure_code": null,
  "failure_message": null,
  "idempotency_id": null,
  "is_void": true,
  "merchant": "MU7noQ1wdgdAeAfymw2rfBMq",
  "merchant_identity": "IDjvxGeXBLKH1V9YnWm1CS4n",
  "messages": [],
  "raw": null,
  "receipt_last_printed_at": null,
  "security_code_verification": "MATCHED",
  "source": "PIkxmtueemLD6dN9ZoWGHT44",
  "state": "CANCELED",
  "supplemental_fee": null,
  "tags": {},
  "trace_id": "836faa82-15e4-4945-8923-94253464ddc4",
  "transfer": null,
  "void_state": "VOIDED",
  "_links": {
    "self": { … },
    "application": { … },
    "merchant_identity": { … }
  }
}
```

---

## Other Resource Endpoints Mentioned

The following resource categories and endpoints are referenced but not fully documented in the provided source:

### Compliance Forms
- `GET /compliance_forms/{compliance_form_id}`
- `PUT /compliance_forms/{compliance_form_id}`
- `GET /compliance_forms`

### Devices
- `GET /devices`
- `GET /devices/{device_id}`
- `PUT /devices/{device_id}`
- `GET /devices/{device_id_connection}`
- `GET /devices/{device_id}/device_metrics`
- `POST /merchants/{merchant_id}/devices`

### Disputes
- `GET /disputes`
- `GET /disputes/{dispute_id}`
- `PUT /disputes/{dispute_id}`
- `POST /disputes/{dispute_id}/evidence`
- `GET /disputes/{dispute_id}/evidence`
- `GET /disputes/{dispute_id}/evidence/{evidence_id}`
- `PUT /disputes/{dispute_id}/evidence/{evidence_id}`
- `DELETE /disputes/{dispute_id}/evidence/{evidence_id}`

### Fees
- `GET /fees`
- `POST /fees`
- `GET /fees/{fee_id}`
- `PUT /fees/{fee_id}`

### Fee Profiles
- `POST /fee_profiles`
- `GET /fee_profiles`
- `GET /fee_profiles/{fee_profile_id}`

### Files
- `POST /files`
- `GET /files`
- `GET /files/{file_id}`
- `GET /files/{file_id}/external_links`
- `POST /files/{file_id}/external_links`
- `POST /files/{file_id}/upload`
- `GET /files/{file_id}/download`
- `GET /files/{file_id}/external_links/{external_link_id}`

### Identities
- `POST /identities`
- `GET /identities`
- `GET /identities/{identity_id}`
- `PUT /identities/{identity_id}`
- `POST /identities/{identity_id}/associated_identities`
- `GET /identities/{identity_id}/associated_identities`
- `GET /identities/{identity_id}/merchants`
- `POST /identities/{identity_id}/verifications`

### Merchants
- `POST /identities/{identity_id}/merchants`
- `GET /merchants`
- `GET /merchants/{merchant_id}`
- `PUT /merchants/{merchant_id}`
- `POST /merchants/{merchant_id}/verifications`

### Onboarding Forms
- `POST /onboarding_forms`
- `GET /onboarding_forms/{onboarding_form_id}`
- `POST /onboarding_forms/{onboarding_form_id}/links`

### Payment Instruments
- `POST /payment_instruments`
- `GET /payment_instruments`
- `GET /payment_instruments/{payment_instrument_id}`
- `PUT /payment_instruments/{payment_instrument_id}`
- `GET /payment_instruments/{payment_instrument_id}/instrument_history`
- `PUT /payment_instruments/{payment_instrument_id_verify}`
- `POST /payment_instruments/{payment_instrument_id_verify}/verifications`
- `POST /apple_pay_sessions`

### Settlements
- `GET /settlements`
- `GET /settlements/{settlement_id}`
- `PUT /settlements/{settlement_id}`
- `GET /settlements/{settlement_id}/entries`
- `DELETE /settlements/{settlement_id}/entries`
- `GET /settlements/{settlement_id}/funding_transfers`
- `DELETE /settlements/{settlement_id}/transfers`
- `GET /settlements/{settlement_id}/transfers`

### Settlement Queue Entries
- `GET /settlement_queue_entries`
- `PUT /settlement_queue_entries`
- `GET /settlement_queue_entries/{settlement_queue_entry_id}`

### Split Transfers
- `GET /split_transfers`
- `GET /split_transfers/{split_transfer_id}`
- `GET /split_transfers/{split_transfer_id}/fees`

### Transfers
- `POST /transfers`
- `GET /transfers`
- `GET /transfers/{transfer_id}`
- `PUT /transfers/{transfer_id}`
- `POST /transfers/{transfer_id}/reversals`
- `GET /transfers/{transfer_id}/reversals`

### Users
- `POST /applications/{application_id}/users`
- `GET /users`
- `GET /users/{user_id}`
- `PUT /users/{user_id}`

### Webhooks
- `POST /webhooks`
- `GET /webhooks`
- `GET /webhooks/{webhook_id}`
- `PUT /webhooks/{webhook_id}`

### Checkout Forms
- `POST /checkout_forms`
- `GET /checkout_forms`
- `GET /checkout_forms/{checkout_forms_id}`

### Payment Links
- `GET /payment_links`
- `POST /payment_links`
- `GET /payment_links/{payment_link_id}`
- `PUT /payment_links/{payment_link_id}`
- `GET /payment_links/{payment_link_id}/delivery-attempts`
- `POST /payment_links/{payment_link_id}/delivery-attempts`

### Payout Links
- `POST /payout_links`
- `GET /payout_links`
- `GET /payout_links/{payout_link_id}`
- `PUT /payout_links/{payout_link_id}`

### Receipts
- `POST /receipts`
- `GET /receipts/{receipt_id}`
- `POST /receipts/{receipt_id}/delivery_attempts`
- `GET /receipts/{receipt_id}/delivery_attempts`

### Subscriptions
- `POST /subscriptions`
- `GET /subscriptions`
- `GET /subscriptions/{subscription_id}`
- `PUT /subscriptions/{subscription_id}`
- `DELETE /subscriptions/{subscription_id}`
- `POST /subscriptions/{subscription_id}/subscription_balance_entries`
- `GET /subscriptions/{subscription_id}/subscription_balance_entries`
- `PUT /subscriptions/{subscription_id}/subscription_balance_entries/{subscription_balance_entry_id}`

### Subscription Links
- `POST /subscription_links`
- `GET /subscription_links`
- `GET /subscription_links/{subscription_link_id}`
- `PUT /subscription_links/{subscription_link_id}`

### Subscription Plans
- `POST /subscription_plans`
- `GET /subscription_plans`
- `GET /subscription_plans/{subscription_plan_id}`
- `PUT /subscription_plans/{subscription_plan_id}`

### Transfer Attempts
- `GET /transfer_attempts`
- `GET /transfer_attempts/{transfer_attempt_id}`

### Balances
- `GET /balances`
- `GET /balances/{balance_id}`
- `GET /balances/{balance_id}/balance_entries`
- `GET /balance_entries/{balance_entry_id}`

### Balance Adjustments
- `POST /balance_adjustments`
- `GET /balance_adjustments`

### Disbursement Rules
- `GET /disbursement_rules`
- `GET /disbursement_rules/current_usages`

### Application Profiles
- `GET /application_profiles`
- `GET /application_profiles/{application_profile_id}`
- `PUT /application_profiles/{application_profile_id}`

### Applications
- `POST /applications`
- `GET /applications`
- `GET /applications/{application_id}`
- `PUT /applications/{application_id}`

### Balance Transfers
- `POST /balance_transfers`
- `GET /balance_transfers`
- `GET /balance_transfers/{balance_transfers_id}`

### Merchant Profiles
- `GET /merchant_profiles`
- `GET /merchant_profiles/{merchant_profile_id}`
- `PUT /merchant_profiles/{merchant_profile_id}`

### Payout Profiles
- `GET /payout_profiles`
- `GET /payout_profiles/{payout_profile_id}`
- `PUT /payout_profiles/{payout_profile_id}`
- `GET /merchants/{merchant_id}/payout_profile`

### Review Queue Items
- `GET /review_queue`
- `GET /review_queue/{review_queue_item_id}`
- `PUT /review_queue/{review_queue_item_id}`

### Verifications
- `GET /merchants/{merchant_id}/verifications`
- `GET /verifications`
- `GET /verifications/{verification_id}`

---

## Flow Categories

### Payment/Authorization Flows
- **Authorization Creation:** `POST /authorizations` - Creates a card hold/reserves funds
- **Authorization Capture:** `PUT /authorizations/{authorization_id}` - Converts authorization to transfer
- **Authorization Void:** `PUT /authorizations/{authorization_id_void_to}` - Cancels authorization

### Status/Sync Endpoints
- **List Authorizations:** `GET /authorizations` - Retrieve all authorizations with filtering
- **Fetch Authorization:** `GET /authorizations/{authorization_id}` - Get single authorization details

### Other Flows Mentioned
- **Transfers:** Payment flow of funds to/from Payment Instruments
- **Settlements:** Batch processing of settlement entries
- **Disputes:** Chargeback and dispute management
- **Refunds:** Via reversals on transfers
- **Tokenization:** Via Payment Instruments
- **Webhooks:** Event notifications
- **Subscriptions:** Recurring payments
- **Payouts:** Including Payout Links and Balance Transfers

---

## Configuration Parameters

### API Version
- **Current Version:** `2022-02-01`
- **Header:** `Finix-Version`

### Request Timeout
- **Maximum Timeout:** 5 minutes

### Tags Configuration
- **Maximum key-value pairs:** 50
- **Maximum key length:** 40 characters
- **Maximum value length:** 500 characters
- **Special Characters:** Not allowed (e.g., `\`, `,`, `"`, `'`)

### Idempotency
- **Available on:** `/transfers`, `/authorizations`, `/transfers/{id}/reversals`
- **Field:** `idempotency_id`
- **Scope:** Checks against previous requests on the same endpoint

### Currencies
- **Format:** ISO 4217 3-letter currency codes
- **Examples:** USD, EUR, GBP, etc. (169+ supported currencies)

---

## HTTP Status Codes

| Code | Definition | Explanation |
|------|------------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource successfully created |
| 400 | Bad Request | Could not parse request. Verify valid JSON |
| 401 | Unauthorized | Could not authenticate. Verify username and password |
| 402 | Upstream Processor Error | Errors caused by 3rd-party service(s) |
| 403 | Forbidden | Credentials do not have correct permissions |
| 404 | Not Found | Could not find the specified resource |
| 405 | Method Not Allowed | Resource does not support the HTTP Method used |
| 406 | Not Acceptable | Server could not accept the submitted request |
| 409 | Conflict | Request conflicts with current state of server |
| 422 | Unprocessable Entity | Parameters valid but request failed |
| 500 | Internal Server Error | Problem with server. Try again later |

---

## Environment Variables/Settings

### Sandbox Environment
- **Base URL:** `https://finix.sandbox-payments-api.com`
- **Purpose:** Developing and testing integration

### Live Environment
- **Base URL:** `https://finix.live-payments-api.com`
- **Purpose:** Processing payments
- **Access:** Contact Finix point-of-contact

### Note
Environments are entirely separate and do not share API Credentials.

---

## Supported Features

### Payment Features
- Authorizations (card holds)
- Captures
- Voids
- Level 2 and Level 3 Processing
- 3D Secure
- Card Present transactions
- Buyer Charges
- Partial Authorizations
- Recurring and Unscheduled payments
- Gaming transactions
- HSA/FSA Card for Non-Healthcare MCC
- Fraud Detection

### Low-Code / No-Code
- Checkout Forms
- Payment Links
- Payout Links
- Receipts
- Subscriptions
- Subscription Links
- Subscription Plans

### Payout Resources
- Balances
- Balance Adjustments
- Disbursement Rules

### Core PayFac Resources
- Application Profiles
- Applications
- Balance Transfers
- Merchant Profiles
- Payout Profiles
- Review Queue Items
- Verifications

### Regions/Limitations
- **Subscriptions:** Available in United States only
- **Subscription Payment Methods:** Recurring card payments and ACH (USA)

---

## Integration Requirements

### Authentication
- HTTP Basic Authentication required for all requests
- Separate credentials for Sandbox and Live environments

### Request Format
- JSON encoded requests and responses
- `Content-Type: application/json` header required

### Versioning
- API version controlled via `Finix-Version` header
- Breaking changes may result in new dated API versions

### Idempotency
- Use `idempotency_id` field to ensure requests are performed only once
- Available on Authorization and Transfer resources

---

## Notes
- Full endpoint details are only provided for Authorizations in the source document
- Other endpoints are listed but not fully documented
- For complete documentation of other resources, refer to the respective documentation pages
- Visa is ending its Level 2 offering in April 2026