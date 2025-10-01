#!/usr/bin/env node

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

class MassSetup {
  constructor() {
    this.configPath = path.join(__dirname, 'searxng-config.yml');
    this.containerName = 'searxng';
    this.dockerPort = 32768;
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  log(message, type = 'info') {
    const colors = {
      info: '\x1b[36m',    // Cyan
      success: '\x1b[32m', // Green
      warning: '\x1b[33m', // Yellow
      error: '\x1b[31m',   // Red
      reset: '\x1b[0m'     // Reset
    };

    const icons = {
      info: 'ℹ️ ',
      success: '✅',
      warning: '⚠️ ',
      error: '❌'
    };

    console.log(`${colors[type]}${icons[type]} ${message}${colors.reset}`);
  }

  async question(prompt) {
    return new Promise((resolve) => {
      this.rl.question(prompt, resolve);
    });
  }

  checkCommand(command) {
    try {
      execSync(`which ${command}`, { stdio: 'ignore' });
      return true;
    } catch (error) {
      return false;
    }
  }

  checkDockerRunning() {
    try {
      execSync('docker info', { stdio: 'ignore' });
      return true;
    } catch (error) {
      return false;
    }
  }

  async checkDockerInstallation() {
    this.log('Checking Docker/OrbStack installation...', 'info');

    // Check for Docker
    const hasDocker = this.checkCommand('docker');
    const hasOrbStack = this.checkCommand('orb');

    if (!hasDocker && !hasOrbStack) {
      this.log('Neither Docker nor OrbStack is installed!', 'error');
      this.log('Please install one of the following:', 'warning');
      console.log('\n📦 Docker Desktop:');
      console.log('   • macOS: https://docs.docker.com/desktop/install/mac-install/');
      console.log('   • Windows: https://docs.docker.com/desktop/install/windows-install/');
      console.log('   • Linux: https://docs.docker.com/desktop/install/linux-install/');

      console.log('\n🚀 OrbStack (macOS only):');
      console.log('   • Download: https://orbstack.dev/');
      console.log('   • Install via Homebrew: brew install orbstack');

      const retry = await this.question('\nWould you like to check again after installation? (y/N): ');
      if (retry.toLowerCase() === 'y' || retry.toLowerCase() === 'yes') {
        return this.checkDockerInstallation();
      } else {
        process.exit(1);
      }
    }

    if (hasOrbStack) {
      this.log('OrbStack detected!', 'success');
    } else if (hasDocker) {
      this.log('Docker detected!', 'success');
    }

    // Check if Docker daemon is running
    if (!this.checkDockerRunning()) {
      this.log('Docker daemon is not running!', 'error');

      if (hasOrbStack) {
        this.log('Please start OrbStack and try again.', 'warning');
      } else {
        this.log('Please start Docker Desktop and try again.', 'warning');
      }

      const retry = await this.question('Would you like to check again? (y/N): ');
      if (retry.toLowerCase() === 'y' || retry.toLowerCase() === 'yes') {
        return this.checkDockerInstallation();
      } else {
        process.exit(1);
      }
    }

    this.log('Docker daemon is running!', 'success');
    return true;
  }

  checkConfigFile() {
    this.log('Checking SearxNG configuration...', 'info');

    if (!fs.existsSync(this.configPath)) {
      this.log(`Configuration file not found: ${this.configPath}`, 'error');
      this.log('Please ensure searxng-config.yml exists in the CLI directory.', 'warning');
      process.exit(1);
    }

    this.log('Configuration file found!', 'success');

    // Display config summary
    const config = fs.readFileSync(this.configPath, 'utf8');
    console.log('\n📋 Configuration Summary:');
    console.log(`   • Port: ${this.dockerPort}`);
    console.log(`   • Safe Search: Disabled`);
    console.log(`   • Default Language: English`);
    console.log(`   • Public Instance: No`);
    console.log(`   • Debug: Disabled`);
  }

  async stopExistingContainer() {
    try {
      // Check if container exists
      execSync(`docker inspect ${this.containerName}`, { stdio: 'ignore' });

      this.log('Existing SearxNG container found. Stopping and removing...', 'warning');

      // Stop and remove existing container
      try {
        execSync(`docker stop ${this.containerName}`, { stdio: 'ignore' });
      } catch (e) {
        // Container might already be stopped
      }

      try {
        execSync(`docker rm ${this.containerName}`, { stdio: 'ignore' });
      } catch (e) {
        // Container might already be removed
      }

      this.log('Previous container cleaned up!', 'success');
    } catch (error) {
      // Container doesn't exist, which is fine
    }
  }

  async pullSearxNGImage() {
    this.log('Pulling latest SearxNG Docker image...', 'info');

    try {
      execSync('docker pull searxng/searxng:latest', {
        stdio: 'inherit',
        timeout: 300000 // 5 minutes timeout
      });
      this.log('SearxNG image pulled successfully!', 'success');
    } catch (error) {
      this.log('Failed to pull SearxNG image!', 'error');
      this.log('Please check your internet connection and try again.', 'warning');
      process.exit(1);
    }
  }

  async startSearxNG() {
    this.log('Starting SearxNG container...', 'info');

    // Use absolute paths and ensure cross-platform compatibility
    const configDir = path.resolve(path.dirname(this.configPath));
    const configFileName = path.basename(this.configPath);

    // Convert Windows paths to Unix-style for Docker
    const dockerConfigDir = process.platform === 'win32'
      ? configDir.replace(/\\/g, '/').replace(/^([A-Z]):/, (match, drive) => `/${drive.toLowerCase()}`)
      : configDir;

    // Find an available port
    const availablePort = await this.findAvailablePort();

    const dockerCommand = [
      'docker', 'run', '-d',
      '--name', this.containerName,
      '-p', `${availablePort}:8080`,
      '-v', `"${dockerConfigDir}":/etc/searxng:ro`,
      '-e', `SEARXNG_SETTINGS_PATH=/etc/searxng/${configFileName}`,
      '--restart', 'unless-stopped',
      'searxng/searxng:latest'
    ];

    try {
      // Join command with proper escaping for cross-platform
      const commandString = dockerCommand.join(' ');
      this.log(`Running: ${commandString}`, 'info');

      const containerId = execSync(commandString, {
        encoding: 'utf8',
        timeout: 30000,
        shell: process.platform === 'win32' ? 'cmd.exe' : '/bin/bash'
      }).trim();

      // Update the port we're actually using
      this.dockerPort = availablePort;

      this.log(`SearxNG container started! Container ID: ${containerId.substring(0, 12)}...`, 'success');
      this.log(`SearxNG will be available at: http://localhost:${this.dockerPort}`, 'info');

      // Wait a moment for the container to fully start
      this.log('Waiting for SearxNG to initialize...', 'info');
      await new Promise(resolve => setTimeout(resolve, 5000));

      return true;
    } catch (error) {
      this.log('Failed to start SearxNG container!', 'error');
      console.log('Error details:', error.message);

      // Try alternative command format for Windows
      if (process.platform === 'win32') {
        this.log('Trying alternative Windows Docker command format...', 'warning');
        return this.startSearxNGWindows(dockerConfigDir, configFileName, availablePort);
      }

      return false;
    }
  }

  async findAvailablePort() {
 

    const checkPort = (port) => {
      return new Promise((resolve) => {
        const server = net.createServer();
        server.listen(port, () => {
          server.once('close', () => resolve(true));
          server.close();
        });
        server.on('error', () => resolve(false));
      });
    };

    // Try ports starting from 32768
    for (let port = 32768; port <= 32800; port++) {
      if (await checkPort(port)) {
        this.log(`Found available port: ${port}`, 'info');
        return port;
      }
    }

    // Fallback to original port
    this.log('No available ports found, using default 32768', 'warning');
    return 32768;
  }

  async startSearxNGWindows(configDir, configFileName, port) {
    try {
      // Windows-specific Docker command
      const dockerArgs = [
        'run', '-d',
        '--name', this.containerName,
        '-p', `${port}:8080`,
        '-v', `${configDir}:/etc/searxng:ro`,
        '-e', `SEARXNG_SETTINGS_PATH=/etc/searxng/${configFileName}`,
        '--restart', 'unless-stopped',
        'searxng/searxng:latest'
      ];

      const containerId = execSync(`docker ${dockerArgs.join(' ')}`, {
        encoding: 'utf8',
        timeout: 30000
      }).trim();

      this.dockerPort = port;
      this.log(`SearxNG container started! Container ID: ${containerId.substring(0, 12)}...`, 'success');
      return true;
    } catch (error) {
      this.log('Windows fallback also failed!', 'error');
      console.log('Error details:', error.message);
      return false;
    }
  }

  async testSearxNG() {
    this.log('Testing SearxNG installation...', 'info');

    const maxRetries = 10;
    let retries = 0;

    // Test basic web interface
    while (retries < maxRetries) {
      try {
        const { default: fetch } = await import('node-fetch');
        const response = await fetch(`http://localhost:${this.dockerPort}/`);

        if (response.ok) {
          this.log('SearxNG web interface is responding!', 'success');
          break;
        }

        throw new Error(`HTTP ${response.status}`);
      } catch (error) {
        retries++;
        if (retries < maxRetries) {
          this.log(`Waiting for SearxNG to be ready... (${retries}/${maxRetries})`, 'info');
          await new Promise(resolve => setTimeout(resolve, 2000));
        } else {
          this.log('SearxNG is not responding after multiple attempts!', 'error');
          this.log('The container might be running but not accessible.', 'warning');
          return false;
        }
      }
    }

    // Test JSON API functionality
    this.log('Testing SearxNG JSON API...', 'info');
    try {
      const { default: fetch } = await import('node-fetch');

      // Test search API with JSON format
      const searchResponse = await fetch(
        `http://localhost:${this.dockerPort}/search?q=test&format=json&engines=duckduckgo`,
        {
          timeout: 10000,
          headers: {
            'User-Agent': 'MASS-CLI-Research/1.0'
          }
        }
      );

      if (searchResponse.ok) {
        const data = await searchResponse.json();
        if (data && typeof data === 'object' && Array.isArray(data.results)) {
          this.log('JSON API is working correctly!', 'success');
          this.log(`Test search returned ${data.results.length} results`, 'info');
        } else {
          this.log('JSON API returned unexpected format', 'warning');
          console.log('Response data:', data);
        }
      } else {
        this.log(`JSON API test failed: HTTP ${searchResponse.status}`, 'warning');
      }

      // Test config API
      const configResponse = await fetch(`http://localhost:${this.dockerPort}/config`, {
        timeout: 5000
      });

      if (configResponse.ok) {
        const configData = await configResponse.json();
        if (configData && configData.engines) {
          this.log('Config API is working correctly!', 'success');
          const enabledEngines = Object.keys(configData.engines).filter(
            engine => configData.engines[engine].enabled
          );
          this.log(`Available search engines: ${enabledEngines.slice(0, 5).join(', ')}${enabledEngines.length > 5 ? '...' : ''}`, 'info');
        }
      } else {
        this.log('Config API test failed', 'warning');
      }

    } catch (error) {
      this.log('API testing failed, but basic web interface works', 'warning');
      console.log('API test error:', error.message);
    }

    return true;
  }

  async createEnvTemplate() {
    const envPath = path.join(__dirname, '.env.example');
    const envContent = `# MASS Research CLI Configuration

# AI Service Configuration
AI_PROVIDER=litellm
LITELLM_API_KEY=your_api_key_here
LITELLM_BASE_URL=http://localhost:4000/v1
LITELLM_MODEL_ID=gpt-4

# Alternative: Vertex AI (Google Cloud)
# AI_PROVIDER=vertex
# VERTEX_AI_PROJECT_ID=your_project_id
# VERTEX_AI_LOCATION=us-central1

# SearxNG Configuration
SEARXNG_BASE_URL=http://localhost:${this.dockerPort}

# Research Configuration
MAX_DEPTH=5
MAX_PAGES_PER_DEPTH=10
MAX_TOTAL_PAGES=50
MAX_CONCURRENT_PAGES=3
LINK_RELEVANCE_THRESHOLD=0.5
TIMEOUT_PER_PAGE=30000
RESPECT_ROBOTS_TXT=true

# Storage Configuration
DATA_DIRECTORY=./data
HISTORY_FILE=./data/research_history.json

# Custom Instructions Configuration
CUSTOM_INSTRUCTIONS_FILE=./custom_instructions.txt

# Debug Configuration
DEBUG_ENABLED=false
DEBUG_LOG_FILE=./logs/debug.log

# Optional: Proxy Configuration
# PROXY_LIST=http://proxy1:8080,http://proxy2:8080
`;

    if (!fs.existsSync(envPath)) {
      fs.writeFileSync(envPath, envContent);
      this.log('Created .env.example file with default configuration!', 'success');
    }
  }

  async showCompletionMessage() {
    console.log('\n🎉 SearxNG Setup Complete!');
    console.log('================================');
    console.log(`✅ SearxNG is running at: http://localhost:${this.dockerPort}`);
    console.log(`✅ Container name: ${this.containerName}`);
    console.log(`✅ Configuration file: ${this.configPath}`);

    console.log('\n📋 Next Steps:');
    console.log('1. Copy .env.example to .env and configure your API keys');
    console.log(`2. Test SearxNG in your browser: http://localhost:${this.dockerPort}`);
    console.log('3. Run your research CLI: npm start research "your query"');

    console.log('\n🔧 Management Commands:');
    console.log(`   • Stop SearxNG: docker stop ${this.containerName}`);
    console.log(`   • Start SearxNG: docker start ${this.containerName}`);
    console.log(`   • View logs: docker logs ${this.containerName}`);
    console.log(`   • Remove container: docker rm -f ${this.containerName}`);

    console.log('\n🌐 SearxNG Web Interface:');
    console.log(`   Open http://localhost:${this.dockerPort} in your browser to test search functionality.`);
  }

  async cleanup() {
    this.rl.close();
  }

  async run() {
    try {
      console.log('🚀 MASS Research CLI - SearxNG Setup');
      console.log('====================================\n');

      // Check Docker installation
      await this.checkDockerInstallation();

      // Check configuration file
      this.checkConfigFile();

      // Ask for confirmation
      const proceed = await this.question('\nProceed with SearxNG setup? (Y/n): ');
      if (proceed.toLowerCase() === 'n' || proceed.toLowerCase() === 'no') {
        this.log('Setup cancelled by user.', 'warning');
        await this.cleanup();
        return;
      }

      // Stop existing container if any
      await this.stopExistingContainer();

      // Pull latest image
      await this.pullSearxNGImage();

      // Start SearxNG
      const started = await this.startSearxNG();
      if (!started) {
        this.log('Setup failed!', 'error');
        await this.cleanup();
        process.exit(1);
      }

      // Test installation
      const working = await this.testSearxNG();
      if (!working) {
        this.log('SearxNG may not be fully functional. Please check manually.', 'warning');
      }

      // Create .env template
      await this.createEnvTemplate();

      // Show completion message
      await this.showCompletionMessage();

    } catch (error) {
      this.log(`Setup failed: ${error.message}`, 'error');
      process.exit(1);
    } finally {
      await this.cleanup();
    }
  }
}

// Handle script execution
if (require.main === module) {
  const setup = new MassSetup();
  setup.run().catch(error => {
    console.error('❌ Setup failed:', error.message);
    process.exit(1);
  });
}

module.exports = MassSetup;