# Global Rapid Agentic Connector Exchange for UCS (GRACE-UCS)

GRACE-UCS is a specialized AI-assisted system for UCS (Universal Connector Service) connector development that supports **complete connector lifecycle management** - from initial implementation to continuation of partially completed work.

## 🎯 Core Purpose

GRACE-UCS enables:
- **Full connector implementation** from scratch
- **Resuming partial implementations** where developers left off
- **All payment method support** (cards, wallets, bank transfers, BNPL, etc.)
- **Complete flow coverage** (authorize, capture, void, refund, sync, webhooks, etc.)
- **UCS-specific patterns** tailored for gRPC-based stateless architecture

## 🏗️ UCS Architecture Overview

The UCS connector-service uses a modern, stateless architecture:

```
backend/
├── connector-integration/     # Connector-specific logic
│   ├── src/connectors/       # Individual connector implementations
│   └── src/types.rs          # Common types and utilities
├── domain-types/             # Domain models and data structures
├── grpc-server/             # gRPC service implementation
└── grpc-api-types/          # Protocol buffer definitions
```

### Key UCS Characteristics:
- **gRPC-first**: All communication via Protocol Buffers
- **Stateless**: No database dependencies in connector logic
- **RouterDataV2**: Enhanced type-safe data flow
- **ConnectorIntegrationV2**: Modern trait-based integration
- **Domain-driven**: Clear separation of concerns

## 🚀 Usage Scenarios

### 1. **New Connector Implementation**
```
integrate [ConnectorName] using grace-ucs/.gracerules
```

### 2. **Resume Partial Implementation**
```
continue implementing [ConnectorName] connector in UCS - I have partially implemented [specific_flows] and need to complete [remaining_flows]
```

### 3. **Add Missing Flows**
```
add [flow_names] flows to existing [ConnectorName] connector in UCS
```

### 4. **Debug/Fix Issues**
```
fix [ConnectorName] connector issues in UCS - having problems with [specific_issue_description]
```

### 5. **Add Payment Methods**
```
add support for [payment_method_types] to [ConnectorName] connector in UCS
```

## 📋 Comprehensive Flow Support

### Core Payment Flows
- **Authorization** - Initial payment authorization
- **Capture** - Capture authorized payments
- **Void/Cancel** - Cancel authorized payments
- **Refund** - Full and partial refunds
- **Sync** - Payment status synchronization
- **Refund Sync** - Refund status synchronization

### Advanced Flows
- **Create Order** - Multi-step payment initiation
- **Session Token** - Secure payment session management
- **Setup Mandate** - Recurring payment setup
- **Webhook Handling** - Real-time payment notifications
- **Dispute Management** - Handle chargebacks and disputes

### Payment Method Coverage
- **Cards** - Credit/Debit (Visa, Mastercard, Amex, etc.)
- **Digital Wallets** - Apple Pay, Google Pay, PayPal, etc.
- **Bank Transfers** - ACH, SEPA, Open Banking
- **Buy Now Pay Later** - Klarna, Afterpay, Affirm
- **Cryptocurrencies** - Bitcoin, Ethereum, stablecoins
- **Regional Methods** - UPI, Alipay, WeChat Pay, etc.
- **Cash/Vouchers** - Boleto, OXXO, convenience store payments

## 🛠️ Implementation States

GRACE-UCS tracks and can resume from any implementation state:

### State 1: **Initial Setup**
- Basic connector structure created
- Auth configuration defined
- Base trait implementations stubbed

### State 2: **Core Flows Implemented**
- Authorization flow working
- Basic error handling in place
- Request/response transformations for primary flow

### State 3: **Extended Flows**
- Capture, void, refund flows implemented
- Sync operations working
- Status mapping complete

### State 4: **Payment Methods**
- Multiple payment method support
- Proper validation and transformation
- Payment method specific handling

### State 5: **Advanced Features**
- Webhook implementation
- 3DS handling
- Mandate/recurring support
- Comprehensive error handling

### State 6: **Production Ready**
- Full test coverage
- All edge cases handled
- Performance optimized
- Documentation complete

## 📖 How to Use GRACE-UCS

### For New Implementation:
1. Place connector API documentation in `grace-ucs/references/{{connector_name}}/`
2. Run: `integrate [ConnectorName] using grace-ucs/.gracerules`
3. AI will create complete implementation plan and code

### For Resuming Work:
1. Describe current state: "I have [existing_functionality] implemented"
2. Specify what you need: "Need to add [missing_functionality]"
3. AI will analyze existing code and continue from there

### For Debugging:
1. Describe the issue: "Getting [error_description] when [specific_scenario]"
2. AI will analyze code, identify issue, and provide fix

## 🔧 UCS-Specific Patterns

GRACE-UCS provides dedicated pattern files for each payment flow:

### Available Flow Patterns
- **📖 `guides/patterns/README.md`** - Pattern directory index and usage guide
- **✅ `guides/patterns/pattern_authorize.md`** - Complete authorization flow patterns and implementations
- **✅ `guides/patterns/pattern_capture.md`** - Comprehensive capture flow patterns and examples
- **🚧 Future patterns**: void, refund, sync, webhook, dispute flows

### Pattern Usage
Each pattern file provides:
- **🎯 Quick Start Guide** with placeholder replacement examples
- **📊 Real-world Analysis** from existing connector implementations
- **🏗️ Modern Macro-Based Templates** for consistent implementations
- **🔧 Legacy Manual Patterns** for special cases
- **🧪 Testing Strategies** and integration checklists
- **✅ Validation Steps** and quality checks

### Using Patterns with AI
```bash
# Use specific patterns for targeted implementation
implement authorization flow for NewPayment using pattern_authorize.md
add capture flow to ExistingConnector using pattern_capture.md
implement complete connector flows using guides/patterns/ directory
```

### Connector Structure
```rust
// Main connector file: backend/connector-integration/src/connectors/connector_name.rs
impl ConnectorIntegrationV2<Flow, Request, Response> for ConnectorName {
    // UCS-specific implementations using patterns from guides/patterns/
}

// Transformers: backend/connector-integration/src/connectors/connector_name/transformers.rs
// Request/response transformations for all payment methods and flows
```

### Data Flow
```
gRPC Request → RouterDataV2 → Connector Transform → HTTP Request → External API
External Response → Connector Transform → RouterDataV2 → gRPC Response
```

## 📁 Directory Structure

```
grace-ucs/
├── .gracerules                          # Main AI instructions
├── README.md                            # This file
├── guides/
│   ├── connector_integration_guide.md   # Step-by-step UCS integration
│   ├── patterns/                        # Flow-specific UCS patterns
│   │   ├── README.md                    # Pattern directory index and usage guide
│   │   ├── pattern_authorize.md         # Authorization flow patterns
│   │   └── pattern_capture.md           # Capture flow patterns
│   ├── learnings/learnings.md           # Lessons from UCS implementations
│   ├── types/types.md                   # UCS type system guide
│   └── integrations/integrations.md     # Previous UCS integrations
├── connector_integration/
│   └── template/
│       ├── tech_spec.md                 # UCS technical specification template
│       └── planner_steps.md             # UCS implementation planning template
└── references/
    └── {{connector_name}}/               # Connector-specific documentation
        ├── api_docs.md
        ├── payment_flows.yaml
        └── webhook_spec.json
```

## 🎯 Key Benefits

1. **Resumable Development**: Pick up exactly where you left off
2. **Complete Coverage**: All payment methods and flows supported
3. **UCS-Optimized**: Patterns specific to UCS architecture
4. **AI-Assisted**: Intelligent code generation and problem solving
5. **Production-Ready**: Follows UCS best practices and patterns
6. **Extensible**: Easy to add new flows and payment methods

## 🚀 Getting Started

1. **For new connector**: Place API docs in `references/` and run integration command
2. **For existing connector**: Describe current state and desired additions
3. **For debugging**: Explain the issue and AI will help diagnose and fix

GRACE-UCS makes UCS connector development efficient, comprehensive, and resumable at any stage.# grace-ucs
