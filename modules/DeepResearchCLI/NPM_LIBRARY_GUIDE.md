# @mass-research/cli - NPM Library Guide

## Overview

`@mass-research/cli` is a professional AI-powered deep web research library and CLI tool. It can be used both programmatically in your Node.js applications and as a command-line interface for interactive research.

## Installation

```bash
# Install the library
npm install @mass-research/cli

# Or with yarn
yarn add @mass-research/cli

# For global CLI access
npm install -g @mass-research/cli
```

## Quick Start

### Programmatic Usage

```typescript
import { createMassResearcher } from '@mass-research/cli';

const researcher = createMassResearcher({
  ai: {
    provider: 'litellm',
    apiKey: 'your-api-key',
    baseUrl: 'http://localhost:4000/v1',
    modelId: 'gpt-4'
  }
});

// Perform research
const result = await researcher.research('What are the latest trends in AI research?');
console.log(result.finalAnswer);
console.log(`Confidence: ${result.confidence}`);
```

### CLI Usage

```bash
# Start interactive research session
mass-research

# Show configuration
mass-research config

# View history
mass-research history
```

## API Reference

### Main Classes

#### MassResearcher

The primary class for programmatic research operations.

```typescript
import { MassResearcher, MassConfig } from '@mass-research/cli';

const config: MassConfig = {
  ai: {
    provider: 'litellm',
    apiKey: 'your-api-key',
    modelId: 'gpt-4'
  },
  research: {
    maxDepth: 5,
    maxPagesPerDepth: 10
  }
};

const researcher = new MassResearcher(config);
```

#### Methods

##### `research(query: string, options?: ResearchOptions): Promise<ResearchResult>`

Perform a research session.

```typescript
const result = await researcher.research('Your research question', {
  customInstructions: 'Focus on academic sources',
  onProgress: (progress) => console.log(`${progress.percentage}% - ${progress.message}`),
  onLogEntry: (entry) => console.log(entry.message),
  outputFormat: 'html'
});
```

**Parameters:**
- `query`: The research question
- `options`: Optional configuration
  - `customInstructions`: Custom AI instructions
  - `onProgress`: Progress callback
  - `onLogEntry`: Log entry callback
  - `saveResults`: Whether to save results (default: true)
  - `outputFormat`: Output format ('json' | 'html' | 'markdown')

**Returns:** `ResearchResult` object with:
- `finalAnswer`: The synthesized research answer
- `confidence`: Confidence score (0-1)
- `session`: Complete session data
- `logs`: All log entries
- `metadata`: Processing statistics

##### `getCurrentSession(): ResearchSession | null`

Get the current research session.

##### `cancel(): Promise<void>`

Cancel the current research session.

##### `getHistory(limit?: number): Promise<ResearchSession[]>`

Get research history.

##### `getStatistics(): Promise<Statistics>`

Get research statistics.

##### `testConnection(): Promise<{success: boolean, error?: string}>`

Test AI service connection.

### Factory Functions

#### `createMassResearcher(config?: Partial<MassConfig>): MassResearcher`

Create a researcher with smart configuration detection.

```typescript
import { createMassResearcher } from '@mass-research/cli';

// Uses environment variables + provided config
const researcher = createMassResearcher({
  research: { maxDepth: 3 }
});
```

#### `createMassResearcherFromEnv(envPath?: string): MassResearcher`

Create a researcher from environment variables.

```typescript
import { createMassResearcherFromEnv } from '@mass-research/cli';

const researcher = createMassResearcherFromEnv('.env.production');
```

#### `createDefaultConfig(): MassConfig`

Get default configuration.

```typescript
import { createDefaultConfig } from '@mass-research/cli';

const defaultConfig = createDefaultConfig();
console.log(defaultConfig);
```

### Configuration

#### MassConfig Interface

```typescript
interface MassConfig {
  ai?: {
    provider?: 'litellm' | 'vertex';
    apiKey?: string;
    baseUrl?: string;
    modelId?: string;
    projectId?: string;
    location?: string;
    customInstructions?: string;
  };
  research?: {
    maxDepth?: number;
    maxPagesPerDepth?: number;
    maxTotalPages?: number;
    maxConcurrentPages?: number;
    linkRelevanceThreshold?: number;
    timeoutPerPage?: number;
    respectRobotsTxt?: boolean;
    dataDirectory?: string;
    historyFile?: string;
  };
}
```

### Events

The `MassResearcher` class extends `EventEmitter` and emits the following events:

```typescript
researcher.on('progress', (progress) => {
  console.log(`${progress.percentage}% - ${progress.stage}: ${progress.message}`);
});

researcher.on('logEntry', (entry) => {
  console.log(`[${entry.type}] ${entry.message}`);
});

researcher.on('researchComplete', (result) => {
  console.log('Research completed!', result.finalAnswer);
});

researcher.on('error', (error) => {
  console.error('Research error:', error);
});

researcher.on('researchCancelled', (session) => {
  console.log('Research cancelled:', session.id);
});
```

## Examples

### Basic Research

```typescript
import { createMassResearcher } from '@mass-research/cli';

async function basicResearch() {
  const researcher = createMassResearcher({
    ai: {
      apiKey: process.env.OPENAI_API_KEY,
      modelId: 'gpt-4'
    }
  });

  const result = await researcher.research('What are the benefits of TypeScript?');

  console.log('Answer:', result.finalAnswer);
  console.log('Confidence:', result.confidence);
  console.log('Pages processed:', result.metadata.totalPages);
}
```

### Advanced Research with Custom Instructions

```typescript
import { MassResearcher } from '@mass-research/cli';

async function advancedResearch() {
  const researcher = new MassResearcher({
    ai: {
      provider: 'litellm',
      apiKey: 'your-api-key',
      baseUrl: 'http://localhost:4000/v1',
      modelId: 'gpt-4'
    },
    research: {
      maxDepth: 3,
      maxPagesPerDepth: 15
    }
  });

  const customInstructions = `
    You are a technical research specialist. When analyzing content:
    - Focus on peer-reviewed sources and official documentation
    - Include specific version numbers and dates when relevant
    - Provide code examples when discussing implementation
    - Compare different approaches objectively
  `;

  const result = await researcher.research(
    'How to implement serverless functions with TypeScript?',
    {
      customInstructions,
      outputFormat: 'markdown',
      onProgress: (progress) => {
        console.log(`Progress: ${progress.percentage}%`);
      }
    }
  );

  console.log(result.finalAnswer);
}
```

### Batch Research

```typescript
async function batchResearch() {
  const researcher = createMassResearcher();

  const queries = [
    'Latest React 18 features',
    'Node.js performance best practices',
    'TypeScript 5.0 new features'
  ];

  const results = await Promise.all(
    queries.map(query => researcher.research(query))
  );

  results.forEach((result, index) => {
    console.log(`\n=== ${queries[index]} ===`);
    console.log(result.finalAnswer);
    console.log(`Confidence: ${result.confidence}`);
  });
}
```

### Research with Progress Tracking

```typescript
import { createMassResearcher } from '@mass-research/cli';

async function researchWithProgress() {
  const researcher = createMassResearcher();

  const result = await researcher.research(
    'What are the security considerations for modern web applications?',
    {
      onProgress: (progress) => {
        console.log(`[${progress.stage}] ${progress.percentage}% - ${progress.message}`);
      },
      onLogEntry: (entry) => {
        if (entry.type === 'analysis') {
          console.log(`✓ Analyzed: ${entry.url}`);
        }
      }
    }
  );

  return result;
}
```

### Environment-based Configuration

```typescript
// .env file
// AI_PROVIDER=litellm
// LITELLM_API_KEY=your-api-key
// LITELLM_MODEL_ID=gpt-4
// MAX_DEPTH=5
// CUSTOM_INSTRUCTIONS_FILE=./research-instructions.txt

import { createMassResearcherFromEnv } from '@mass-research/cli';

async function envBasedResearch() {
  const researcher = createMassResearcherFromEnv();

  // Configuration loaded from environment
  const config = researcher.getConfiguration();
  console.log('Loaded config:', config);

  const result = await researcher.research('Your research question');
  return result;
}
```

### Error Handling

```typescript
async function researchWithErrorHandling() {
  const researcher = createMassResearcher({
    ai: { apiKey: 'invalid-key' }
  });

  try {
    // Test connection first
    const connectionTest = await researcher.testConnection();
    if (!connectionTest.success) {
      throw new Error(`AI connection failed: ${connectionTest.error}`);
    }

    const result = await researcher.research('Your question');
    return result;
  } catch (error) {
    console.error('Research failed:', error.message);
    throw error;
  } finally {
    researcher.destroy(); // Clean up resources
  }
}
```

## TypeScript Support

The library is fully written in TypeScript and includes comprehensive type definitions:

```typescript
import {
  MassResearcher,
  MassConfig,
  ResearchResult,
  ResearchOptions,
  ResearchSession,
  LogEntry
} from '@mass-research/cli';

// Full type safety
const config: MassConfig = {
  ai: {
    provider: 'litellm',
    modelId: 'gpt-4'
  }
};

const researcher: MassResearcher = new MassResearcher(config);
const result: ResearchResult = await researcher.research('question');
```

## Best Practices

### 1. Configuration Management

```typescript
// Use environment variables for sensitive data
const researcher = createMassResearcher({
  ai: {
    apiKey: process.env.AI_API_KEY,
    provider: process.env.AI_PROVIDER as 'litellm' | 'vertex'
  }
});
```

### 2. Resource Cleanup

```typescript
const researcher = createMassResearcher(config);

try {
  const result = await researcher.research(query);
  return result;
} finally {
  researcher.destroy(); // Always clean up
}
```

### 3. Progress Monitoring

```typescript
const researcher = createMassResearcher(config);

researcher.on('progress', (progress) => {
  // Update UI or log progress
  updateProgressBar(progress.percentage);
});

const result = await researcher.research(query);
```

### 4. Error Recovery

```typescript
const researcher = createMassResearcher(config);

researcher.on('error', async (error) => {
  console.error('Research error:', error);

  // Attempt to save partial results
  const currentSession = researcher.getCurrentSession();
  if (currentSession) {
    await savePartialResults(currentSession);
  }
});
```

## Performance Considerations

- **Concurrent Requests**: Use `maxConcurrentPages` to control load
- **Timeouts**: Set appropriate `timeoutPerPage` for your use case
- **Memory Usage**: Monitor with large research sessions
- **Rate Limiting**: Respect AI provider rate limits

## Troubleshooting

### Common Issues

1. **AI Connection Failures**
   ```typescript
   const test = await researcher.testConnection();
   if (!test.success) {
     console.error('AI connection failed:', test.error);
   }
   ```

2. **Configuration Validation**
   ```typescript
   import { validateConfig } from '@mass-research/cli';

   const validation = validateConfig(config);
   if (!validation.valid) {
     console.error('Config errors:', validation.errors);
   }
   ```

3. **Memory Issues**
   - Reduce `maxTotalPages` and `maxPagesPerDepth`
   - Process results in batches
   - Call `destroy()` to clean up resources

## License

MIT License - see LICENSE file for details.

## Support

- 🐛 Bug reports: [GitHub Issues](https://github.com/mass-research/cli/issues)
- 📚 Documentation: [GitHub Wiki](https://github.com/mass-research/cli/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/mass-research/cli/discussions)