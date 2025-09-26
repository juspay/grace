/**
 * Mock Server Generation Node - TypeScript implementation
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import { OpenAI } from 'openai';
import { WorkflowState, MockServerData } from '../types/workflow-state';
import { console } from '../utils/console';
import { Progress } from '../utils/progress';

export class MockServerGenerationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MockServerGenerationError';
  }
}

export async function mockServerNode(state: WorkflowState): Promise<WorkflowState> {
  if (!state.tech_spec) {
    const errorMsg = 'No technical specification available for mock server generation';
    state.errors.push(errorMsg);
    console.error(errorMsg);
    return state;
  }

  console.print('\n[bold]Step 4: Generating mock server...[/bold]');

  const progress = new Progress();
  const newState = { ...state };

  try {
    // Create mock server directory
    const mockServerDir = path.join(state.output_dir, 'mock-server');
    await fs.ensureDir(mockServerDir);

    // Generate server code with AI
    const aiTaskId = progress.addTask('Generating server code with AI');
    const aiResponse = await generateServerCode(state.tech_spec, state.config);
    progress.completeTask(aiTaskId, 'AI generation complete!');

    // Parse the AI response
    const parseTaskId = progress.addTask('Parsing AI response');
    const parsedData = parseAiResponse(aiResponse);
    progress.completeTask(parseTaskId, 'Response parsed!');

    // Create project files
    const filesTaskId = progress.addTask('Creating project files');
    await createProjectFiles(mockServerDir, parsedData);
    progress.completeTask(filesTaskId, 'Project files created!');

    // Install dependencies
    const depsTaskId = progress.addTask('Installing npm dependencies');
    await installDependencies(mockServerDir);
    progress.completeTask(depsTaskId, 'Dependencies installed!');

    // Start server (optional)
    const serverTaskId = progress.addTask('Starting mock server');
    const serverProcess = await startMockServer(mockServerDir);
    progress.completeTask(serverTaskId, 'Mock server started!');

    // Update state with results
    newState.metadata.mock_server_generated = true;
    newState.mock_server_dir = mockServerDir;
    newState.mock_server_process = serverProcess;
    newState.mock_server_data = parsedData;

    console.success('Mock server generated successfully!');
    console.print(`[dim]Server directory: ${mockServerDir}[/dim]`);

    if (serverProcess) {
      console.print(`[dim]Server PID: ${serverProcess.pid}[/dim]`);
      console.print(`[dim]API documentation: ${path.join(mockServerDir, 'api_docs.md')}[/dim]`);
    }

    // Try to open in VS Code
    try {
      const { spawn } = require('child_process');
      spawn('code', [mockServerDir], { 
        detached: true,
        stdio: 'ignore',
        timeout: 5000
      });
      console.print('[green]💻[/green] Opened project in VS Code');
    } catch (error) {
      console.print('[yellow]💻[/yellow] VS Code not available');
    }

  } catch (error: any) {
    const errorMsg = `Mock server generation failed: ${error.message}`;
    newState.errors.push(errorMsg);
    newState.metadata.mock_server_generated = false;
    console.error(errorMsg);
  }

  return newState;
}

async function generateServerCode(techSpec: string, config: any): Promise<string> {
  const prompt = `Create an express server which mocks all the api calls mentioned here. If encryption is required use crypto or some popular libraries to handle it. Print all endpoints created after server starts running.

IMPORTANT: Make the server run on port 5000 (not 3000) to avoid conflicts. Use const PORT = process.env.PORT || 5000;

Format your response exactly like the JSON given below and don't respond with any subscript like "of course" or "here you go":

{
  "server_js": "// Your server.js code here - MUST use port 5000",
  "package_json": "// Your package.json content here", 
  "info": "// Simple Markdown text providing all generated curls with port 5000"
}

${techSpec}`;

  try {
    const openai = new OpenAI({
      apiKey: config.litellm.api_key,
      baseURL: config.litellm.base_url
    });

    const response = await openai.chat.completions.create({
      model: config.litellm.model,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
      max_tokens: config.litellm.max_tokens
    });

    const content = response.choices[0]?.message?.content;
    if (!content) {
      throw new MockServerGenerationError('No response from AI');
    }

    return content;

  } catch (error: any) {
    throw new MockServerGenerationError(`AI code generation failed: ${error.message}`);
  }
}

function parseAiResponse(aiResponse: string): MockServerData {
  // Remove markdown code block markers
  let cleanJson = aiResponse.replace(/```json\n?/g, '');
  cleanJson = cleanJson.replace(/\n?```$/g, '').trim();

  try {
    const parsedData = JSON.parse(cleanJson);

    // Validate required fields
    const requiredFields = ['server_js', 'package_json', 'info'];
    for (const field of requiredFields) {
      if (!(field in parsedData)) {
        throw new MockServerGenerationError(`Missing required field: ${field}`);
      }
    }

    return parsedData as MockServerData;

  } catch (error: any) {
    if (error instanceof MockServerGenerationError) {
      throw error;
    }
    throw new MockServerGenerationError(`Failed to parse AI response as JSON: ${error.message}`);
  }
}

async function createProjectFiles(projectDir: string, parsedData: MockServerData): Promise<void> {
  const files = {
    'server.js': parsedData.server_js,
    'package.json': parsedData.package_json,
    'api_docs.md': parsedData.info
  };

  for (const [filename, content] of Object.entries(files)) {
    const filePath = path.join(projectDir, filename);
    await fs.writeFile(filePath, content, 'utf-8');
    console.success(`Created ${filename}`);
  }
}

async function installDependencies(projectDir: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const npmProcess = spawn('npm', ['install'], {
      cwd: projectDir,
      stdio: 'pipe'
    });

    let stderr = '';

    npmProcess.stderr?.on('data', (data) => {
      stderr += data.toString();
    });

    npmProcess.on('close', (code) => {
      if (code === 0) {
        console.success('Dependencies installed successfully');
        resolve();
      } else {
        console.warn(`npm install warnings: ${stderr}`);
        resolve(); // Don't fail on warnings
      }
    });

    npmProcess.on('error', (error) => {
      if (error.message.includes('ENOENT')) {
        reject(new MockServerGenerationError('npm not found - please install Node.js'));
      } else {
        reject(new MockServerGenerationError(`npm install failed: ${error.message}`));
      }
    });

    // Timeout after 5 minutes
    setTimeout(() => {
      npmProcess.kill();
      reject(new MockServerGenerationError('npm install timed out after 5 minutes'));
    }, 300000);
  });
}

async function startMockServer(projectDir: string): Promise<ChildProcess> {
  return new Promise((resolve, reject) => {
    try {
      const serverProcess = spawn('node', ['server.js'], {
        cwd: projectDir,
        stdio: 'pipe',
        detached: false
      });

      // Give the server a moment to start
      setTimeout(() => {
        if (serverProcess.pid && !serverProcess.killed) {
          console.success(`Mock server started with PID: ${serverProcess.pid}`);
          resolve(serverProcess);
        } else {
          reject(new MockServerGenerationError('Server failed to start'));
        }
      }, 2000);

      serverProcess.on('error', (error) => {
        if (error.message.includes('ENOENT')) {
          reject(new MockServerGenerationError('Node.js not found - please install Node.js'));
        } else {
          reject(new MockServerGenerationError(`Failed to start server: ${error.message}`));
        }
      });

    } catch (error: any) {
      reject(new MockServerGenerationError(`Failed to start server: ${error.message}`));
    }
  });
}