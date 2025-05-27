# Global Rapid Agentic Connector Exchange (GRACE)

GRACE is a system designed to streamline the integration of new payment connectors into the Hyperswitch ecosystem. It provides a structured, step-by-step process to ensure that connectors are added accurately and efficiently.

## Overview

The core of GRACE is a comprehensive guide that details the entire connector integration process. This guide, located at `grace/guides/connector_integration_guide.md`, provides a reusable framework for developers to follow.

## Key Concepts

### Flows

GRACE defines a series of "flows" that represent the different stages of a payment transaction. These flows include:

-   `preprocessing_flow`
-   `tokenization_flow`
-   `authorize_flow`
-   `cancel_flow`
-   `capture_flow`
-   `psync_flow`
-   `access_token_flow`
-   `refund`
-   `rsync`

Each flow corresponds to a specific action or set of actions that a connector must be able to handle.

## Integration Process

The integration process is broken down into several key steps:

1.  **Preparation**: This initial step involves creating a technical specification and a detailed integration plan for the new connector. Templates for these documents can be found in `grace/connector_integration/template/`.
    -   `tech_spec.md`: Outlines the technical details of the connector.
    -   `planner_steps.md`: Provides a step-by-step plan for the integration.

2.  **Implementation**: Following the plan created in the preparation phase, the developer implements the necessary code to integrate the connector into Hyperswitch. This involves implementing the various flows and data transformations required for the connector to function correctly.

3.  **Testing**: Once the implementation is complete, the new connector must be thoroughly tested to ensure that it functions as expected.

## Usage

To integrate a new connector using GRACE, you will need to use an AI model that has the capability to read, write, and execute commands. Follow these steps:

1.  **Clone the Hyperswitch repository**:
    ```bash
    git clone https://github.com/juspay/hyperswitch.git
    ```
2.  **Navigate to the Hyperswitch directory**:
    ```bash
    cd hyperswitch
    ```
3.  **Clone the GRACE repository**:
    ```bash
    git clone https://github.com/juspay/grace.git
    ```
4. **Adding Docs or Reference Docs for a Connector**
   
    To add reference documentation for a connector:
    - Place the files under the following path: `grace/references/{{connector_name}}/`
        - Supported file formats:
            - .md (Markdown)
            - .yaml
            - .json
    - For each flow (e.g., payment, refund, webhook handling, etc.), name the files as:
      doc1.md, doc2.yaml, doc3.json, etc., depending on the content and format.

> 📌 This structure helps keep documentation organized and accessible per connector and flow.

5.  **Prompt the AI model**:
    Prompt the AI model with the following command:
    ```
    integrate [ConnectorName] using .gracerules
    ```
    Replace `[ConnectorName]` with the name of the connector you want to integrate.

6.  **Review and Confirm**:
    The AI model will create a technical specification and an implementation plan. You will be asked to review these documents. You can either approve the plan or suggest modifications. Once the plan is approved, the AI model will proceed with the integration.

7. **Generate code**:
    The Ai will generate the code for the connector, just follow and update the files if needed.

# Model Selection
To ensure high-quality integration planning and documentation generation, select a powerful and reliable AI model. Recommended models include:
- Claude Opus (by Anthropic) — Excellent for long-context understanding and reasoning.
- Claude Sonnet — Balanced in performance and speed for most tasks.
- Gemini 2.5 Pro (by Google) — Strong code and planning capabilities, especially with structured prompts.
> Choose a model with strong reasoning, planning, and multi-step instruction-following capabilities for best results during the integration phase.



