import axios from 'axios';
import { AIConfig } from '../types';

export interface AIMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface AIResponse {
  content: string;
  tokensUsed: number;
}

export class AIConfigurationError extends Error {
  public configHelp: string;

  constructor(message: string, configHelp: string) {
    super(message);
    this.name = 'AIConfigurationError';
    this.configHelp = configHelp;
  }
}

export class AIService {
  private config: AIConfig;

  constructor(config: AIConfig) {
    this.config = config;
  }

  /**
   * Analyze screenshot using vision-capable AI models
   * For interactive browser navigation decisions
   */
  async analyzeScreenshot(prompt: string, base64Image: string): Promise<string> {
    try {
      // Check if vision AI is enabled
      if (process.env.AI_BROWSER_SCREENSHOTS !== 'true') {
        throw new Error('Screenshot analysis is disabled');
      }

      // For now, use a text-based fallback analysis
      // In production, this would call a vision model like GPT-4V, Gemini Pro Vision, or Claude 3
      const fallbackResponse = {
        hasInteractiveElements: true,
        isSPA: false,
        hasAccordions: false,
        hasDropdowns: false,
        hasInfiniteScroll: false,
        hasLoadMoreButtons: false,
        hiddenContentDetected: false,
        suggestedActions: [
          {
            type: "extract",
            reason: "Perform standard content extraction as fallback"
          }
        ],
        reasoning: "Vision analysis not available - using fallback mode",
        confidence: 0.5
      };

      return JSON.stringify(fallbackResponse);

    } catch (error) {
      // Return safe fallback
      const fallbackResponse = {
        hasInteractiveElements: false,
        isSPA: false,
        hasAccordions: false,
        hasDropdowns: false,
        hasInfiniteScroll: false,
        hasLoadMoreButtons: false,
        hiddenContentDetected: false,
        suggestedActions: [],
        reasoning: "Screenshot analysis failed - using safe fallback",
        confidence: 0.3
      };

      return JSON.stringify(fallbackResponse);
    }
  }

  /**
   * Clean AI response content to extract valid JSON
   * Removes markdown code blocks and other formatting
   */
  private cleanJsonResponse(content: string): string {
    // Remove markdown code blocks (various formats)
    let cleaned = content
      .replace(/```json\s*\n?/gi, '')
      .replace(/```javascript\s*\n?/gi, '')
      .replace(/```\s*\n?/gi, '')
      .replace(/```\s*$/g, '');

    // Remove any leading/trailing whitespace
    cleaned = cleaned.trim();

    // Remove any text before the JSON starts
    const jsonStartMatch = cleaned.match(/[\{\[]/);
    if (jsonStartMatch) {
      cleaned = cleaned.substring(jsonStartMatch.index!);
    }

    // Find the last closing brace/bracket to handle text after JSON
    let braceCount = 0;
    let bracketCount = 0;
    let lastValidIndex = -1;

    for (let i = 0; i < cleaned.length; i++) {
      const char = cleaned[i];
      if (char === '{') braceCount++;
      else if (char === '}') braceCount--;
      else if (char === '[') bracketCount++;
      else if (char === ']') bracketCount--;

      if (braceCount === 0 && bracketCount === 0 && (char === '}' || char === ']')) {
        lastValidIndex = i;
        break;
      }
    }

    if (lastValidIndex > -1) {
      cleaned = cleaned.substring(0, lastValidIndex + 1);
    }

    return cleaned;
  }

  private enhanceMessagesWithCustomInstructions(messages: AIMessage[]): AIMessage[] {
    if (!this.config.customInstructions) {
      return messages;
    }

    const enhancedMessages = [...messages];

    // Find the first system message or create one
    const systemMessageIndex = enhancedMessages.findIndex(msg => msg.role === 'system');

    if (systemMessageIndex >= 0) {
      // Prepend custom instructions to existing system message
      enhancedMessages[systemMessageIndex] = {
        ...enhancedMessages[systemMessageIndex],
        content: `${this.config.customInstructions}\n\n${enhancedMessages[systemMessageIndex].content}`
      };
    } else {
      // Create a new system message with custom instructions at the beginning
      enhancedMessages.unshift({
        role: 'system',
        content: this.config.customInstructions
      });
    }

    return enhancedMessages;
  }

  getCustomInstructionsInfo(): { hasCustomInstructions: boolean; instructionsLength?: number; filePath?: string } {
    return {
      hasCustomInstructions: !!this.config.customInstructions,
      instructionsLength: this.config.customInstructions?.length,
      filePath: this.config.customInstructionsFile
    };
  }

  async generateText(messages: AIMessage[], options?: {
    temperature?: number;
    maxTokens?: number;
  }): Promise<AIResponse> {
    try {
      // Enhance messages with custom instructions
      const enhancedMessages = this.enhanceMessagesWithCustomInstructions(messages);

      if (this.config.provider === 'litellm') {
        return await this.callLiteLLM(enhancedMessages, options);
      } else if (this.config.provider === 'vertex') {
        return await this.callVertexAI(enhancedMessages, options);
      } else if (this.config.provider === 'anthropic') {
        return await this.callAnthropicDirect(enhancedMessages, options);
      } else {
        throw new AIConfigurationError(`Unsupported AI provider: ${this.config.provider}`, this.getConfigHelp());
      }
    } catch (error) {
      if (error instanceof AIConfigurationError) {
        throw error;
      }

      // Check for common configuration issues
      if (error instanceof Error) {
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
          throw new AIConfigurationError('Invalid API key', this.getConfigHelp());
        }
        if (error.message.includes('ECONNREFUSED') || error.message.includes('network')) {
          throw new AIConfigurationError('Cannot connect to AI service', this.getConfigHelp());
        }
        if (error.message.includes('timeout')) {
          throw new AIConfigurationError('AI service timeout', this.getConfigHelp());
        }
      }

      throw new AIConfigurationError(
        `AI service error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        this.getConfigHelp()
      );
    }
  }

  async testConnection(): Promise<{ success: boolean; error?: string; configHelp?: string }> {
    try {
      const testMessages: AIMessage[] = [
        {
          role: 'user',
          content: 'Reply with exactly "TEST_OK" if you can process this message.'
        }
      ];

      const response = await this.generateText(testMessages, {
        temperature: 0,
        maxTokens: 10
      });

      if (response.content.includes('TEST_OK')) {
        return { success: true };
      } else {
        return {
          success: false,
          error: 'AI service responded but response format was unexpected',
          configHelp: this.getConfigHelp()
        };
      }

    } catch (error) {
      if (error instanceof AIConfigurationError) {
        return {
          success: false,
          error: error.message,
          configHelp: error.configHelp
        };
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        configHelp: this.getConfigHelp()
      };
    }
  }

  private getConfigHelp(): string {
    return `
🔧 AI Configuration Help:

1. Check your .env file:
   - LITELLM_API_KEY=your_api_key_here
   - LITELLM_BASE_URL=http://localhost:4000/v1
   - LITELLM_MODEL_ID=gpt-4

2. Ensure LiteLLM server is running:
   - Start LiteLLM: litellm --config config.yaml
   - Test connection: curl ${this.config.baseUrl}/health

3. Verify API key is valid:
   - Check if API key has sufficient credits
   - Ensure API key has correct permissions

4. Alternative providers:
   - Set AI_PROVIDER=vertex for Google Vertex AI
   - Configure VERTEX_AI_PROJECT_ID and VERTEX_AI_LOCATION

📚 For more help, see: https://docs.litellm.ai/
`;
  }

  private async callLiteLLM(messages: AIMessage[], options?: {
    temperature?: number;
    maxTokens?: number;
  }): Promise<AIResponse> {
    const response = await axios.post(`${this.config.baseUrl}/chat/completions`, {
      model: this.config.modelId,
      messages: messages,
      temperature: options?.temperature || 0.3,
      max_tokens: options?.maxTokens || 4096,
      stream: false
    }, {
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Content-Type': 'application/json'
      },
      timeout: 60000
    });

    const result = response.data;
    return {
      content: result.choices[0].message.content,
      tokensUsed: result.usage?.total_tokens || 0
    };
  }

  private async callVertexAI(messages: AIMessage[], options?: {
    temperature?: number;
    maxTokens?: number;
  }): Promise<AIResponse> {
    try {
      const projectId = this.config.projectId;
      const location = this.config.location || 'us-central1';

      if (!projectId) {
        throw new Error('Project ID not found. Set VERTEX_AI_PROJECT_ID or configure gcloud CLI.');
      }

      // Determine model and API format based on model ID
      const modelId = this.config.modelId || 'gemini-1.5-pro-001';

      if (modelId.includes('claude') || modelId.includes('anthropic')) {
        return await this.callVertexAnthropicSDK(projectId, location, modelId, messages, options);
      } else {
        return await this.callVertexGemini(projectId, location, modelId, messages, options);
      }

    } catch (error: any) {
      console.error('Vertex AI call failed:', error);

      if (error.message?.includes('authentication') || error.message?.includes('unauthorized')) {
        throw new AIConfigurationError(
          'Vertex AI authentication failed',
          `Please ensure you have valid Google Cloud credentials:
1. Run 'gcloud auth application-default login'
2. Or set GOOGLE_APPLICATION_CREDENTIALS environment variable
3. Ensure the Vertex AI API is enabled in your project
4. Check permissions: gcloud auth list`
        );
      }

      if (error.message?.includes('Project ID')) {
        throw new AIConfigurationError(
          error.message,
          `Please set your project ID:
1. Set VERTEX_AI_PROJECT_ID in .env file
2. Or run 'gcloud config set project YOUR_PROJECT_ID'`
        );
      }

      throw new AIConfigurationError(
        `Vertex AI error: ${error.message}`,
        `Troubleshooting steps:
1. Ensure Vertex AI API is enabled: gcloud services enable aiplatform.googleapis.com
2. Check authentication: gcloud auth list
3. Verify project access: gcloud config get-value project
4. Try: gcloud auth application-default login`
      );
    }
  }

  /**
   * Get access token for Vertex AI API calls
   */
  private async getVertexAIAccessToken(): Promise<string> {
    try {
      const { GoogleAuth } = await import('google-auth-library');

      const auth = new GoogleAuth({
        scopes: ['https://www.googleapis.com/auth/cloud-platform']
      });

      const authClient = await auth.getClient();
      const accessTokenResponse = await authClient.getAccessToken();

      if (!accessTokenResponse.token) {
        throw new Error('Failed to get access token');
      }

      return accessTokenResponse.token;
    } catch (error: any) {
      throw new Error(`Authentication failed: ${error?.message || 'Unknown error'}`);
    }
  }

  /**
   * Call Vertex AI with Anthropic Claude models using official SDK
   */
  private async callVertexAnthropicSDK(
    projectId: string,
    location: string,
    modelId: string,
    messages: AIMessage[],
    options?: { temperature?: number; maxTokens?: number }
  ): Promise<AIResponse> {

    try {
      const { AnthropicVertex } = await import('@anthropic-ai/vertex-sdk');

      const client = new AnthropicVertex({
        projectId: projectId,
        region: location,
      });

      // Convert messages to Anthropic format
      const anthropicMessages = messages
        .filter(msg => msg.role !== 'system')
        .map(msg => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content
        }));

      const systemMessage = messages.find(msg => msg.role === 'system')?.content;

      const response = await client.messages.create({
        model: modelId,
        max_tokens: options?.maxTokens || 4096,
        temperature: options?.temperature || 0.7,
        messages: anthropicMessages,
        ...(systemMessage && { system: systemMessage })
      });

      if (!response.content || response.content.length === 0) {
        throw new Error('No content in Anthropic Vertex response');
      }

      const textContent = response.content.find((block: any) => block.type === 'text');
      if (!textContent || textContent.type !== 'text') {
        throw new Error('No text content found in Anthropic Vertex response');
      }

      return {
        content: textContent.text,
        tokensUsed: response.usage.input_tokens + response.usage.output_tokens
      };

    } catch (error: any) {
      console.error('Anthropic Vertex AI call failed:', error);

      if (error.message?.includes('not found') || error.message?.includes('404')) {
        throw new AIConfigurationError(
          'Anthropic model not found in Vertex AI',
          `Please ensure:
1. The model "${modelId}" is available in Vertex AI
2. Your project has access to Anthropic models
3. The model is available in the "${location}" region
4. Try using a valid Anthropic model like: claude-3-5-sonnet-v2@20241022`
        );
      }

      if (error.message?.includes('permission') || error.message?.includes('403')) {
        throw new AIConfigurationError(
          'Permission denied for Anthropic models in Vertex AI',
          `Please ensure:
1. Your project has permission to use Anthropic models
2. The Vertex AI API is enabled
3. You have proper IAM permissions for AI Platform
4. Try: gcloud auth application-default login`
        );
      }

      if (error.message?.includes('authentication') || error.message?.includes('401')) {
        throw new AIConfigurationError(
          'Vertex AI authentication failed',
          `Please ensure you have valid Google Cloud credentials:
1. Run 'gcloud auth application-default login'
2. Or set GOOGLE_APPLICATION_CREDENTIALS environment variable
3. Ensure the Vertex AI API is enabled in your project`
        );
      }

      throw new Error(`Anthropic via Vertex AI error: ${error.message}`);
    }
  }

  /**
   * Call Vertex AI with Google Gemini models
   */
  private async callVertexGemini(
    projectId: string,
    location: string,
    modelId: string,
    messages: AIMessage[],
    options?: { temperature?: number; maxTokens?: number }
  ): Promise<AIResponse> {

    try {
      // Use Google Cloud Vertex AI SDK
      const { PredictionServiceClient } = await import('@google-cloud/aiplatform');
      const { GoogleAuth } = await import('google-auth-library');

      // Initialize authentication
      const auth = new GoogleAuth({
        scopes: ['https://www.googleapis.com/auth/cloud-platform']
      });

      const authClient = await auth.getClient();
      const accessToken = await authClient.getAccessToken();

      if (!accessToken.token) {
        throw new Error('Failed to get access token for Gemini');
      }

      // Convert messages to Gemini format
      const contents = [];
      let systemInstruction = '';

      for (const message of messages) {
        if (message.role === 'system') {
          systemInstruction = message.content;
        } else {
          contents.push({
            role: message.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: message.content }]
          });
        }
      }

      const requestBody = {
        contents,
        generationConfig: {
          temperature: options?.temperature || 0.7,
          maxOutputTokens: options?.maxTokens || 4096,
          topP: 0.8,
          topK: 40
        },
        safetySettings: [
          { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
          { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
          { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
          { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' }
        ],
        ...(systemInstruction && { systemInstruction: { parts: [{ text: systemInstruction }] } })
      };

      const url = `https://${location}-aiplatform.googleapis.com/v1/projects/${projectId}/locations/${location}/publishers/google/models/${modelId}:generateContent`;

      const response = await axios.post(url, requestBody, {
        headers: {
          'Authorization': `Bearer ${accessToken.token}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000
      });

      if (!response.data?.candidates?.[0]?.content?.parts?.[0]?.text) {
        throw new Error('Invalid response format from Gemini via Vertex AI');
      }

      const content = response.data.candidates[0].content.parts[0].text;
      const tokensUsed = response.data.usageMetadata?.totalTokenCount || Math.ceil(content.length / 4);

      return {
        content,
        tokensUsed
      };

    } catch (error: any) {
      console.error('Gemini Vertex AI call failed:', error);
      throw new Error(`Gemini via Vertex AI error: ${error.message}`);
    }
  }

  /**
   * Call Anthropic API directly using official SDK
   */
  private async callAnthropicDirect(messages: AIMessage[], options?: {
    temperature?: number;
    maxTokens?: number;
  }): Promise<AIResponse> {
    try {
      const Anthropic = (await import('@anthropic-ai/sdk')).default;

      if (!this.config.apiKey) {
        throw new Error('Anthropic API key is required. Set ANTHROPIC_API_KEY in your .env file.');
      }

      const anthropic = new Anthropic({
        apiKey: this.config.apiKey,
      });

      // Convert messages to Anthropic format
      const anthropicMessages = messages
        .filter(msg => msg.role !== 'system')
        .map(msg => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content
        }));

      const systemMessage = messages.find(msg => msg.role === 'system')?.content;

      const response = await anthropic.messages.create({
        model: this.config.modelId || 'claude-3-5-sonnet-20241022',
        max_tokens: options?.maxTokens || 4096,
        temperature: options?.temperature || 0.7,
        messages: anthropicMessages,
        ...(systemMessage && { system: systemMessage })
      });

      if (!response.content || response.content.length === 0) {
        throw new Error('No content in Anthropic response');
      }

      const textContent = response.content.find(block => block.type === 'text');
      if (!textContent || textContent.type !== 'text') {
        throw new Error('No text content found in Anthropic response');
      }

      return {
        content: textContent.text,
        tokensUsed: response.usage.input_tokens + response.usage.output_tokens
      };

    } catch (error: any) {
      console.error('Anthropic API call failed:', error);

      if (error.message?.includes('API key')) {
        throw new AIConfigurationError(
          'Anthropic API key error',
          `Please check your Anthropic API key:
1. Set ANTHROPIC_API_KEY in your .env file
2. Ensure the key is valid and has sufficient credits
3. Check https://console.anthropic.com/ for account status`
        );
      }

      throw new AIConfigurationError(
        `Anthropic API error: ${error.message}`,
        `Please check your Anthropic configuration and try again.
Error details: ${error.message}`
      );
    }
  }

  async generateResponse(prompt: string, options?: {
    temperature?: number;
    maxTokens?: number;
  }): Promise<string> {
    const messages: AIMessage[] = [
      {
        role: 'user',
        content: prompt
      }
    ];

    try {
      const response = await this.generateText(messages, options);
      return response.content;
    } catch (error) {
      console.warn('Failed to generate response:', error);
      throw error;
    }
  }

  async scoreRelevance(query: string, content: string): Promise<number> {
    const messages: AIMessage[] = [
      {
        role: 'system',
        content: 'You are a relevance scoring expert. Rate how relevant the given content is to the query on a scale of 0.0 to 1.0. Respond with only a number.'
      },
      {
        role: 'user',
        content: `Query: "${query}"\n\nContent: "${content.substring(0, 1000)}..."\n\nRelevance score (0.0-1.0):`
      }
    ];

    try {
      const response = await this.generateText(messages, { temperature: 0.1, maxTokens: 10 });
      const score = parseFloat(response.content.trim());
      return isNaN(score) ? 0.5 : Math.max(0, Math.min(1, score));
    } catch (error) {
      console.warn('Failed to score relevance, using default score:', error);
      return 0.5;
    }
  }

  async extractKeyInsights(content: string, query: string): Promise<string[]> {
    const messages: AIMessage[] = [
      {
        role: 'system',
        content: 'Extract 3-5 key insights from the content that are relevant to the query. Return as a JSON array of strings.'
      },
      {
        role: 'user',
        content: `Query: "${query}"\n\nContent: "${content.substring(0, 2000)}..."\n\nKey insights:`
      }
    ];

    try {
      const response = await this.generateText(messages, { temperature: 0.2, maxTokens: 500 });
      const cleanedContent = this.cleanJsonResponse(response.content);
      const insights = JSON.parse(cleanedContent);
      return Array.isArray(insights) ? insights : [];
    } catch (error) {
      console.warn('Failed to extract insights:', error);
      return [];
    }
  }

  async generateSearchQueries(originalQuery: string, depth: number, previousResults?: string[]): Promise<string[]> {
    let systemPrompt = `Generate 2-3 search queries to find comprehensive information about the topic.
    The queries should be diverse and explore different aspects of the topic.
    Return as a JSON array of strings.`;

    if (depth > 1) {
      systemPrompt += ` This is depth level ${depth}, so focus on more specific and detailed aspects.`;
    }

    const messages: AIMessage[] = [
      { role: 'system', content: systemPrompt },
      {
        role: 'user',
        content: `Original query: "${originalQuery}"\n\n${previousResults ? `Previous results context: ${previousResults.join(', ')}` : ''}\n\nGenerate search queries:`
      }
    ];

    try {
      const response = await this.generateText(messages, { temperature: 0.5, maxTokens: 200 });
      const cleanedContent = this.cleanJsonResponse(response.content);

      // Additional validation for empty or invalid content
      if (!cleanedContent || cleanedContent.length < 2) {
        console.warn('Empty or invalid AI response for search queries');
        return [originalQuery];
      }

      const queries = JSON.parse(cleanedContent);
      return Array.isArray(queries) ? queries : [originalQuery];
    } catch (error) {
      console.warn('Failed to generate search queries, using original:', error);
      return [originalQuery];
    }
  }

  async synthesizeResults(query: string, allContent: Array<{ url: string; title: string; content: string; relevanceScore: number; depth: number }>): Promise<{ answer: string; confidence: number; summary: string }> {
    const sortedContent = allContent
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, 20); // Use top 20 most relevant pieces

    const contentSummary = sortedContent
      .map((item, index) => `[${index + 1}] ${item.title} (Relevance: ${item.relevanceScore.toFixed(2)}, Depth: ${item.depth})\nURL: ${item.url}\nContent: ${item.content.substring(0, 800)}...`)
      .join('\n\n---\n\n');

    // Check if custom instructions exist and determine output format
    const hasCustomInstructions = this.config.customInstructions && this.config.customInstructions.trim().length > 0;

    let systemPrompt: string;
    let parseResponse: (content: string) => { answer: string; confidence: number; summary: string };

    if (hasCustomInstructions) {
      // Use custom instructions as primary directive
      systemPrompt = `You are an expert research analyst. Based on the collected research data, provide a comprehensive analysis following the custom format requirements that will be provided.

Important: The custom instructions contain the specific output format and requirements. Follow them exactly.

Research Guidelines:
1. Analyze all provided data thoroughly
2. Extract relevant information for the requested format
3. Ensure accuracy and completeness
4. Include source references where applicable
5. Maintain high attention to detail`;

      // Parser for custom instruction responses
      parseResponse = (content: string) => {
        // For custom instructions, return the raw content as answer
        // Extract confidence if present, otherwise default
        const confidenceMatch = content.match(/confidence[:\s]+([0-9.]+)/i);
        const confidence = confidenceMatch ? parseFloat(confidenceMatch[1]) : 0.8;

        // Extract summary if present in a structured way
        const summaryMatch = content.match(/(?:summary|executive summary)[:\s]*([^\n]{50,200})/i);
        const summary = summaryMatch ? summaryMatch[1].trim() : 'Comprehensive analysis completed following custom instructions.';

        return {
          answer: content,
          confidence: Math.max(0, Math.min(1, confidence)),
          summary: summary
        };
      };
    } else {
      // Use default JSON format
      systemPrompt = `You are an expert research analyst. Provide a comprehensive analysis based on the collected research data.

Format your response as JSON with the following structure:
{
  "answer": "Comprehensive detailed answer (minimum 1000 words)",
  "summary": "Executive summary (3-4 sentences)",
  "confidence": 0.85
}

The answer should be well-structured with:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Supporting Evidence
5. Implications
6. Conclusion

Include source references in the analysis. Rate your confidence from 0.0 to 1.0.`;

      // Parser for JSON responses
      parseResponse = (content: string) => {
        const cleanedContent = this.cleanJsonResponse(content);
        const result = JSON.parse(cleanedContent);
        return {
          answer: result.answer || 'No analysis available',
          confidence: Math.max(0, Math.min(1, result.confidence || 0.5)),
          summary: result.summary || 'No summary available'
        };
      };
    }

    const messages: AIMessage[] = [
      {
        role: 'system',
        content: systemPrompt
      },
      {
        role: 'user',
        content: `Research Query: "${query}"\n\nCollected Data from ${sortedContent.length} sources:\n\n${contentSummary}\n\nProvide comprehensive analysis:`
      }
    ];

    try {
      const response = await this.generateText(messages, {
        temperature: 0.3,
        maxTokens: 8192
      });

      return parseResponse(response.content);
    } catch (error) {
      console.warn('Failed to synthesize results:', error);
      return {
        answer: 'Failed to generate comprehensive analysis due to processing error.',
        confidence: 0.1,
        summary: 'Analysis could not be completed.'
      };
    }
  }
}