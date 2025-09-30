#!/usr/bin/env node

/**
 * Example usage of @mass-research/cli library
 * This demonstrates how users would consume the library programmatically
 */

const { createMassResearcher, createDefaultConfig } = require('./dist/lib/lib/index.js');

async function example() {
  console.log('🔍 MASS Research Library Example\n');

  try {
    // Example 1: Create with default configuration
    console.log('📋 Creating researcher with default configuration...');
    const config = createDefaultConfig();
    console.log('Default config:', JSON.stringify(config, null, 2));

    // Example 2: Create researcher (would need actual API key for real usage)
    console.log('\n🤖 Creating researcher instance...');
    const researcher = createMassResearcher({
      ai: {
        provider: 'litellm',
        // apiKey: 'your-api-key-here', // Uncomment for real usage
        modelId: 'gpt-4'
      },
      research: {
        maxDepth: 3,
        maxPagesPerDepth: 5
      }
    });

    console.log('✅ Researcher created successfully!');

    // Example 3: Get configuration
    console.log('\n⚙️ Current configuration:');
    const currentConfig = researcher.getConfiguration();
    console.log('AI Provider:', currentConfig.ai.provider);
    console.log('Model:', currentConfig.ai.modelId);
    console.log('Max Depth:', currentConfig.research.maxDepth);

    // Example 4: Test connection (would fail without real API key)
    console.log('\n🔌 Testing AI connection...');
    try {
      const connectionTest = await researcher.testConnection();
      if (connectionTest.success) {
        console.log('✅ AI connection successful!');
      } else {
        console.log('❌ AI connection failed:', connectionTest.error);
      }
    } catch (error) {
      console.log('❌ Connection test failed (expected without API key)');
    }

    // Example 5: Get statistics
    console.log('\n📊 Getting research statistics...');
    try {
      const stats = await researcher.getStatistics();
      console.log('Statistics:', stats);
    } catch (error) {
      console.log('No statistics available yet');
    }

    // Example 6: Event listeners
    console.log('\n📡 Setting up event listeners...');
    researcher.on('progress', (progress) => {
      console.log(`Progress: ${progress.percentage}% - ${progress.message}`);
    });

    researcher.on('logEntry', (entry) => {
      console.log(`[${entry.type}] ${entry.message}`);
    });

    researcher.on('error', (error) => {
      console.error('Research error:', error.message);
    });

    console.log('✅ Event listeners configured!');

    // Example 7: Cleanup
    console.log('\n🧹 Cleaning up resources...');
    researcher.destroy();
    console.log('✅ Cleanup complete!');

    console.log('\n🎉 Example completed successfully!');
    console.log('\n💡 To use with real research:');
    console.log('   1. Set up your AI API key in .env file or config');
    console.log('   2. Call researcher.research("Your question") to start research');
    console.log('   3. Check the NPM_LIBRARY_GUIDE.md for complete documentation');

  } catch (error) {
    console.error('❌ Example failed:', error.message);
    process.exit(1);
  }
}

// Run the example
if (require.main === module) {
  example().catch(console.error);
}

module.exports = { example };