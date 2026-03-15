# UCS Connector Implementation Patterns

This directory contains comprehensive implementation patterns for each payment flow in the UCS (Universal Connector Service) system. Each pattern file provides complete, reusable templates that can be consumed by AI to generate consistent, production-ready connector code.

## Directory Structure

```
guides/patterns/
├── README.md                              # This file
├── flow_macro_guide.md                    # Shared macro patterns
├── macro_patterns_reference.md            # Complete macro reference
├── pattern_authorize.md                   # Authorization flow
├── pattern_capture.md                     # Capture flow
├── pattern_psync.md                       # Payment sync
├── pattern_void.md                        # Void flow
├── pattern_void_pc.md                     # Void (post-capture)
├── pattern_refund.md                      # Refund flow
├── pattern_rsync.md                       # Refund sync
├── pattern_dsync.md                       # Dispute sync
├── pattern_setup_mandate.md               # Mandate setup
├── pattern_repeat_payment_flow.md         # Repeat payments
├── pattern_mandate_revoke.md              # Mandate revocation
├── pattern_IncomingWebhook_flow.md        # Webhook handling
├── pattern_createorder.md                 # Order creation
├── pattern_session_token.md               # Session tokens
├── pattern_payment_method_token.md        # PM tokenization
├── pattern_accept_dispute.md              # Accept dispute
├── pattern_defend_dispute.md              # Defend dispute
├── pattern_submit_evidence.md             # Submit dispute evidence
├── pattern_IncrementalAuthorization_flow.md # Incremental auth
├── pattern_CreateAccessToken_flow.md      # Access token creation
└── authorize/                             # Payment method patterns
    ├── README.md
    ├── card/pattern_authorize_card.md
    ├── wallet/pattern_authorize_wallet.md
    ├── bank_transfer/pattern_authorize_bank_transfer.md
    ├── bank_debit/pattern_authorize_bank_debit.md
    ├── bank_redirect/pattern_authorize_bank_redirect.md
    ├── upi/pattern_authorize_upi.md
    ├── bnpl/pattern_authorize_bnpl.md
    ├── crypto/pattern_authorize_crypto.md
    ├── gift_card/pattern_authorize_gift_card.md
    ├── mobile_payment/pattern_authorize_mobile_payment.md
    └── reward/pattern_authorize_reward.md
```

## Available Patterns

### Core Payment Flows (Always Implement)

These flows form the foundation of every connector integration.

| Flow | Pattern File | Description |
|------|-------------|-------------|
| **Authorize** | [`pattern_authorize.md`](./pattern_authorize.md) | Complete authorization flow patterns |
| **Capture** | [`pattern_capture.md`](./pattern_capture.md) | Payment capture flow patterns |
| **PSync** | [`pattern_psync.md`](./pattern_psync.md) | Payment status synchronization |
| **Void** | [`pattern_void.md`](./pattern_void.md) | Void/cancel authorization |
| **Refund** | [`pattern_refund.md`](./pattern_refund.md) | Full and partial refunds |
| **RSync** | [`pattern_rsync.md`](./pattern_rsync.md) | Refund status synchronization |

### Extended Flows (Conditional -- Implement If Connector Supports)

| Flow | Pattern File | Description |
|------|-------------|-------------|
| **Void (Post-Capture)** | [`pattern_void_pc.md`](./pattern_void_pc.md) | Void after capture |
| **IncomingWebhook** | [`pattern_IncomingWebhook_flow.md`](./pattern_IncomingWebhook_flow.md) | Webhook handling and signature verification |
| **SetupMandate** | [`pattern_setup_mandate.md`](./pattern_setup_mandate.md) | Recurring payment setup |
| **RepeatPayment** | [`pattern_repeat_payment_flow.md`](./pattern_repeat_payment_flow.md) | Process recurring payments |
| **MandateRevoke** | [`pattern_mandate_revoke.md`](./pattern_mandate_revoke.md) | Cancel stored mandates |
| **PaymentMethodToken** | [`pattern_payment_method_token.md`](./pattern_payment_method_token.md) | Payment method tokenization |
| **CreateOrder** | [`pattern_createorder.md`](./pattern_createorder.md) | Multi-step payment initiation |
| **SessionToken** | [`pattern_session_token.md`](./pattern_session_token.md) | Secure session management |
| **IncrementalAuthorization** | [`pattern_IncrementalAuthorization_flow.md`](./pattern_IncrementalAuthorization_flow.md) | Incremental authorization |
| **CreateAccessToken** | [`pattern_CreateAccessToken_flow.md`](./pattern_CreateAccessToken_flow.md) | Access token creation |
| **DSync** | [`pattern_dsync.md`](./pattern_dsync.md) | Dispute status sync |

### Dispute Flows (Conditional -- Implement If Connector Supports)

| Flow | Pattern File | Description |
|------|-------------|-------------|
| **AcceptDispute** | [`pattern_accept_dispute.md`](./pattern_accept_dispute.md) | Accept chargeback |
| **DefendDispute** | [`pattern_defend_dispute.md`](./pattern_defend_dispute.md) | Defend against disputes |
| **SubmitEvidence** | [`pattern_submit_evidence.md`](./pattern_submit_evidence.md) | Submit dispute evidence |

### Payment Method Patterns (Authorize Flow)

These patterns live under [`authorize/`](./authorize/README.md) and provide payment-method-specific authorization guidance.

| Payment Method | Pattern File | Supported Flows |
|----------------|-------------|-----------------|
| **Card** | [`authorize/card/pattern_authorize_card.md`](./authorize/card/pattern_authorize_card.md) | All flows |
| **Wallet** | [`authorize/wallet/pattern_authorize_wallet.md`](./authorize/wallet/pattern_authorize_wallet.md) | Authorize, Refund |
| **Bank Transfer** | [`authorize/bank_transfer/pattern_authorize_bank_transfer.md`](./authorize/bank_transfer/pattern_authorize_bank_transfer.md) | Authorize, Refund |
| **Bank Debit** | [`authorize/bank_debit/pattern_authorize_bank_debit.md`](./authorize/bank_debit/pattern_authorize_bank_debit.md) | Authorize, Refund |
| **Bank Redirect** | [`authorize/bank_redirect/pattern_authorize_bank_redirect.md`](./authorize/bank_redirect/pattern_authorize_bank_redirect.md) | Authorize |
| **UPI** | [`authorize/upi/pattern_authorize_upi.md`](./authorize/upi/pattern_authorize_upi.md) | Authorize, Refund |
| **BNPL** | [`authorize/bnpl/pattern_authorize_bnpl.md`](./authorize/bnpl/pattern_authorize_bnpl.md) | Authorize, Refund |
| **Crypto** | [`authorize/crypto/pattern_authorize_crypto.md`](./authorize/crypto/pattern_authorize_crypto.md) | Authorize |
| **Gift Card** | [`authorize/gift_card/pattern_authorize_gift_card.md`](./authorize/gift_card/pattern_authorize_gift_card.md) | Authorize |
| **Mobile Payment** | [`authorize/mobile_payment/pattern_authorize_mobile_payment.md`](./authorize/mobile_payment/pattern_authorize_mobile_payment.md) | Authorize, Refund |
| **Reward** | [`authorize/reward/pattern_authorize_reward.md`](./authorize/reward/pattern_authorize_reward.md) | Authorize |

### Macro Guides

| File | Description |
|------|-------------|
| [`flow_macro_guide.md`](./flow_macro_guide.md) | Shared macro patterns for flow implementation |
| [`macro_patterns_reference.md`](./macro_patterns_reference.md) | Complete macro documentation and reference |

## Workflow Controllers

Grace supports multiple workflow controllers for different use cases:

| Controller | Purpose | Trigger Pattern |
|------------|---------|-----------------|
| `integrate_connector.md` | New connector integration | "integrate {connector}" |
| `add_flow.md` | Add specific flow(s) to existing connector | "add {flow} flow to {connector}" |
| `add_pm.md` | Add payment method(s) to existing connector | "add {Category}:{payment_method} to {connector}" |

### Payment Method Specification Syntax

The `add_pm.md` workflow **requires** category prefix syntax:

```bash
add {Category}:{type1},{type2} and {Category2}:{type3} to {connector}
```

**Examples:**
```bash
add Wallet:Apple Pay,Google Pay,PayPal to Stripe
add Card:Credit,Debit to Adyen
add BankTransfer:SEPA,ACH to Wise
add Wallet:Apple Pay,Google Pay and Card:Credit,Debit to Stripe
add Wallet:PayPal and BankTransfer:SEPA,ACH to Wise
add UPI:Collect,Intent to PhonePe
```

**Available Categories:** Card, Wallet, BankTransfer, BankDebit, BankRedirect, UPI, BNPL, Crypto, GiftCard, MobilePayment, Reward

## Pattern Usage

### For New Implementations

Use `integrate_connector.md` for complete new connector integration:

```bash
integrate {ConnectorName} using grace/integrate_connector.md
```

This implements all core flows in sequence.

### For Adding Specific Flows

Use `add_flow.md` when adding flows to an existing connector:

```bash
add {flow_name} flow to {ConnectorName}
# Example: "add Refund flow to Stripe"
```

Available flows: Authorize, Capture, Refund, Void, PSync, RSync, SetupMandate, IncomingWebhook, etc.

### For Adding Payment Methods

Use `add_pm.md` when adding payment methods:

```bash
add {payment_method} to {ConnectorName}
# Example: "add Apple Pay to Stripe"
```

Available payment methods: Card, Wallet, BankTransfer, BankDebit, UPI, BNPL, Crypto, etc.

### AI Integration Commands

```bash
# New connector - complete integration
integrate {ConnectorName} using grace/integrate_connector.md

# Add specific flow
add {flow_name} flow to {ConnectorName}

# Add payment method
add {payment_method} to {ConnectorName}

# Examples:
integrate Stripe using grace/integrate_connector.md
add Refund flow to Stripe
add Apple Pay to Stripe
```

## Pattern Structure

Each pattern file follows a consistent structure:

### 1. Quick Start Guide
- Placeholder replacement guide
- Example implementations
- Time-to-completion estimates

### 2. Prerequisites
- Required flows that must be implemented first
- Dependencies and requirements
- What must exist before using this pattern

### 3. Modern Macro-Based Pattern
- Recommended implementation approach
- Complete code templates
- Type-safe implementations
- Integration with existing code

### 4. Request/Response Patterns
- Data structure examples
- Transformation patterns
- Payment method specific handling

### 5. Error Handling
- Error mapping strategies
- Specific error messages
- Common pitfalls

### 6. Testing Patterns
- Unit test templates
- Integration test patterns
- Validation checklists

### 7. Integration Checklist
- Pre-implementation requirements
- Step-by-step implementation guide
- Quality validation steps

## Workflow Selection Guide

Choose the right workflow based on your needs:

| Scenario | Use This | Workflow File |
|----------|----------|---------------|
| New connector from scratch | Complete Integration | `integrate_connector.md` |
| Add missing flow to existing connector | Flow Addition | `add_flow.md` |
| Add payment method to existing connector | Payment Method Addition | `add_pm.md` |
| Resume partial implementation | Depends on state | Use appropriate workflow |

## Contributing to Patterns

When implementing new connectors or flows:

1. **Document new patterns** discovered during implementation
2. **Update existing patterns** with improvements or edge cases
3. **Add real-world examples** to pattern files
4. **Enhance checklists** based on implementation experience

## Pattern Quality Standards

All pattern files maintain:

- **Completeness**: Cover all aspects of flow implementation
- **Clarity**: Clear explanations and examples
- **Reusability**: Templates work for any connector
- **Validation**: Comprehensive testing and quality checks
- **UCS-specific**: Tailored for UCS architecture and patterns
- **Production-ready**: Battle-tested in real implementations

## Related Documentation

### Integration & Implementation
- [`../connector_integration_guide.md`](../connector_integration_guide.md) - Complete UCS integration process
- [`../types/types.md`](../types/types.md) - UCS type system reference
- [`../learnings/learnings.md`](../learnings/learnings.md) - Implementation lessons learned
- [`../../README.md`](../../README.md) - GRACE-UCS overview and usage

### Pattern Reference
- [`flow_macro_guide.md`](./flow_macro_guide.md) - Macro usage reference
- [`macro_patterns_reference.md`](./macro_patterns_reference.md) - Complete macro documentation

### Quality & Standards
- [`../feedback.md`](../feedback.md) - Quality feedback database and review template
- [`../quality/README.md`](../quality/README.md) - Quality system overview
- [`../quality/CONTRIBUTING_FEEDBACK.md`](../quality/CONTRIBUTING_FEEDBACK.md) - Guide for adding quality feedback

**Quality Note**: All implementations using these patterns are reviewed by the Quality Guardian Subagent to ensure UCS compliance and code quality. Review common issues in `feedback.md` before implementing to avoid known anti-patterns.

---

**Pro Tip**: Always choose the right workflow controller for your task. Use `integrate_connector.md` for new connectors, `add_flow.md` for adding flows, and `add_pm.md` for adding payment methods.
