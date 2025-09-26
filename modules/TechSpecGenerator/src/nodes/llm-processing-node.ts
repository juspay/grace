/**
 * LLM Processing Node - TypeScript implementation
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import { OpenAI } from 'openai';
import { WorkflowState } from '../types/workflow-state';
import { console } from '../utils/console';
import { Progress } from '../utils/progress';

export async function llmProcessingNode(state: WorkflowState): Promise<WorkflowState> {
  console.print('\n[bold]Step 3: LLM Processing...[/bold]');
  
  if (state.markdown_files.length === 0) {
    console.warn('No markdown files to process');
    return state;
  }
  
  const progress = new Progress();
  const newState = { ...state };
  
  try {
    // Read all markdown files
    const taskId = progress.addTask('Reading markdown files');
    const markdownContent = await readMarkdownFiles(state.markdown_files);
    progress.completeTask(taskId, `Read ${state.markdown_files.length} markdown files`);
    
    // Generate technical specification
    const specTaskId = progress.addTask('Generating technical specification with AI');
    const techSpec = await generateTechSpec(markdownContent, state.config);
    progress.completeTask(specTaskId, 'Technical specification generated');
    
    // Save tech spec
    const saveTaskId = progress.addTask('Saving technical specification');
    const specsDir = path.join(state.output_dir, 'specs');
    await fs.ensureDir(specsDir);
    
    const specFilepath = path.join(specsDir, 'technical_specification.md');
    await fs.writeFile(specFilepath, techSpec, 'utf-8');
    progress.completeTask(saveTaskId, `Specification saved to ${specFilepath}`);
    
    // Update state
    newState.tech_spec = techSpec;
    newState.spec_filepath = specFilepath;
    newState.metadata.spec_generated = true;
    
    // Estimate tokens (simplified calculation)
    newState.metadata.estimated_tokens = {
      input: Math.ceil(markdownContent.length / 4), // Rough estimate
      output: Math.ceil(techSpec.length / 4)
    };
    
    console.success('LLM processing completed successfully');
    
  } catch (error) {
    const errorMsg = `LLM processing failed: ${error}`;
    console.error(errorMsg);
    newState.errors.push(errorMsg);
    newState.metadata.spec_generated = false;
  }
  
  return newState;
}

async function readMarkdownFiles(filePaths: string[]): Promise<string> {
  const contents: string[] = [];
  
  for (const filePath of filePaths) {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      contents.push(`\n\n## Content from ${path.basename(filePath)}\n\n${content}`);
    } catch (error) {
      console.warn(`Failed to read ${filePath}: ${error}`);
    }
  }
  
  return contents.join('\n');
}

async function generateTechSpec(content: string, config: any): Promise<string> {
  const prompt = `
Analyze the following API documentation content and create a comprehensive technical specification.

Focus on:
1. API endpoints and their methods
2. Request/response schemas
3. Authentication mechanisms
4. Error handling
5. Rate limiting
6. Data models

Content:
${content}

Generate a detailed technical specification in markdown format that can be used to create a mock server.
  `.trim();

  try {
    // Initialize OpenAI (assuming OpenAI-compatible API)
    const openai = new OpenAI({
      apiKey: config.litellm.api_key,
      baseURL: config.litellm.base_url
    });

    const response = await openai.chat.completions.create({
      model: config.litellm.model,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: config.litellm.max_tokens,
      temperature: 0.7
    });

    const techSpec = response.choices[0]?.message?.content;
    
    if (!techSpec) {
      throw new Error('No response from LLM');
    }
    
    return techSpec;
    
  } catch (error: any) {
    throw new Error(`LLM API request failed: ${error.message}`);
  }
}