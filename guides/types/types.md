# UCS Type System Guide

Comprehensive guide to UCS connector-service type system, covering all payment flows and data structures.

## Core UCS Type Imports

```rust
// Essential UCS imports - use these in every connector
use domain_types::{
    // Flow types for all operations
    connector_flow::{
        Authorize, Capture, Void, Refund, PSync, RSync,
        CreateOrder, CreateSessionToken, SetupMandate, 
        DefendDispute, SubmitEvidence, Accept
    },
    
    // Request/Response types for all flows
    connector_types::{
        // Payment flow types
        PaymentsAuthorizeData, PaymentsCaptureData, PaymentVoidData,
        PaymentsSyncData, PaymentsResponseData,
        
        // Refund flow types
        RefundsData, RefundSyncData, RefundsResponseData,
        
        // Advanced flow types
        PaymentCreateOrderData, PaymentCreateOrderResponse,
        SessionTokenRequestData, SessionTokenResponseData,
        SetupMandateRequestData,
        
        // Dispute types
        DisputeFlowData, DisputeResponseData,
        AcceptDisputeData, DisputeDefendData, SubmitEvidenceData,
        
        // Webhook types
        WebhookDetailsResponse, RefundWebhookDetailsResponse,
        
        // Common types
        ResponseId, RequestDetails, ConnectorSpecifications,
        SupportedPaymentMethodsExt, ConnectorWebhookSecrets,
    },
    
    // Enhanced router data
    router_data_v2::RouterDataV2,
    
    // Payment method data (all types)
    payment_method_data::{
        PaymentMethodData, PaymentMethodDataTypes, DefaultPCIHolder,
        Card, Wallet, BankTransfer, BuyNowPayLater, Voucher, 
        Crypto, GiftCard, BankRedirect, CardRedirect
    },
    
    // Address and customer data
    payment_address::{Address, AddressDetails},
    
    // Error types
    errors,
    
    // Router data and auth
    router_data::{ConnectorSpecificConfig, ErrorResponse},
    router_data_v2::RouterDataV2,
    router_response_types::Response,
    
    // Utility types
    types::{
        self, Connectors, ConnectorInfo, FeatureStatus,
        PaymentMethodDetails, PaymentMethodSpecificFeatures,
        SupportedPaymentMethods, CardSpecificFeatures,
        PaymentMethodDataType
    },
    utils,
};

// Interface types
use interfaces::{
    api::ConnectorCommon,
    connector_integration_v2::ConnectorIntegrationV2,
    connector_types::{self, ConnectorValidation, is_mandate_supported},
    events::connector_api_logs::ConnectorEvent,
};

// Common utilities
use common_enums::{
    AttemptStatus, CaptureMethod, CardNetwork, EventClass,
    PaymentMethod, PaymentMethodType, Currency, CountryAlpha2
};
use common_utils::{
    errors::CustomResult, 
    ext_traits::ByteSliceExt,
    pii::{SecretSerdeValue, Email, IpAddress},
    types::{StringMinorUnit, MinorUnit, StringMajorUnit, FloatMajorUnit},
    request::Method,
};

// Masking utilities
use hyperswitch_masking::{Mask, Maskable};

// Serialization
use serde::{Serialize, Deserialize};
```

## RouterDataV2 - The Core Data Type

### RouterDataV2 Struct Definition

`RouterDataV2` is the central data structure passed through every connector flow. It has **4 type parameters**:

```rust
pub struct RouterDataV2<Flow, ResourceCommonData, FlowSpecificRequest, FlowSpecificResponse> {
    pub flow: PhantomData<Flow>,
    pub resource_common_data: ResourceCommonData,     // PaymentFlowData or RefundFlowData
    pub connector_config: ConnectorSpecificConfig,    // Typed per-connector auth config
    pub request: FlowSpecificRequest,                 // Flow-specific request data
    pub response: Result<FlowSpecificResponse, ErrorResponse>,  // Flow-specific response
}
```

**IMPORTANT**: The auth field is `connector_config: ConnectorSpecificConfig`, NOT `connector_auth_type: ConnectorAuthType`. The old `ConnectorAuthType` is a legacy type used only in backward-compatibility bridges.

### Flow Type Signatures

| Flow | ResourceCommonData | FlowSpecificRequest | FlowSpecificResponse |
|------|-------------------|---------------------|---------------------|
| Authorize | `PaymentFlowData` | `PaymentsAuthorizeData<T>` | `PaymentsResponseData` |
| PSync | `PaymentFlowData` | `PaymentsSyncData` | `PaymentsResponseData` |
| Capture | `PaymentFlowData` | `PaymentsCaptureData` | `PaymentsResponseData` |
| Void | `PaymentFlowData` | `PaymentVoidData` | `PaymentsResponseData` |
| Refund | `RefundFlowData` | `RefundsData` | `RefundsResponseData` |
| RSync | `RefundFlowData` | `RefundSyncData` | `RefundsResponseData` |
| SetupMandate | `PaymentFlowData` | `SetupMandateRequestData<T>` | `PaymentsResponseData` |
| RepeatPayment | `PaymentFlowData` | `RepeatPaymentData<T>` | `PaymentsResponseData` |

### Full Router Data Type Examples

```rust
// Payment flows use PaymentFlowData as ResourceCommonData
type AuthorizeRouterData<T> = RouterDataV2<
    Authorize,               // Flow type
    PaymentFlowData,         // Resource common data
    PaymentsAuthorizeData<T>, // Request data
    PaymentsResponseData     // Response data
>;

type CaptureRouterData = RouterDataV2<Capture, PaymentFlowData, PaymentsCaptureData, PaymentsResponseData>;
type VoidRouterData = RouterDataV2<Void, PaymentFlowData, PaymentVoidData, PaymentsResponseData>;
type SyncRouterData = RouterDataV2<PSync, PaymentFlowData, PaymentsSyncData, PaymentsResponseData>;

// Refund flows use RefundFlowData as ResourceCommonData
type RefundRouterData = RouterDataV2<Refund, RefundFlowData, RefundsData, RefundsResponseData>;
type RefundSyncRouterData = RouterDataV2<RSync, RefundFlowData, RefundSyncData, RefundsResponseData>;
```

### ResponseRouterData - Response Transformer Input

Response transformers receive a `ResponseRouterData` wrapper that pairs the connector's HTTP response with the original router data:

```rust
pub struct ResponseRouterData<Response, RouterData> {
    pub response: Response,      // Deserialized connector response struct
    pub router_data: RouterData, // The original RouterDataV2
    pub http_code: u16,          // HTTP status code
}
```

Usage in response TryFrom:
```rust
impl<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize>
    TryFrom<ResponseRouterData<ConnectorPaymentResponse,
        RouterDataV2<Authorize, PaymentFlowData, PaymentsAuthorizeData<T>, PaymentsResponseData>>>
    for RouterDataV2<Authorize, PaymentFlowData, PaymentsAuthorizeData<T>, PaymentsResponseData>
{
    type Error = error_stack::Report<errors::ConnectorError>;
    fn try_from(item: ResponseRouterData<...>) -> Result<Self, Self::Error> {
        // item.response  -- the deserialized connector response
        // item.router_data  -- the original RouterDataV2
        // item.http_code  -- HTTP status code
    }
}
```

## PaymentFlowData - Resource Common Data for Payment Flows

This struct is available as `router_data.resource_common_data` in payment flows (Authorize, PSync, Capture, Void).

```rust
pub struct PaymentFlowData {
    pub merchant_id: MerchantId,
    pub customer_id: Option<CustomerId>,
    pub connector_customer: Option<String>,
    pub payment_id: String,
    pub attempt_id: String,
    pub status: AttemptStatus,
    pub payment_method: PaymentMethod,
    pub description: Option<String>,
    pub return_url: Option<String>,
    pub address: PaymentAddress,
    pub auth_type: AuthenticationType,
    pub amount_captured: Option<i64>,
    pub minor_amount_captured: Option<MinorUnit>,
    pub minor_amount_capturable: Option<MinorUnit>,
    pub access_token: Option<AccessTokenResponseData>,
    pub session_token: Option<String>,
    pub reference_id: Option<String>,
    pub payment_method_token: Option<PaymentMethodToken>,
    pub preprocessing_id: Option<String>,
    pub connector_api_version: Option<String>,
    pub connector_request_reference_id: String,  // Unique reference for this request
    pub test_mode: Option<bool>,
    pub connector_http_status_code: Option<u16>,
    pub connectors: Connectors,                  // Contains base URLs for all connectors
    pub recurring_mandate_payment_data: Option<RecurringMandatePaymentData>,
    pub order_details: Option<Vec<OrderDetailsWithAmount>>,
    pub minor_amount_authorized: Option<MinorUnit>,
    // ... other fields
}
```

**Key access patterns:**
```rust
// Get the connector's base URL
let base_url = &req.resource_common_data.connectors.{connector_name}.base_url;

// Get payment reference ID
let reference = &req.resource_common_data.connector_request_reference_id;

// Get billing address
let billing = req.resource_common_data.address.get_payment_method_billing();

// Get shipping address
let shipping = req.resource_common_data.address.get_shipping();
```

## RefundFlowData - Resource Common Data for Refund Flows

This struct is available as `router_data.resource_common_data` in refund flows (Refund, RSync).

```rust
pub struct RefundFlowData {
    pub merchant_id: MerchantId,
    pub status: RefundStatus,
    pub refund_id: Option<String>,
    pub connectors: Connectors,                    // Contains base URLs for all connectors
    pub connector_request_reference_id: String,
    pub access_token: Option<AccessTokenResponseData>,
    pub test_mode: Option<bool>,
    pub payment_method: Option<PaymentMethod>,
    // ... other fields
}
```

**Key access patterns:**
```rust
// Get the connector's base URL for refund flows
let base_url = &req.resource_common_data.connectors.{connector_name}.base_url;
```

## Flow Request Data Types

### PaymentsAuthorizeData - Authorize Flow Request

Most commonly used fields (full struct has 40+ fields):

```rust
pub struct PaymentsAuthorizeData<T: PaymentMethodDataTypes> {
    pub payment_method_data: PaymentMethodData<T>,
    pub amount: MinorUnit,                              // Total amount (original + surcharge + tax)
    pub minor_amount: MinorUnit,                        // Amount in minor units
    pub currency: Currency,
    pub email: Option<Email>,
    pub customer_name: Option<String>,
    pub capture_method: Option<CaptureMethod>,          // Automatic or Manual
    pub confirm: bool,
    pub router_return_url: Option<String>,
    pub webhook_url: Option<String>,
    pub complete_authorize_url: Option<String>,
    pub mandate_id: Option<MandateIds>,
    pub setup_future_usage: Option<FutureUsage>,
    pub off_session: Option<bool>,
    pub browser_info: Option<BrowserInformation>,
    pub enrolled_for_3ds: Option<bool>,
    pub payment_method_type: Option<PaymentMethodType>,
    pub customer_id: Option<CustomerId>,
    pub metadata: Option<SecretSerdeValue>,
    pub authentication_data: Option<AuthenticationData>,
    pub billing_descriptor: Option<BillingDescriptor>,
    pub merchant_order_id: Option<String>,
    pub shipping_cost: Option<MinorUnit>,
    pub setup_mandate_details: Option<MandateData>,
    pub connector_feature_data: Option<SecretSerdeValue>,
    pub order_tax_amount: Option<MinorUnit>,
    pub split_payments: Option<SplitPaymentsRequest>,
    pub session_token: Option<String>,
    pub access_token: Option<AccessTokenResponseData>,
    pub customer_acceptance: Option<CustomerAcceptance>,
    pub related_transaction_id: Option<String>,
    pub payment_experience: Option<PaymentExperience>,
    pub request_incremental_authorization: Option<bool>,
    pub merchant_account_id: Option<String>,
    pub locale: Option<String>,
    pub redirect_response: Option<ContinueRedirectionResponse>,
}
```

### PaymentsCaptureData - Capture Flow Request

```rust
pub struct PaymentsCaptureData {
    pub amount_to_capture: i64,
    pub minor_amount_to_capture: MinorUnit,      // Preferred: use this for amount
    pub currency: Currency,
    pub connector_transaction_id: ResponseId,     // The original authorize transaction ID
    pub multiple_capture_data: Option<MultipleCaptureRequestData>,
    pub capture_method: Option<CaptureMethod>,
    pub browser_info: Option<BrowserInformation>,
    pub metadata: Option<SecretSerdeValue>,
    pub merchant_order_id: Option<String>,
    pub connector_feature_data: Option<SecretSerdeValue>,
}
```

### PaymentVoidData - Void Flow Request

```rust
pub struct PaymentVoidData {
    pub connector_transaction_id: String,         // The original authorize transaction ID
    pub cancellation_reason: Option<String>,
    pub amount: Option<MinorUnit>,
    pub currency: Option<Currency>,
    pub browser_info: Option<BrowserInformation>,
    pub metadata: Option<SecretSerdeValue>,
    pub merchant_order_id: Option<String>,
    pub connector_feature_data: Option<SecretSerdeValue>,
}
```

### PaymentsSyncData - PSync Flow Request

```rust
pub struct PaymentsSyncData {
    pub connector_transaction_id: ResponseId,     // Transaction ID to sync
    pub encoded_data: Option<String>,
    pub capture_method: Option<CaptureMethod>,
    pub sync_type: SyncRequestType,
    pub mandate_id: Option<MandateIds>,
    pub payment_method_type: Option<PaymentMethodType>,
    pub currency: Currency,
    pub amount: MinorUnit,
    pub connector_feature_data: Option<SecretSerdeValue>,
}
```

**Helper method:** `req.request.get_connector_transaction_id()` returns `CustomResult<String, ConnectorError>`.

### RefundsData - Refund Flow Request

```rust
pub struct RefundsData {
    pub refund_id: String,
    pub connector_transaction_id: String,         // Original payment transaction ID
    pub connector_refund_id: Option<String>,
    pub currency: Currency,
    pub payment_amount: i64,
    pub refund_amount: i64,
    pub minor_payment_amount: MinorUnit,
    pub minor_refund_amount: MinorUnit,           // Preferred: use this for refund amount
    pub reason: Option<String>,
    pub webhook_url: Option<String>,
    pub refund_status: RefundStatus,
    pub capture_method: Option<CaptureMethod>,
    pub browser_info: Option<BrowserInformation>,
    pub merchant_account_id: Option<String>,
    pub connector_feature_data: Option<SecretSerdeValue>,
}
```

### RefundSyncData - RSync Flow Request

```rust
pub struct RefundSyncData {
    pub connector_transaction_id: String,
    pub connector_refund_id: String,              // Refund ID to sync
    pub reason: Option<String>,
    pub refund_status: RefundStatus,
    pub connector_feature_data: Option<SecretSerdeValue>,
}
```

## Flow Response Data Types

### PaymentsResponseData - Payment Flow Response

Used for Authorize, PSync, Capture, and Void response mapping:

```rust
pub enum PaymentsResponseData {
    TransactionResponse {
        resource_id: ResponseId,
        redirection_data: Option<Box<RedirectForm>>,
        connector_metadata: Option<serde_json::Value>,
        mandate_reference: Option<Box<MandateReference>>,
        network_txn_id: Option<String>,
        connector_response_reference_id: Option<String>,
        incremental_authorization_allowed: Option<bool>,
        status_code: u16,                            // HTTP status code from connector
    },
    // Other variants for specialized flows (SdkSessionToken, Authenticate, etc.)
}
```

### RefundsResponseData - Refund Flow Response

Used for Refund and RSync response mapping:

```rust
pub struct RefundsResponseData {
    pub connector_refund_id: String,
    pub refund_status: RefundStatus,
    pub status_code: u16,                            // HTTP status code from connector
}
```

### ResponseId enum

```rust
pub enum ResponseId {
    ConnectorTransactionId(String),    // Most common - the connector's transaction ID
    EncodedData(String),               // Base64/encoded reference
    NoResponseId,                      // No ID available
}
```

## Payment Method Data Types

### Comprehensive Payment Method Handling
```rust
// Handle all payment method types
match payment_method_data {
    // Card payments - most common
    PaymentMethodData::Card(card_data) => {
        // card_data fields:
        // - card_number: cards::CardNumber
        // - card_exp_month: SecretSerdeValue
        // - card_exp_year: SecretSerdeValue  
        // - card_cvc: SecretSerdeValue
        // - card_holder_name: Option<SecretSerdeValue>
        // - card_network: Option<CardNetwork>
        // - card_issuer: Option<String>
        // - card_type: Option<String>
        // - nick_name: Option<SecretSerdeValue>
    }
    
    // Digital wallets
    PaymentMethodData::Wallet(wallet_data) => match wallet_data {
        WalletData::ApplePay(apple_pay) => {
            // apple_pay fields:
            // - payment_data: SecretSerdeValue (encrypted payment data)
            // - payment_method: ApplepayPaymentMethod
            // - transaction_identifier: Option<String>
        }
        
        WalletData::GooglePay(google_pay) => {
            // google_pay fields:
            // - type_: String (e.g., "CARD", "PAYPAL")
            // - description: String
            // - info: GooglePayPaymentMethodInfo
            // - tokenization_specification: Option<GooglePayTokenizationSpecification>
        }
        
        WalletData::PaypalRedirect(paypal) => {
            // paypal fields:
            // - email: Option<Email>
        }
        
        WalletData::SamsungPay(samsung_pay) => {
            // Samsung Pay encrypted payment data
        }
        
        WalletData::WeChatPayRedirect(wechat) => {
            // WeChat Pay specific data
        }
        
        WalletData::AliPayRedirect(alipay) => {
            // Alipay specific data
        }
        
        WalletData::MbWayRedirect(mbway) => {
            // MB Way (Portuguese wallet)
            // - telephone_number: SecretSerdeValue
        }
        
        WalletData::TouchNGoRedirect(touchngo) => {
            // Touch 'n Go (Malaysian wallet)
        }
        
        WalletData::GrabPayRedirect(grabpay) => {
            // GrabPay (Southeast Asian wallet)
        }
        
        // Add all wallet variants your connector supports
    }
    
    // Bank transfers
    PaymentMethodData::BankTransfer(bank_data) => match bank_data {
        BankTransferData::AchBankTransfer => {
            // ACH bank transfer (US)
            // Requires: account_number, routing_number, account_type
        }
        
        BankTransferData::SepaBankTransfer => {
            // SEPA bank transfer (Europe)
            // Requires: iban, bic (optional)
        }
        
        BankTransferData::BacsBankTransfer => {
            // BACS bank transfer (UK)
            // Requires: account_number, sort_code
        }
        
        BankTransferData::MultibancoBankTransfer => {
            // Multibanco (Portugal)
        }
        
        BankTransferData::PermataBankTransfer => {
            // Permata Bank (Indonesia)
        }
        
        BankTransferData::BcaBankTransfer => {
            // BCA Bank (Indonesia)
        }
        
        BankTransferData::BniVaBankTransfer => {
            // BNI Virtual Account (Indonesia)
        }
        
        BankTransferData::BriVaBankTransfer => {
            // BRI Virtual Account (Indonesia)
        }
        
        BankTransferData::CimbVaBankTransfer => {
            // CIMB Virtual Account (Indonesia/Malaysia)
        }
        
        BankTransferData::DanamonVaBankTransfer => {
            // Danamon Virtual Account (Indonesia)
        }
        
        BankTransferData::LocalBankTransfer => {
            // Generic local bank transfer
            // Fields vary by country
        }
        
        // Add all bank transfer types
    }
    
    // Buy Now Pay Later
    PaymentMethodData::BuyNowPayLater(bnpl_data) => match bnpl_data {
        BuyNowPayLaterData::KlarnaRedirect => {
            // Klarna BNPL
        }
        
        BuyNowPayLaterData::AffirmRedirect => {
            // Affirm BNPL
        }
        
        BuyNowPayLaterData::AfterpayClearpayRedirect => {
            // Afterpay/Clearpay BNPL
        }
        
        BuyNowPayLaterData::AlmaRedirect => {
            // Alma BNPL (French)
        }
        
        BuyNowPayLaterData::AtomeRedirect => {
            // Atome BNPL (Southeast Asia)
        }
        
        // Add all BNPL providers
    }
    
    // Cash and voucher payments
    PaymentMethodData::Voucher(voucher_data) => match voucher_data {
        VoucherData::BoletoRedirect => {
            // Boleto (Brazil)
            // - social_security_number: Option<SecretSerdeValue>
        }
        
        VoucherData::OxxoRedirect => {
            // OXXO (Mexico)
        }
        
        VoucherData::SevenElevenRedirect => {
            // 7-Eleven convenience store
        }
        
        VoucherData::LawsonRedirect => {
            // Lawson convenience store (Japan)
        }
        
        VoucherData::FamilyMartRedirect => {
            // FamilyMart convenience store
        }
        
        VoucherData::AlfamartRedirect => {
            // Alfamart convenience store (Indonesia)
        }
        
        VoucherData::IndomaretRedirect => {
            // Indomaret convenience store (Indonesia)
        }
        
        // Add all voucher types
    }
    
    // Bank redirects (online banking)
    PaymentMethodData::BankRedirect(bank_redirect) => match bank_redirect {
        BankRedirectData::BancontactCard => {
            // Bancontact (Belgium)
        }
        
        BankRedirectData::Blik => {
            // BLIK (Poland)
            // - blik_code: Option<SecretSerdeValue>
        }
        
        BankRedirectData::Eps => {
            // EPS (Austria)
            // - bank_name: Option<String>
        }
        
        BankRedirectData::Giropay => {
            // Giropay (Germany)
            // - bank_account_bic: Option<SecretSerdeValue>
            // - bank_account_iban: Option<SecretSerdeValue>
        }
        
        BankRedirectData::Ideal => {
            // iDEAL (Netherlands)
            // - bank_name: Option<String>
        }
        
        BankRedirectData::OnlineBankingCzechRepublic => {
            // Czech Republic online banking
            // - issuer: String
        }
        
        BankRedirectData::OnlineBankingFinland => {
            // Finland online banking
        }
        
        BankRedirectData::OnlineBankingPoland => {
            // Poland online banking
            // - issuer: String
        }
        
        BankRedirectData::OnlineBankingSlovakia => {
            // Slovakia online banking
            // - issuer: String
        }
        
        BankRedirectData::Przelewy24 => {
            // Przelewy24 (Poland)
            // - bank_name: Option<String>
            // - billing_details: Option<BillingDetails>
        }
        
        BankRedirectData::Sofort => {
            // Sofort (Germany/Austria)
            // - preferred_language: Option<String>
        }
        
        BankRedirectData::Trustly => {
            // Trustly (Nordic countries)
        }
        
        // Add all bank redirect methods
    }
    
    // Card redirects (3DS and similar)
    PaymentMethodData::CardRedirect(card_redirect) => match card_redirect {
        CardRedirectData::Knet => {
            // KNET (Kuwait)
        }
        
        CardRedirectData::Benefit => {
            // Benefit (Bahrain)
        }
        
        CardRedirectData::CardRedirect => {
            // Generic card redirect for 3DS
        }
    }
    
    // Cryptocurrency
    PaymentMethodData::Crypto(crypto_data) => match crypto_data {
        CryptoData::CryptoCurrencyRedirect => {
            // Generic crypto redirect
            // - network: Option<String> (e.g., "bitcoin", "ethereum")
        }
    }
    
    // Gift cards
    PaymentMethodData::GiftCard(gift_card) => match gift_card {
        GiftCardData::Givex(givex) => {
            // Givex gift card
            // - number: cards::CardNumber
            // - cvc: SecretSerdeValue
        }
        
        GiftCardData::PaySafeCard => {
            // PaySafeCard
        }
    }
}
```

## Address and Customer Types

### Address Handling
```rust
// Address structure in UCS
pub struct Address {
    pub line1: Option<SecretSerdeValue>,
    pub line2: Option<SecretSerdeValue>,
    pub line3: Option<SecretSerdeValue>,
    pub city: Option<String>,
    pub state: Option<SecretSerdeValue>,
    pub zip: Option<SecretSerdeValue>,
    pub country: Option<CountryAlpha2>,
    pub first_name: Option<SecretSerdeValue>,
    pub last_name: Option<SecretSerdeValue>,
}

// Accessing address from RouterDataV2 (via resource_common_data)
let billing = router_data.resource_common_data.address.get_payment_method_billing();
let shipping = router_data.resource_common_data.address.get_shipping();

// Convert to connector format
fn build_connector_address(address: &Address) -> ConnectorAddress {
    ConnectorAddress {
        street: address.line1.clone(),
        street2: address.line2.clone(),
        city: address.city.clone(),
        state: address.state.clone(),
        postal_code: address.zip.clone(),
        country: address.country.clone(),
        first_name: address.first_name.clone(),
        last_name: address.last_name.clone(),
    }
}
```

### Customer Information
```rust
// Customer data accessed via resource_common_data and request
let customer_id = router_data.resource_common_data.customer_id.clone();
let email = router_data.request.email.clone();
let customer_name = router_data.request.customer_name.clone();

// Browser information for 3DS
let browser_info = router_data.request.browser_info.as_ref();
```

## Amount and Currency Types

### Amount Handling
```rust
// UCS amount types
use common_utils::types::{
    MinorUnit,        // For amounts in minor units (cents)
    StringMinorUnit,  // String representation of minor units
    StringMajorUnit,  // String representation of major units (dollars)
    FloatMajorUnit,   // Float representation of major units
};

// Convert between types
let minor_amount: MinorUnit = router_data.request.amount;
let amount_string = minor_amount.to_string();
let amount_f64 = utils::to_currency_base_unit(minor_amount, currency)?;

// Currency handling
use common_enums::Currency;
let currency: Currency = router_data.request.currency;
let currency_string = currency.to_string();

// Zero decimal currencies (amounts don't have decimal places)
let is_zero_decimal = matches!(currency, 
    Currency::JPY | Currency::KRW | Currency::VND | 
    Currency::CLP | Currency::ISK | Currency::XOF
);
```

## Authentication Types - ConnectorSpecificConfig

**IMPORTANT**: UCS uses `ConnectorSpecificConfig` (NOT the legacy `ConnectorAuthType`). Each connector has a named variant with semantically-named credential fields.

### ConnectorSpecificConfig Enum (per-connector typed auth)

The `ConnectorSpecificConfig` enum has one variant per connector. Each variant contains:
- **Named credential fields** specific to that connector (e.g., `api_key`, `merchant_account`, `username`, `password`)
- **`base_url: Option<String>`** for runtime URL override

Examples of existing variants:
```rust
pub enum ConnectorSpecificConfig {
    // Single-key connectors (Bearer token auth)
    Stripe { api_key: Secret<String>, base_url: Option<String> },
    Paystack { api_key: Secret<String>, base_url: Option<String> },

    // Two-key connectors
    Razorpay { api_key: Secret<String>, api_secret: Option<Secret<String>>, base_url: Option<String> },
    Bluesnap { username: Secret<String>, password: Secret<String>, base_url: Option<String> },

    // Three-key connectors
    Adyen { api_key: Secret<String>, merchant_account: Secret<String>, review_key: Option<Secret<String>>, base_url: Option<String>, dispute_base_url: Option<String> },
    Checkout { api_key: Secret<String>, api_secret: Secret<String>, processing_channel_id: Secret<String>, base_url: Option<String> },

    // Four-key connectors
    Finix { finix_user_name: Secret<String>, finix_password: Secret<String>, merchant_identity_id: Secret<String>, merchant_id: Secret<String>, base_url: Option<String> },
}
```

### Defining Connector Auth Type (in transformers.rs)

```rust
use domain_types::router_data::ConnectorSpecificConfig;

#[derive(Debug, Clone)]
pub struct {ConnectorName}AuthType {
    pub api_key: Secret<String>,
    // Add fields matching your ConnectorSpecificConfig variant
}

impl TryFrom<&ConnectorSpecificConfig> for {ConnectorName}AuthType {
    type Error = error_stack::Report<errors::ConnectorError>;

    fn try_from(auth_type: &ConnectorSpecificConfig) -> Result<Self, Self::Error> {
        match auth_type {
            ConnectorSpecificConfig::{ConnectorName} { api_key, .. } => Ok(Self {
                api_key: api_key.to_owned(),
            }),
            _ => Err(error_stack::report!(
                errors::ConnectorError::FailedToObtainAuthType
            )),
        }
    }
}
```

### Using Auth in ConnectorCommon (in connector.rs)

```rust
fn get_auth_header(
    &self,
    auth_type: &ConnectorSpecificConfig,    // NOT ConnectorAuthType
) -> CustomResult<Vec<(String, Maskable<String>)>, errors::ConnectorError> {
    let auth = {connector_name}::{ConnectorName}AuthType::try_from(auth_type)
        .change_context(errors::ConnectorError::FailedToObtainAuthType)?;
    Ok(vec![(
        headers::AUTHORIZATION.to_string(),
        format!("Bearer {}", auth.api_key.peek()).into(),
    )])
}
```

### Using Auth in build_headers Member Function

```rust
// In create_all_prerequisites! member_functions block:
pub fn build_headers<F, FCD, Req, Res>(
    &self,
    req: &RouterDataV2<F, FCD, Req, Res>,
) -> CustomResult<Vec<(String, Maskable<String>)>, errors::ConnectorError> {
    let mut header = vec![(
        headers::CONTENT_TYPE.to_string(),
        "application/json".to_string().into(),
    )];
    let mut api_key = self.get_auth_header(&req.connector_config)?;  // NOT connector_auth_type
    header.append(&mut api_key);
    Ok(header)
}
```

### Using Auth in Transformers (request construction)

```rust
// Extract auth from router_data.connector_config
let auth = {ConnectorName}AuthType::try_from(&item.router_data.connector_config)?;
let api_key = auth.api_key.peek().to_string();
```

### Auth Patterns by API Type

| API Auth Method | ConnectorSpecificConfig Fields | Header Format |
|---|---|---|
| Bearer Token | `api_key` | `Authorization: Bearer {api_key}` |
| Basic Auth | `username, password` | `Authorization: Basic {base64(user:pass)}` |
| API Key Header | `api_key` | `X-Api-Key: {api_key}` or custom header |
| Multiple Keys | `api_key, merchant_account, ...` | Multiple headers or body fields |

## Response Mapping Patterns

### Standard Payment Response Mapping

```rust
// In transformers.rs - response TryFrom implementation
impl<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize>
    TryFrom<ResponseRouterData<{ConnectorName}PaymentResponse,
        RouterDataV2<Authorize, PaymentFlowData, PaymentsAuthorizeData<T>, PaymentsResponseData>>>
    for RouterDataV2<Authorize, PaymentFlowData, PaymentsAuthorizeData<T>, PaymentsResponseData>
{
    type Error = error_stack::Report<errors::ConnectorError>;

    fn try_from(
        item: ResponseRouterData<{ConnectorName}PaymentResponse,
            RouterDataV2<Authorize, PaymentFlowData, PaymentsAuthorizeData<T>, PaymentsResponseData>>,
    ) -> Result<Self, Self::Error> {
        // Map connector status to UCS AttemptStatus
        let status = match item.response.status.as_str() {
            "authorized" | "success" => AttemptStatus::Authorized,
            "captured" | "completed" => AttemptStatus::Charged,
            "failed" | "error" | "declined" => AttemptStatus::Failure,
            "pending" | "processing" => AttemptStatus::Pending,
            "requires_action" | "requires_redirect" => AttemptStatus::AuthenticationPending,
            "cancelled" | "voided" => AttemptStatus::Voided,
            _ => AttemptStatus::Pending,
        };

        Ok(Self {
            status,
            response: Ok(PaymentsResponseData::TransactionResponse {
                resource_id: ResponseId::ConnectorTransactionId(item.response.id.clone()),
                redirection_data: None,       // Set if redirect needed (Box<RedirectForm>)
                mandate_reference: None,      // Set if mandate created
                connector_metadata: None,     // Set if connector returns metadata to store
                network_txn_id: None,         // Set if network transaction ID available
                connector_response_reference_id: Some(item.response.id.clone()),
                incremental_authorization_allowed: None,
                status_code: item.http_code,  // HTTP status code from the connector response
            }),
            ..item.router_data
        })
    }
}
```

### Refund Response Mapping

```rust
impl<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize>
    TryFrom<ResponseRouterData<{ConnectorName}RefundResponse,
        RouterDataV2<Refund, RefundFlowData, RefundsData, RefundsResponseData>>>
    for RouterDataV2<Refund, RefundFlowData, RefundsData, RefundsResponseData>
{
    type Error = error_stack::Report<errors::ConnectorError>;

    fn try_from(
        item: ResponseRouterData<{ConnectorName}RefundResponse,
            RouterDataV2<Refund, RefundFlowData, RefundsData, RefundsResponseData>>,
    ) -> Result<Self, Self::Error> {
        let refund_status = match item.response.status.as_str() {
            "success" | "completed" => RefundStatus::Success,
            "failed" | "error" => RefundStatus::Failure,
            "pending" | "processing" => RefundStatus::Pending,
            _ => RefundStatus::Pending,
        };

        Ok(Self {
            response: Ok(RefundsResponseData {
                connector_refund_id: item.response.id.clone(),
                refund_status,
                status_code: item.http_code,
            }),
            ..item.router_data
        })
    }
}
```

### Status Mapping Reference

**Payment AttemptStatus values:**
| UCS Status | When to use |
|---|---|
| `AttemptStatus::Authorized` | Payment authorized but not yet captured |
| `AttemptStatus::Charged` | Payment captured/completed successfully |
| `AttemptStatus::Pending` | Payment is processing |
| `AttemptStatus::Failure` | Payment failed |
| `AttemptStatus::Voided` | Payment was voided/cancelled |
| `AttemptStatus::AuthenticationPending` | Awaiting 3DS or redirect completion |
| `AttemptStatus::VoidFailed` | Void attempt failed |
| `AttemptStatus::CaptureInitiated` | Capture has been initiated |
| `AttemptStatus::CaptureFailed` | Capture failed |

**Refund RefundStatus values:**
| UCS Status | When to use |
|---|---|
| `RefundStatus::Success` | Refund completed |
| `RefundStatus::Failure` | Refund failed |
| `RefundStatus::Pending` | Refund is processing |

## Webhook Types

### Webhook Data Structures
```rust
// Incoming webhook structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectorWebhook {
    pub event_type: String,
    pub object_type: String,
    pub object_id: String,
    pub data: serde_json::Value,
}

// Webhook object reference types
use domain_types::connector_types::{
    ObjectReferenceId, PaymentIdType, RefundIdType,
    IncomingWebhookEvent, DisputePayload
};

// Map webhook events
match webhook.event_type.as_str() {
    "payment.authorized" => IncomingWebhookEvent::PaymentIntentAuthorizationSuccess,
    "payment.captured" => IncomingWebhookEvent::PaymentIntentSuccess,
    "payment.failed" => IncomingWebhookEvent::PaymentIntentFailure,
    "payment.cancelled" => IncomingWebhookEvent::PaymentIntentCancelled,
    "refund.succeeded" => IncomingWebhookEvent::RefundSuccess,
    "refund.failed" => IncomingWebhookEvent::RefundFailure,
    "dispute.created" => IncomingWebhookEvent::DisputeOpened,
    "dispute.won" => IncomingWebhookEvent::DisputeWon,
    "dispute.lost" => IncomingWebhookEvent::DisputeLost,
    _ => IncomingWebhookEvent::EventNotSupported,
}
```

## Utility Types

### Common Utility Functions
```rust
// Amount conversion utilities
use domain_types::utils;

// Convert minor to major units
let major_amount = utils::to_currency_base_unit(minor_amount, currency)?;

// Format amount for connector
let formatted_amount = utils::to_currency_base_unit_as_string(minor_amount, currency)?;

// Get unimplemented payment method error
let error = utils::get_unimplemented_payment_method_error_message("connector_name");
```

## Type Safety Best Practices

1. **Always use RouterDataV2** instead of RouterData
2. **Use ConnectorIntegrationV2** for all trait implementations
3. **Import from domain_types** not hyperswitch_domain_models
4. **Handle all payment method variants** explicitly
5. **Use proper error types** from domain_types::errors
6. **Implement comprehensive status mapping** for all connector states
7. **Use Secret types** for sensitive data (SecretSerdeValue)
8. **Handle Option types** properly for optional fields
9. **Use proper currency handling** for international payments
10. **Implement complete webhook event mapping** for real-time updates

This type system ensures type safety, comprehensive payment method support, and proper integration with the UCS architecture.