# Grace Workflow Selection Guide

> **Note**: All file paths in this document are relative to the Grace project root directory.

This guide helps you choose the right Grace workflow controller for your UCS connector task.

## Quick Decision Tree

```
What do you need to do?
│
├── New connector from scratch?
│   └── Use integrate_connector.md
│       Command: integrate {Connector} using grace/integrate_connector.md
│
├── Add to existing connector?
│   │
│   ├── Add a flow (Authorize, Capture, Refund, etc.)?
│   │   └── Use add_flow.md
│       Command: add {flow} flow to {Connector} using grace/add_flow.md
│   │
│   └── Add a payment method (Apple Pay, Cards, etc.)?
│       └── Use add_pm.md
│           Command: add {payment_method} to {Connector} using grace/add_pm.md
│
└── Fix or improve existing connector?
    └── Use add_flow.md (for flow fixes) or manual editing
```

> **Note**: Always use explicit form with full path to the workflow file to avoid ambiguity.

## Workflow Controllers

### 0. `codegen.md` - Main Orchestrator

**When to Use:**
- Starting a brand new connector integration from scratch
- Need the full end-to-end pipeline (scrape docs -> tech spec -> scaffold -> implement)

**What It Does:**
- Orchestrates the complete pipeline
- Delegates to `integrate_connector.md` for the implementation phase

**Trigger Commands:**
```bash
Read grace/codegen.md. Integrate {ConnectorName}.
Read grace/codegen.md. Integrate {ConnectorName} using: {url1}, {url2}
```

---

### 1. `integrate_connector.md` - New Connector Integration

**When to Use:**

- Building a new connector from scratch
- Connector doesn't exist yet in the codebase
- Need complete implementation (all core flows)

**What It Does:**

1. Creates connector foundation (using `add_connector.sh`)
2. Implements all 6 core flows in sequence:
   - Authorize → PSync → Capture → Refund → RSync → Void
3. Runs quality review

**Trigger Commands:**

```bash
# Explicit form (recommended)
integrate {ConnectorName} using grace/integrate_connector.md
integrate Stripe using grace/integrate_connector.md
```

**Prerequisites:**

- Tech spec placed in `grace/references/{connector_name}/technical_specification.md`

**Output:**

- Complete connector with all core flows
- Ready for testing

---

### 2. `add_flow.md` - Add Specific Flows

**When to Use:**

- Connector already exists
- Need to add one or more missing flows
- Resume partial implementation
- Fix/improve existing flow

**What It Does:**

1. Analyzes existing connector state
2. Validates prerequisites for requested flow
3. Implements only the requested flow(s)
4. Ensures integration with existing code

**Trigger Commands:**

```bash
# Explicit form (recommended)
add {flow_name} flow to {connector_name} using grace/add_flow.md
add Refund flow to Stripe using grace/add_flow.md
add Capture and Void flows to Adyen using grace/add_flow.md
```

**Supported Flows:**

| Flow               | Prerequisites | Description                        |
| ------------------ | ------------- | ---------------------------------- |
| Authorize          | None          | Payment authorization (foundation) |
| PSync              | Authorize     | Payment status sync                |
| Capture            | Authorize     | Capture authorized payments        |
| Void               | Authorize     | Cancel authorized payments         |
| Refund             | Capture       | Refund captured payments           |
| RSync              | Refund        | Refund status sync                 |
| SetupMandate       | Authorize     | Set up recurring payments          |
| RepeatPayment      | SetupMandate  | Process recurring payments         |
| IncomingWebhook    | PSync         | Webhook handling                   |
| CreateOrder        | -             | Multi-step payment initiation      |
| SessionToken       | -             | Secure session management          |
| PaymentMethodToken | -             | Tokenize payment methods           |
| DefendDispute      | -             | Defend chargebacks                 |
| AcceptDispute      | -             | Accept chargebacks                 |
| DSync              | -             | Dispute status sync                |

**Pattern Files:**

- `guides/patterns/pattern_{flow_name}.md`

---

### 3. `add_pm.md` - Add Payment Methods

**When to Use:**

- Connector exists with Authorize flow
- Need to add support for new payment method(s)
- Expand payment method coverage

**What It Does:**

1. Analyzes existing connector state
2. Checks which flows need the payment method
3. Implements payment method handling in transformers
4. Adds PM-specific request/response handling

**Trigger Commands:**

```bash
# Explicit form (required) - Category prefix syntax
add {Category}:{payment_method1},{payment_method2} to {connector_name} using grace/add_pm.md
add Wallet:Apple Pay,Google Pay and Card:Credit,Debit to Stripe using grace/add_pm.md
add Wallet:PayPal and BankTransfer:SEPA,ACH to Wise using grace/add_pm.md
add UPI:Collect,Intent to PhonePe using grace/add_pm.md
```

**Supported Payment Methods:**

| Category      | Types                                     | Pattern File                                                   |
| ------------- | ----------------------------------------- | -------------------------------------------------------------- |
| Card          | Credit, Debit                             | `authorize/card/pattern_authorize_card.md`                     |
| Wallet        | Apple Pay, Google Pay, PayPal, WeChat Pay | `authorize/wallet/pattern_authorize_wallet.md`                 |
| BankTransfer  | SEPA, ACH, Wire                           | `authorize/bank_transfer/pattern_authorize_bank_transfer.md`   |
| BankDebit     | SEPA Direct Debit, ACH Debit              | `authorize/bank_debit/pattern_authorize_bank_debit.md`         |
| BankRedirect  | iDEAL, Sofort, Giropay                    | `authorize/bank_redirect/pattern_authorize_bank_redirect.md`   |
| UPI           | Collect, Intent                           | `authorize/upi/pattern_authorize_upi.md`                       |
| BNPL          | Klarna, Afterpay, Affirm                  | `authorize/bnpl/pattern_authorize_bnpl.md`                     |
| Crypto        | Bitcoin, Ethereum                         | `authorize/crypto/pattern_authorize_crypto.md`                 |
| GiftCard      | Gift Card                                 | `authorize/gift_card/pattern_authorize_gift_card.md`           |
| MobilePayment | Carrier Billing                           | `authorize/mobile_payment/pattern_authorize_mobile_payment.md` |
| Reward        | Loyalty Points                            | `authorize/reward/pattern_authorize_reward.md`                 |

**Payment Method Specification Syntax:**

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
add Wallet:Apple Pay,Google Pay and Card:Credit,Debit and BankTransfer:ACH to Stripe
```

_Category Names:_ Card, Wallet, BankTransfer, BankDebit, BankRedirect, UPI, BNPL, Crypto, GiftCard, MobilePayment, Reward

**Prerequisites:**

- Authorize flow must be implemented (required foundation)

---

## Common Scenarios

### Scenario 1: New Connector Integration

**Situation:** You need to integrate a new payment gateway (e.g., "NewPay") that doesn't exist in UCS.

**Solution:** Use `integrate_connector.md`

**Steps:**

1. Create tech spec at `grace/references/newpay/technical_specification.md`
2. Run: `integrate NewPay using grace/integrate_connector.md`
3. AI will create complete connector with all 6 core flows

---

### Scenario 2: Add Missing Flow to Existing Connector

**Situation:** Stripe connector has Authorize, Capture, but is missing Refund.

**Solution:** Use `add_flow.md`

**Command:**

```bash
add Refund flow to Stripe
```

**What Happens:**

1. AI detects Stripe exists with Authorize and Capture
2. Validates Refund prerequisites (needs Capture - ✅ exists)
3. Implements Refund flow only
4. Integrates with existing code

---

### Scenario 3: Add Payment Method to Existing Connector

**Situation:** Adyen connector supports Cards but needs Apple Pay.

**Solution:** Use `add_pm.md`

**Command:**

```bash
add Apple Pay to Adyen
```

**What Happens:**

1. AI detects Adyen exists with Authorize flow
2. Adds Apple Pay handling in Authorize transformers
3. Adds to Refund if applicable

---

### Scenario 4: Resume Partial Implementation

**Situation:** You started integrating a connector but only completed Authorize and Capture.

**Solution:** Depends on what's missing

**Option A - Add specific flows:**

```bash
add Refund and Void flows to MyConnector
```

**Option B - Continue with complete integration:**

```bash
integrate MyConnector using grace/integrate_connector.md
```

(Will detect existing flows and continue from there)

---

### Scenario 5: Fix Error Handling in Existing Flow

**Situation:** Stripe's Refund flow has incorrect error mapping.

**Solution:** Use `add_flow.md` with fix intent

**Command:**

```bash
fix error handling in Stripe Refund flow
```

Or manually edit using patterns from `guides/patterns/` (e.g., `pattern_refund.md`)

---

## Workflow Comparison

| Aspect               | `integrate_connector.md` | `add_flow.md`          | `add_pm.md`                       |
| -------------------- | --------------------- | ---------------------- | --------------------------------- |
| **Purpose**          | New connector         | Add flows              | Add payment methods               |
| **Starting Point**   | Empty/foundation only | Existing connector     | Existing connector with Authorize |
| **What It Adds**     | All core flows        | Specific flow(s)       | Payment method handling           |
| **Files Modified**   | Creates new files     | Modifies existing      | Modifies transformers             |
| **Prerequisites**    | Tech spec             | Connector exists       | Authorize flow exists             |
| **Typical Duration** | Full integration      | Single flow            | Single payment method             |

## Pattern File Locations

### Flow Patterns

```
guides/patterns/pattern_{flow_name}.md
```

Examples:

- `guides/patterns/pattern_authorize.md`
- `guides/patterns/pattern_capture.md`
- `guides/patterns/pattern_refund.md`

### Payment Method Patterns

```
guides/patterns/authorize/{payment_method}/pattern_authorize_{payment_method}.md
```

Examples:

- `guides/patterns/authorize/card/pattern_authorize_card.md`
- `guides/patterns/authorize/wallet/pattern_authorize_wallet.md`
- `guides/patterns/authorize/bank_transfer/pattern_authorize_bank_transfer.md`

## Tips for Best Results

1. **Always start with the right workflow** - Using wrong workflow wastes time
2. **Check prerequisites** - Flows have dependencies (e.g., Refund needs Capture)
3. **Payment methods need Authorize** - Can't add PM without Authorize flow
4. **Be specific** - "Add Refund flow to Stripe" is better than "fix Stripe"
5. **One task at a time** - Complete one workflow before starting another

## Troubleshooting

### "Connector not found"

- Check connector name spelling
- Verify connector exists in `backend/connector-integration/src/connectors/`
- If new connector, use `integrate_connector.md` instead

### "Prerequisites not met"

- Check flow dependencies table
- Implement prerequisite flows first
- Example: Can't add Refund without Capture

### "Payment method already supported"

- Check existing transformers.rs
- May need to add to additional flows
- Or PM is already implemented

## Related Documentation

- [Patterns README](./patterns/README.md) - Pattern overview
- [Connector Integration Guide](./connector_integration_guide.md) - Step-by-step integration
- [Quality Guide](./quality/README.md) - Code quality standards
