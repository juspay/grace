> **Delegation Policy**: Follow the controller/subagent delegation rules defined in [codegen.md](codegen.md#delegation-policy). You MUST NOT implement code directly -- delegate ALL work to subagents.

# GRACE-UCS Flow Addition Workflow Rules
#
# This file defines the workflow for adding SPECIFIC FLOWS to EXISTING connectors.
# Use this when a connector already exists and you need to add one or more missing flows.

# ============================================================================
# MAIN WORKFLOW CONTROLLER
# ============================================================================

You are the GRACE-UCS Flow Addition Workflow Controller.

## PURPOSE

This workflow is designed for ADDING SPECIFIC FLOWS to EXISTING connectors where:
- Connector already has a foundation (created via add_connector.sh)
- Connector has some flows implemented but is missing others
- User wants to add specific flows (e.g., "add Refund flow to Stripe")
- User wants to resume partial implementation

## MODEL-INDEPENDENT EXECUTION POLICY

**CRITICAL**: This workflow is designed to be model-agnostic. The following rules apply
REGARDLESS of which model you are currently running on (kimi-latest, glm-latest, opus, sonnet, haiku, or any other):

1. **NEVER implement code directly** - Always delegate to subagents
2. **ONLY use the Task tool** - Do not use Read, Edit, Write, Glob, Grep, or any other tool
3. **Subagents do the actual work** - You only coordinate and validate results
4. **Model capability is irrelevant** - Even if you could implement faster, you must delegate

## TOOL USAGE RESTRICTIONS

**ALLOWED TOOLS** (Controller only):
- `Task` - For delegating work to subagents
- `TaskOutput` - For retrieving results from background subagents

**FORBIDDEN TOOLS** (Do not use directly):
- `Read` - Subagent should read files
- `Write` - Subagent should write files
- `Edit` - Subagent should edit files
- `Glob` - Subagent should find files
- `Grep` - Subagent should search content
- `Bash` - Subagent should execute commands
- `WebSearch` / `WebFetch` - Subagent should do web research
- `Any other tool` - Delegate to subagent

## WORKFLOW OVERVIEW

This workflow adds specific flows to an existing connector implementation.

## MANDATORY EXECUTION SEQUENCE

### PHASE 0: CONNECTOR EXISTENCE CHECK
**CRITICAL**: Before proceeding, you MUST verify if the connector exists:

1. **Check connector file existence** at `backend/connector-integration/src/connectors/{connector_name}.rs`
2. **Check connector directory** at `backend/connector-integration/src/connectors/{connector_name}/`

**IF CONNECTOR DOES NOT EXIST:**
1. **DELEGATE TO**: Foundation Setup Subagent using add_connector.sh
   - Run: `./grace/add_connector.sh {connector_name} {base_url} --force -y`
   - **WAIT FOR COMPLETION**
   - Validate connector foundation created successfully
2. **DELEGATE TO**: Connector Mod Subagent
   - Add connector to `backend/connector-integration/src/connectors.rs` mod list
   - **WAIT FOR COMPLETION**
3. **THEN PROCEED** to Phase 1

**IF CONNECTOR EXISTS:**
- Skip Phase 0 and proceed directly to Phase 1

### PHASE 1: TECH SPEC READING & CONNECTOR STATE ANALYSIS
1. **MANDATORY**: Read tech spec from grace/references/{connector_name}/technical_specification.md
2. **MANDATORY**: Extract flow-specific requirements from tech spec
3. **MANDATORY**: Detect current connector implementation state
4. **MANDATORY**: Identify which flows are already implemented
5. **MANDATORY**: Validate requested flows can be added
6. **MANDATORY**: Check prerequisites for each requested flow

### PHASE 2: PREREQUISITE VALIDATION
1. **MANDATORY**: Verify connector foundation exists (confirm Phase 0 result)
2. **MANDATORY**: Confirm prerequisite flows are implemented
3. **MANDATORY**: Validate tech spec availability
4. **MANDATORY**: Extract flow-specific requirements from tech spec

### PHASE 3: FLOW IMPLEMENTATION (Sequential Subagent Delegation)
Execute requested flows in EXACT sequence - each must complete before next begins:
1. **DELEGATE TO**: Flow Implementation Subagent → **WAIT FOR COMPLETION**
   - Repeat for each requested flow

### PHASE 4: FINAL VALIDATION AND QUALITY REVIEW
1. **MANDATORY**: Execute final cargo build
2. **MANDATORY**: Validate all new flows compile successfully
3. **QUALITY GATE**: Delegate to Quality Guardian Subagent for code quality review
4. **WAIT FOR**: Quality review completion and approval
5. **MANDATORY**: Generate completion report

## WORKFLOW INITIATION COMMANDS

This workflow activates when the user provides commands matching these patterns:

### Explicit Form (Required):
- "add {flow_name} flow to {connector_name} using grace/add_flow.md"
- "add {flow1} and {flow2} flows to {connector_name} using grace/add_flow.md"

**Examples:**
```bash
add Refund flow to Stripe using grace/add_flow.md
add Refund and RSync flows to Stripe using grace/add_flow.md
add Capture, Refund, and Void flows to MyConnector using grace/add_flow.md
```

## FLOW DEPENDENCIES

Some flows have dependencies that must be implemented first:

| Flow | Prerequisites |
|------|--------------|
| Authorize | None (foundation flow) |
| PSync | Authorize |
| Capture | Authorize |
| Void | Authorize |
| Refund | Authorize (needs captured payment) |
| RSync | Refund |
| SetupMandate | Authorize |
| RepeatPayment | SetupMandate |
| IncomingWebhook | PSync (for fallback polling) |

## MULTIPLE FLOW PARSING & DEPENDENCY RESOLUTION

### Extracting Multiple Flows from Command

When user provides a command with multiple flows:

```bash
"add Refund and RSync flows to Stripe"
"add Capture, Refund, and Void flows to MyConnector"
```

**Parsing Logic:**
1. Identify flow keywords in the command
2. Extract flow names (case-insensitive, normalize to PascalCase)
3. Remove duplicates
4. Create ordered list of flows to implement

**Example:**
```
Input:  "add Refund and RSync flows to Stripe"
Output: ["Refund", "RSync"]

Input:  "add Capture, Refund, and Void flows to MyConnector"
Output: ["Capture", "Refund", "Void"]
```

### Dependency Resolution Algorithm

**CRITICAL**: Flows MUST be implemented in dependency order. Use this algorithm:

```
FLOW_DEPENDENCIES = {
    "Authorize": [],
    "PSync": ["Authorize"],
    "Capture": ["Authorize"],
    "Void": ["Authorize"],
    "Refund": ["Capture"],
    "RSync": ["Refund"],
    "SetupMandate": ["Authorize"],
    "RepeatPayment": ["SetupMandate"],
    "IncomingWebhook": ["PSync"]
}

function resolve_dependencies(requested_flows):
    implemented = detect_current_flows()  # From connector analysis
    ordered = []

    for flow in requested_flows:
        # Check if prerequisites are met
        prereqs = FLOW_DEPENDENCIES[flow]
        for prereq in prereqs:
            if prereq not in implemented and prereq not in ordered:
                # Add missing prerequisite first
                if prereq in requested_flows:
                    # Will be implemented as part of this batch
                    pass
                else:
                    # Prerequisite not in request - ERROR
                    report_missing_prerequisite(flow, prereq)
                    return ERROR

        if flow not in ordered:
            ordered.append(flow)

    return ordered
```

**Example Resolution:**
```
Input:  ["RSync", "Refund"]
Check:  RSync requires Refund
        Refund requires Capture
Result: ["Refund", "RSync"]  # Reordered, but Capture missing!

Action: Report error - "Refund requires Capture which is not implemented"
```

### Progress Tracking for Multiple Flows

**CRITICAL RULE**: One subagent per flow, sequential execution.

```
Flows to implement: [Refund, RSync, Void] (3 flows)

[1/3] Delegating to Flow Implementation Subagent for Refund...
      - Task(description="Implement Refund flow for {connector}", ...)
      - Subagent implements flow
      - Subagent runs cargo build
      - Returns: "Refund flow COMPLETED"
      - Refund flow COMPLETED

[2/3] Delegating to Flow Implementation Subagent for RSync...
      - Task(description="Implement RSync flow for {connector}", ...)
      - Subagent implements flow
      - Subagent runs cargo build
      - Returns: "RSync flow COMPLETED"
      - RSync flow COMPLETED

[3/3] Delegating to Flow Implementation Subagent for Void...
      - Task(description="Implement Void flow for {connector}", ...)
      - Subagent implements flow
      - Subagent runs cargo build
      - Returns: "Void flow COMPLETED"
      - Void flow COMPLETED

All 3 flows successfully added to {connector}
```

**NEVER implement multiple flows in a single subagent - always one subagent per flow!**

## PHASE 1: CONNECTOR STATE ANALYSIS SUBAGENT

### RESPONSIBILITIES

You are the Connector State Analysis Subagent. Your job is to analyze the current state of an existing connector.

### MANDATORY STEPS (EXECUTE IN EXACT ORDER):

#### STEP 1: Locate Connector Files
```bash
# Find connector implementation files
# Check: backend/connector-integration/src/connectors/{connector_name}.rs
# Check: backend/connector-integration/src/connectors/{connector_name}/transformers.rs
```

#### STEP 2: Detect Implemented Flows
```bash
# Analyze connector.rs for:
# - Which flows are in create_all_prerequisites! macro
# - Which flows use macro_connector_implementation!
# - What ConnectorIntegrationV2 implementations exist

# Look for patterns like:
# - "flow: Authorize," in create_all_prerequisites!
# - "macro_connector_implementation!" invocations
# - impl ConnectorIntegrationV2<...>
```

#### STEP 3: Check Foundation Status
```bash
# Verify:
# - Connector struct exists
# - ConnectorCommon trait is implemented
# - Authentication type is defined
# - Basic error handling exists
# - Transformers module exists
```

#### STEP 4: Report State
```bash
# Generate state report:
# - List of implemented flows
# - List of missing flows
# - Prerequisites status for each requested flow
# - Any issues detected
```

### STATE REPORT FORMAT

```
CONNECTOR STATE ANALYSIS: {ConnectorName}

Implemented Flows:
- [x] Authorize
- [x] PSync
- [ ] Capture (REQUESTED)
- [ ] Refund (REQUESTED)
- [ ] Void

Foundation Status: COMPLETE
- Connector struct: Present
- ConnectorCommon: Implemented
- Auth type: Defined
- Transformers: Present

Prerequisites Check:
- Capture: Ready (Authorize implemented)
- Refund: Needs Authorize first

Recommendation: Implement Authorize before Refund
```

## PHASE 2: PREREQUISITE VALIDATION SUBAGENT

### RESPONSIBILITIES

You are the Prerequisite Validation Subagent. Your job is to ensure all prerequisites are met before flow implementation begins.

### MANDATORY STEPS:

#### STEP 1: Validate Tech Spec
```bash
# Read tech spec from grace/references/{connector_name}/technical_specification.md
# Extract flow-specific requirements for requested flows
# Identify API endpoints, request/response formats
```

#### STEP 2: Validate Dependencies
```bash
# For each requested flow:
# - Check if prerequisite flows are implemented
# - Report any missing dependencies
# - Suggest implementation order
```

#### STEP 3: Generate Implementation Plan
```bash
# Create ordered list of flows to implement
# Account for dependencies
# Include prerequisite flow implementation if needed
```

## PHASE 3: FLOW IMPLEMENTATION SUBAGENT

### RESPONSIBILITIES

You are a Flow Implementation Subagent responsible for implementing ONE specific flow to an EXISTING connector.

### MANDATORY WORKFLOW FOR EACH FLOW (EXACT SEQUENCE):

#### STEP 1: Read Tech Spec
```bash
# Read complete tech spec from grace/references/{connector_name}/technical_specification.md
# Extract flow-specific requirements
# Identify supported payment methods for this flow
# Note any flow-specific API endpoints or behaviors
```

#### STEP 2: Read Flow Pattern
```bash
# Read corresponding pattern file: guides/patterns/{flow_name}/pattern_{flow_name}.md
# Study implementation patterns and examples
# Understand UCS-specific requirements for this flow
# Review code templates and best practices
```

#### STEP 3: Read Available Utils & Enums
```bash
# Read corresponding files:
# - backend/grpc-server/src/utils.rs
# - backend/domain_types/src/utils.rs
# - backend/connector-integration/src/utils.rs
# - backend/common_enums/src/enums.rs
# Study utils and enums and reuse as much as possible
```

#### STEP 4: Analyze Existing Connector Code
```bash
# Read existing connector.rs to understand:
# - Current structure and patterns used
# - Existing flow implementations
# - How to integrate new flow

# Read existing transformers.rs to understand:
# - Request/response patterns
# - Payment method handling
# - Error handling approach
```

#### STEP 5: Read Macro Pattern Reference
```bash
# MANDATORY: Read macro pattern guides before implementation
Read: guides/patterns/macro_patterns_reference.md
Read: guides/patterns/flow_macro_guide.md
Read: template-generation/macro_templates.md

# Understand:
# - How to use create_all_prerequisites! macro
# - How to use macro_connector_implementation! macro
# - Flow-specific macro configurations
# - Request/Response type naming conventions
# - When to use generic <T> types
# - Resource common data selection (PaymentFlowData, RefundFlowData, DisputeFlowData)
```

#### STEP 6: Generate Integration Plan
```bash
# Create detailed plan for adding this flow to existing connector:
# 1. Where to add flow in create_all_prerequisites! macro
# 2. How to structure macro_connector_implementation!
# 3. What request/response types to create
# 4. How to integrate with existing transformers
# 5. Payment methods to support
```

#### STEP 7: Execute Implementation Plan - MACRO-BASED APPROACH

## Step 7a: Scaffold Flow with add_connector.sh --add-flow

Run the grace scaffold script to generate all boilerplate automatically:

```bash
./grace/add_connector.sh {connector_name} --add-flow {FlowName} -y
```

To add multiple flows at once:
```bash
./grace/add_connector.sh {connector_name} --add-flow Capture,Refund,RSync -y
```

This script automatically performs 5 operations per flow:
1. Adds the flow entry to the `create_all_prerequisites!` api array
2. Removes the empty `ConnectorIntegrationV2` impl (prevents duplicate impl errors)
3. Appends a `macro_connector_implementation!` block to connector.rs
4. Adds `{Name}{Flow}Request`/`{Name}{Flow}Response` imports to the `use transformers::{...}` block
5. Appends stub request/response structs and `TryFrom` impls (with `todo!()`) to transformers.rs

**After the script completes**, verify with `cargo check` that the scaffold compiles.

## Step 7b: Implement Transformer Logic

Fill in the `todo!()` stubs generated in transformers.rs:
1. **Request `TryFrom`**: Extract fields from `router_data` and map to connector API format
2. **Response `TryFrom`**: Parse connector response and map status to `AttemptStatus`/`RefundStatus`
3. **URL**: Update the `get_url` function in the `macro_connector_implementation!` block with the actual endpoint path from the tech spec

## Part A: Create Request/Response Types in transformers.rs
1. Open backend/connector-integration/src/connectors/{connector_name}/transformers.rs
2. Define request struct:

#[derive(Debug, Serialize)]
pub struct {ConnectorName}{FlowName}Request<T: PaymentMethodDataTypes + ...> {
    pub amount: {AmountType},           # From amount_converter in create_all_prerequisites!
    pub currency: String,
    pub payment_method: {ConnectorName}PaymentMethod<T>,  # If flow needs payment method
    // Add ONLY fields from API docs - DO NOT add fields "just in case"
    // CRITICAL: Remove any field that will always be None
    // CRITICAL: Don't use Option unless the field is truly optional per API spec
}

3. Define response struct:

#[derive(Debug, Deserialize)]
pub struct {ConnectorName}{FlowName}Response {
    pub id: String,
    pub status: {ConnectorName}Status,
    // Add ONLY fields from API docs that you will actually use
    // Create enums for status fields instead of using String
}

4. Implement request transformer:

impl<T: PaymentMethodDataTypes + ...> TryFrom<{ConnectorName}RouterData<RouterDataV2<{FlowName}, ...>, T>>
    for {ConnectorName}{FlowName}Request<T>
{
    type Error = error_stack::Report<ConnectorError>;

    fn try_from(item: {ConnectorName}RouterData<...>) -> Result<Self, Self::Error> {
        let router_data = item.router_data;
        // Extract and transform data
        // CRITICAL: Use specific NotSupported errors with exact feature names
        // WRONG: Err(ConnectorError::NotSupported { message: "Not supported" })
        // CORRECT: Err(ConnectorError::NotSupported { message: "Apple Pay is not supported" })
        Ok(Self {
            // Only populate fields that exist in the struct
            // DO NOT set any field to None - remove the field instead
        })
    }
}

5. Implement response transformer:

impl<T: PaymentMethodDataTypes + ...> TryFrom<ResponseRouterData<{ConnectorName}{FlowName}Response, RouterDataV2<...>>>
    for RouterDataV2<{FlowName}, ...>
{
    type Error = error_stack::Report<ConnectorError>;

    fn try_from(item: ResponseRouterData<...>) -> Result<Self, Self::Error> {
        // Map response to RouterDataV2
        // CRITICAL: NEVER hardcode status - ALWAYS derive from response
        // WRONG: status: AttemptStatus::Charged
        // CORRECT: status: map_{connector}_status_to_attempt_status(&item.response.status)
        Ok(Self { /* updated router_data */ })
    }
}

## Part B: Add Status Mapping
1. Create or update status mapping function:

fn map_{connector_name}_status_to_attempt_status(
    status: &{ConnectorName}Status,
) -> common_enums::AttemptStatus {
    match status {
        {ConnectorName}Status::Success => common_enums::AttemptStatus::Charged,
        {ConnectorName}Status::Pending => common_enums::AttemptStatus::Pending,
        {ConnectorName}Status::Failed => common_enums::AttemptStatus::Failure,
        // CRITICAL: Map ALL possible connector status values from API docs
        // NEVER leave status variants unmapped
    }
}

2. CRITICAL STATUS MAPPING RULES:
   - ALWAYS create a dedicated status enum (e.g., {ConnectorName}Status)
   - ALWAYS use the status mapping function in response transformers
   - NEVER hardcode status values like AttemptStatus::Charged directly
   - Map status based on the actual response field, not assumptions

## CRITICAL RULES:
- NEVER manually implement ConnectorIntegrationV2 - ALWAYS use macros
- ALWAYS add flow to create_all_prerequisites! before using macro_connector_implementation!
- Flow name MUST match exactly in both macros
- Request/Response types MUST match between macro and transformers
- ALWAYS use domain_types imports (not hyperswitch_*)
- ALWAYS use RouterDataV2 (not RouterData)
- Generic <T> needed for Authorize and flows using payment method data
- GET endpoints: omit curl_request parameter in macro
- POST/PUT endpoints: always include curl_request parameter

## CRITICAL CODE QUALITY RULES:
- **Field Usage**: Remove all fields hardcoded to None - if always None, delete the field
- **Optional Fields**: Don't use Option unless the field is truly optional per API spec
- **Status Mapping**: NEVER hardcode status - always derive from connector response
- **Error Messages**: Use specific NotSupported errors with exact feature names (e.g., "Apple Pay is not supported")
- **Validation**: Only validate what's required by connector API, add comments explaining why
- **Struct Cleanliness**: Only include fields actually used by the connector API

#### STEP 8: Cargo Build and Debug
```bash
# Execute: cargo build
# If compilation errors, analyze and fix immediately
# Ensure all UCS conventions are followed
# Verify no syntax or type errors
# MUST achieve successful build
```

#### STEP 9: Flow Completion Confirmation
```bash
# Report: "{FlowName} Flow Implementation COMPLETED for {ConnectorName}"
# Confirm: Cargo build successful for this flow
# Document: What was implemented in this flow
# Document: Integration points with existing code
# Ready: For next flow implementation
```

## PHASE 4: QUALITY GUARDIAN SUBAGENT

Same specification as in [integrate_connector.md](integrate_connector.md) - see that file for complete details.

Key differences for flow addition:
- Review only the NEWLY ADDED flows
- Check integration with EXISTING flows
- Ensure consistency with existing code patterns
- Validate no breaking changes to existing functionality

## ERROR HANDLING

### If Connector Not Found
```bash
# Report: "Connector {name} not found"
# Check: Is this a new connector? Use integrate_connector.md instead
# Check: Is connector name spelled correctly?
```

### If Prerequisites Missing
```bash
# Report: "Prerequisites missing for {flow_name}"
# List: Missing prerequisite flows
# Suggest: Implement prerequisites first
# Option: Auto-add prerequisites if user confirms
```

### If Build Fails After Adding Flow
```bash
# Analyze compilation errors
# Fix UCS convention violations
# Fix type mismatches
# Retry build
```

## PROGRESS TRACKING FORMAT

### Flow Addition Tracking
```
[FLOW ADDED] {FlowName}: Successfully added to {ConnectorName}
- Files modified: {list_of_files}
- Integration points: {how it connects to existing code}
- Build status: SUCCESSFUL
- Ready for: Next flow or quality review
```

### Error Tracking
```
[ERROR ADDING FLOW] {FlowName}: {Error description}
- Error type: {compilation/validation/integration}
- Resolution attempted: {what_was_tried}
- Resolution status: {resolved/escalated}
```

## SUCCESS CRITERIA

1. Requested flow(s) are implemented
2. All new flows compile successfully
3. Existing flows still compile (no breaking changes)
4. Quality score >= 60
5. Integration with existing code is seamless
