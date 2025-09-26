/**
 * Configuration utilities - TypeScript equivalent of Python config.py
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import { Config } from '../types/workflow-state';

export function loadConfig(configPath?: string): Config {
  const actualPath = configPath || 'config.json';
  
  if (!fs.existsSync(actualPath)) {
    throw new Error(
      `Configuration file not found: ${actualPath}\n` +
      'Please create a config.json file with your API keys.'
    );
  }

  try {
    const configData = JSON.parse(fs.readFileSync(actualPath, 'utf-8'));
    return validateAndParseConfig(configData);
  } catch (error: any) {
    if (error.message.includes('Unexpected token')) {
      throw new Error(`Invalid JSON in configuration file: ${error.message}`);
    }
    throw new Error(`Error loading configuration: ${error.message}`);
  }
}

function validateAndParseConfig(configData: any): Config {
  // Validate required sections
  if (!configData.firecrawl || !configData.firecrawl.api_key) {
    throw new Error('Missing firecrawl.api_key in configuration');
  }
  
  if (!configData.litellm || !configData.litellm.api_key) {
    throw new Error('Missing litellm.api_key in configuration');
  }

  // Build config with defaults
  const config: Config = {
    firecrawl: {
      api_key: configData.firecrawl.api_key
    },
    litellm: {
      api_key: configData.litellm.api_key,
      model: configData.litellm.model || 'gpt-3.5-turbo',
      max_tokens: configData.litellm.max_tokens || 4000,
      base_url: configData.litellm.base_url,
      custom_headers: configData.litellm.custom_headers
    },
    workflow: {
      url_collection: { enabled: true },
      crawling: { enabled: true },
      llm_processing: { enabled: true },
      mock_server_generation: { enabled: false }, // Default to false like Python
      output_management: { enabled: true }
    }
  };

  // Override workflow config if provided
  if (configData.workflow) {
    config.workflow = {
      ...config.workflow,
      ...configData.workflow
    };
  }

  return config;
}

export function createSampleConfig(configPath?: string): void {
  const actualPath = configPath || 'config.json';
  
  const sampleConfig = {
    "firecrawl": {
      "api_key": "your-firecrawl-api-key-here"
    },
    "litellm": {
      "api_key": "your-llm-api-key-here",
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.7,
      "max_tokens": 50000,
      "_comment": "For proxy setups, add base_url and optionally custom_headers",
      "base_url": "https://grid.ai.juspay.net",
      "custom_headers": {
        "X-Custom-Header": "value"
      }
    },
    "prompt": {
      "template": "You are tasked with creating comprehensive API documentation by extracting information from the provided context. Your role is to structure the available information into a standardized documentation format without making any modifications, assumptions, or interpretations.\n\n## Core Requirements:\n- Extract ALL available endpoints from the following documentation\n- Maintain exact 1:1 correspondence between source content and documentation\n- Do not modify, enhance, or assume any missing information\n- Structure only what is explicitly present in the source material\n- Cover all API flows mentioned in the context, not just specific ones\n\n## Documentation Structure:\n\n### Connector Information\n- Extract connector name and basic details as provided\n- List all base URLs (production, sandbox, testing) mentioned\n- Include any additional URLs found (webhooks, status endpoints, documentation links, etc.)\n\n### Authentication Details\n- Document authentication methods exactly as described\n- Include all authentication parameters, headers, and configurations mentioned\n- Preserve exact format of API keys, tokens, or credentials structure\n\n### Complete Endpoint Inventory\nFor EVERY endpoint found in the context, document:\n- Exact endpoint URL/path\n- HTTP method\n- All headers mentioned\n- Complete request payload structure (as provided)\n- Complete response payload structure (as provided)\n- Any curl examples if present\n- Error responses if documented\n\n### Flow Categories to Extract:\nDocument all flows present, which may include:\n- Payment/Authorization flows\n- Capture operations\n- Refund processes\n- Status/sync endpoints\n- Dispute handling\n- Tokenization/vaulting\n- Webhook endpoints\n- Account/configuration endpoints\n- Any other flows mentioned\n\n### Configuration Parameters\n- List all configuration requirements mentioned\n- Environment variables or settings\n- Supported features, currencies, regions as stated\n- Integration requirements\n\n## Output Guidelines:\n- Use the exact field names, values, and structures from the source\n- Preserve original JSON formatting and data types\n- Include all optional and required parameters as marked\n- Maintain original error codes and messages\n- Do not fill gaps or make educated guesses\n- If information is partially available, document only what's explicitly provided\n- Use \"Not specified in source\" for clearly missing but relevant information\n\nGenerate documentation that serves as a faithful representation of the API capabilities based solely on the provided context.\n\nAPI Documentation:\n{content}"
    }
  };
  
  fs.writeFileSync(actualPath, JSON.stringify(sampleConfig, null, 2));
  
  console.log(`Sample configuration created at: ${actualPath}`);
  console.log('Please update the API keys before running the tool.');
}

export function validateConfig(config: Config): void {
  if (!config.litellm.api_key) {
    throw new Error('API key is required in configuration');
  }

  if (!config.litellm.model) {
    throw new Error('Model is required in configuration');
  }

  if (config.litellm.max_tokens <= 0) {
    throw new Error('Max tokens must be greater than 0');
  }
}