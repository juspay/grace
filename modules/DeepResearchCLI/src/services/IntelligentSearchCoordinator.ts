import { AIService } from './AIService';
import { ConfigService } from './ConfigService';
import { ExtractedLink, PageData } from '../types';

export interface SearchDecision {
  proceed: boolean;
  selectedLinks: string[];
  reason: string;
  confidence: number;
  refinedQuery?: string;
  searchStrategy: 'depth' | 'breadth' | 'focused' | 'pivot';
}

export interface ContentQualityAssessment {
  relevanceScore: number;
  completenessScore: number;
  qualityScore: number;
  missingAspects: string[];
  nextActions: ('continue_depth' | 'change_query' | 'focus_specific' | 'stop_sufficient')[];
  reasoning: string;
}

export interface DepthDecision {
  continueToNextDepth: boolean;
  newQuery?: string;
  focusAreas: string[];
  maxAdditionalPages: number;
  reason: string;
  confidence: number;
}

/**
 * Intelligent Search Coordinator - AI-driven decision making for search operations
 *
 * This service adds intelligence between each search step:
 * 1. Analyzes search results before link selection
 * 2. Evaluates content quality after page fetching
 * 3. Makes intelligent decisions about depth progression
 * 4. Refines queries based on findings
 * 5. Prioritizes custom instructions over generic research
 */
export class IntelligentSearchCoordinator {
  private aiService: AIService;
  private config: ConfigService;
  private customInstructions: string;

  constructor(aiService: AIService, customInstructions: string = '') {
    this.aiService = aiService;
    this.config = ConfigService.getInstance();
    this.customInstructions = customInstructions;
  }

  /**
   * Phase 1: Analyze search results and decide which links to pursue
   * Called after search results are obtained but before fetching pages
   */
  async analyzeSearchResults(
    query: string,
    searchResults: any[],
    depth: number
  ): Promise<SearchDecision> {
    try {
      const resultsContext = searchResults.slice(0, 15).map((result, index) =>
        `[${index + 1}] Title: ${result.title}\n   URL: ${result.url}\n   Snippet: ${result.snippet || 'No snippet'}\n   Engine: ${result.engine}\n   Score: ${result.score}`
      ).join('\n\n');

      const analysisPrompt = `
You are an AI Search Results Analyzer. Your job is to intelligently select the most valuable links for deep research.

RESEARCH QUERY: "${query}"
CURRENT DEPTH: ${depth}
SEARCH RESULTS:

${resultsContext}

${this.customInstructions ? `\nCUSTOM RESEARCH INSTRUCTIONS (HIGH PRIORITY):\n${this.customInstructions}\n` : ''}

DECISION CRITERIA:
1. **Relevance to Query**: How directly does each result address the research query?
2. **Information Potential**: Which sources likely contain comprehensive, technical details?
3. **Authority & Credibility**: Official documentation, developer guides, API references
4. **Uniqueness**: Avoid redundant sources, prioritize diverse information types
5. **Custom Instructions Alignment**: Prioritize sources that help fulfill custom requirements

INSTRUCTIONS:
- Select 5-8 most valuable links (URLs only)
- If custom instructions exist, they take ABSOLUTE PRIORITY over generic research
- Consider source authority: official docs > developer guides > tutorials > forums
- Ensure diverse information types for comprehensive coverage
- For payment connectors: prioritize API docs, integration guides, authentication details

Respond with JSON only:
{
  "proceed": true/false,
  "selectedLinks": ["url1", "url2", ...],
  "reason": "Explanation for selection strategy",
  "confidence": 0.0-1.0,
  "searchStrategy": "depth|breadth|focused|pivot",
  "refinedQuery": "optional improved query if original is insufficient"
}

Selection Strategy Guide:
- depth: Go deeper into specific technical areas
- breadth: Cover more general aspects
- focused: Narrow down to specific missing information
- pivot: Change direction based on findings
`;

      const response = await this.aiService.generateResponse(analysisPrompt, {
        temperature: 0.3,
        maxTokens: 600
      });

      const decision = this.parseAIDecision(response);

      // Apply safety checks
      const validUrls = searchResults.map(r => r.url);
      decision.selectedLinks = decision.selectedLinks.filter(url => validUrls.includes(url));

      // Ensure minimum quality
      if (decision.selectedLinks.length === 0) {
        decision.selectedLinks = searchResults
          .sort((a, b) => b.score - a.score)
          .slice(0, 3)
          .map(r => r.url);
        decision.reason = "Fallback: Selected top-scoring results";
      }

      return decision;

    } catch (error) {
      // Fallback decision
      return {
        proceed: true,
        selectedLinks: searchResults.slice(0, 5).map(r => r.url),
        reason: "Fallback selection due to analysis error",
        confidence: 0.6,
        searchStrategy: 'breadth'
      };
    }
  }

  /**
   * Phase 2: Assess content quality and determine next actions
   * Called after fetching and processing page content
   */
  async assessContentQuality(
    query: string,
    processedPages: PageData[],
    depth: number
  ): Promise<ContentQualityAssessment> {
    try {
      const contentSummary = processedPages
        .filter(page => page.relevanceScore >= 0.4)
        .sort((a, b) => b.relevanceScore - a.relevanceScore)
        .slice(0, 10)
        .map((page, index) =>
          `[${index + 1}] Title: ${page.title}\n   URL: ${page.url}\n   Relevance: ${(page.relevanceScore * 100).toFixed(1)}%\n   Content: ${page.content.substring(0, 400)}...`
        ).join('\n\n---\n\n');

      const assessmentPrompt = `
You are an AI Content Quality Assessor. Analyze the fetched content and determine research completeness.

RESEARCH QUERY: "${query}"
CURRENT DEPTH: ${depth}
PROCESSED PAGES: ${processedPages.length}
HIGH-QUALITY PAGES: ${processedPages.filter(p => p.relevanceScore >= 0.7).length}

${this.customInstructions ? `\nCUSTOM RESEARCH REQUIREMENTS:\n${this.customInstructions}\n` : ''}

CONTENT SUMMARY:
${contentSummary}

ASSESSMENT CRITERIA:
1. **Relevance Score**: How well does collected content address the query?
2. **Completeness Score**: What percentage of required information is covered?
3. **Quality Score**: How authoritative and detailed are the sources?
4. **Missing Aspects**: What key information is still needed?
5. **Custom Instructions Fulfillment**: How well do we meet custom requirements?

Respond with JSON only:
{
  "relevanceScore": 0.0-1.0,
  "completenessScore": 0.0-1.0,
  "qualityScore": 0.0-1.0,
  "missingAspects": ["aspect1", "aspect2", ...],
  "nextActions": ["continue_depth", "change_query", "focus_specific", "stop_sufficient"],
  "reasoning": "Detailed explanation of assessment and recommendations"
}

Action Guide:
- continue_depth: Current approach is working, go deeper
- change_query: Need different search terms for missing info
- focus_specific: Narrow search to specific missing aspects
- stop_sufficient: Adequate information collected
`;

      const response = await this.aiService.generateResponse(assessmentPrompt, {
        temperature: 0.2,
        maxTokens: 800
      });

      const assessment = this.parseContentAssessment(response);

      // Apply logical constraints
      if (processedPages.length === 0) {
        assessment.nextActions = ['change_query'];
        assessment.completenessScore = 0;
      }

      if (depth >= 4 && assessment.completenessScore >= 0.7) {
        assessment.nextActions = ['stop_sufficient'];
      }

      return assessment;

    } catch (error) {
      // Fallback assessment
      const highQualityPages = processedPages.filter(p => p.relevanceScore >= 0.6).length;
      return {
        relevanceScore: highQualityPages > 0 ? 0.6 : 0.3,
        completenessScore: Math.min(0.8, processedPages.length / 10),
        qualityScore: highQualityPages > 2 ? 0.7 : 0.4,
        missingAspects: ['Unable to assess specific gaps'],
        nextActions: processedPages.length >= 8 ? ['stop_sufficient'] : ['continue_depth'],
        reasoning: 'Fallback assessment due to analysis error'
      };
    }
  }

  /**
   * Phase 3: Decide whether to proceed to next depth level
   * Called before incrementing depth, with option to refine query
   */
  async decideDepthProgression(
    query: string,
    allPageData: PageData[],
    currentDepth: number,
    pendingLinks: { url: string; relevance: number }[]
  ): Promise<DepthDecision> {
    try {
      const knowledgeBase = allPageData
        .filter(page => page.relevanceScore >= 0.5)
        .sort((a, b) => b.relevanceScore - a.relevanceScore)
        .slice(0, 15)
        .map(page => `${page.title}: ${page.content.substring(0, 300)}...`)
        .join('\n\n');

      const highValueLinks = pendingLinks
        .filter(link => link.relevance >= 0.6)
        .slice(0, 10)
        .map(link => `${link.url} (${(link.relevance * 100).toFixed(1)}%)`)
        .join('\n');

      const decisionPrompt = `
You are an AI Research Depth Coordinator. Decide whether to continue deeper research.

RESEARCH QUERY: "${query}"
CURRENT DEPTH: ${currentDepth}
TOTAL PAGES PROCESSED: ${allPageData.length}
HIGH-QUALITY SOURCES: ${allPageData.filter(p => p.relevanceScore >= 0.7).length}
PENDING HIGH-VALUE LINKS: ${pendingLinks.filter(l => l.relevance >= 0.6).length}

${this.customInstructions ? `\nCUSTOM RESEARCH REQUIREMENTS:\n${this.customInstructions}\n` : ''}

CURRENT KNOWLEDGE BASE:
${knowledgeBase}

AVAILABLE HIGH-VALUE LINKS:
${highValueLinks}

DECISION FACTORS:
1. **Information Completeness**: Is the knowledge base sufficient for the query?
2. **Custom Requirements**: Are custom instructions fully satisfied?
3. **Quality vs Quantity**: Balance between depth and comprehensive coverage
4. **Diminishing Returns**: Will deeper research yield significant new insights?
5. **Resource Efficiency**: Cost/benefit of additional depth

DEPTH DECISION CRITERIA:
- STOP if: >85% complete OR custom requirements met OR no high-value pending links
- CONTINUE if: <70% complete OR custom requirements not met OR high-value links available
- REFINE QUERY if: Missing specific technical details or hitting irrelevant content

Respond with JSON only:
{
  "continueToNextDepth": true/false,
  "newQuery": "refined query if needed, null otherwise",
  "focusAreas": ["area1", "area2", ...],
  "maxAdditionalPages": 0-15,
  "reason": "Detailed explanation for decision",
  "confidence": 0.0-1.0
}
`;

      const response = await this.aiService.generateResponse(decisionPrompt, {
        temperature: 0.2,
        maxTokens: 600
      });

      const decision = this.parseDepthDecision(response);

      // Apply safety constraints
      if (currentDepth >= 5) {
        decision.continueToNextDepth = false;
        decision.reason = "Maximum depth reached";
      }

      if (allPageData.length >= 30) {
        decision.continueToNextDepth = false;
        decision.reason = "Sufficient data collected";
      }

      if (pendingLinks.length === 0) {
        decision.continueToNextDepth = false;
        decision.reason = "No more links to explore";
      }

      return decision;

    } catch (error) {
      // Fallback decision logic
      const hasQualitySources = allPageData.filter(p => p.relevanceScore >= 0.7).length >= 3;
      const hasSufficientData = allPageData.length >= 10;

      return {
        continueToNextDepth: !hasQualitySources && !hasSufficientData && currentDepth < 4,
        focusAreas: ['General research continuation'],
        maxAdditionalPages: Math.max(5, 15 - allPageData.length),
        reason: 'Fallback decision based on basic metrics',
        confidence: 0.5
      };
    }
  }

  /**
   * Generate refined search queries based on knowledge gaps
   */
  async generateRefinedQueries(
    originalQuery: string,
    missingAspects: string[],
    existingKnowledge: string
  ): Promise<string[]> {
    try {
      const refinementPrompt = `
You are an AI Query Refinement Specialist. Generate improved search queries to fill knowledge gaps.

ORIGINAL QUERY: "${originalQuery}"
MISSING ASPECTS: ${missingAspects.join(', ')}

${this.customInstructions ? `\nCUSTOM REQUIREMENTS:\n${this.customInstructions}\n` : ''}

EXISTING KNOWLEDGE SUMMARY:
${existingKnowledge.substring(0, 1500)}...

TASK: Generate 3-5 refined search queries that specifically target the missing aspects.

GUIDELINES:
- Make queries specific and technical
- Target authoritative sources (official docs, API references)
- Include relevant technical terms and specifications
- For payment connectors: focus on authentication, endpoints, API formats
- Ensure queries will find documentation, not just tutorials

Respond with JSON only:
{
  "refinedQueries": ["query1", "query2", "query3", ...],
  "reasoning": "Why these queries target the knowledge gaps"
}
`;

      const response = await this.aiService.generateResponse(refinementPrompt, {
        temperature: 0.4,
        maxTokens: 500
      });

      const result = this.parseQueryRefinement(response);
      return result.refinedQueries || [originalQuery];

    } catch (error) {
      // Fallback: generate basic refined queries
      return missingAspects.slice(0, 3).map(aspect =>
        `${originalQuery} ${aspect} documentation`
      );
    }
  }

  /**
   * Intelligently filter and prioritize links based on context
   */
  async prioritizeLinks(
    links: ExtractedLink[],
    query: string,
    currentKnowledge: string,
    focusAreas: string[]
  ): Promise<ExtractedLink[]> {
    try {
      const linkContext = links.slice(0, 20).map((link, index) =>
        `[${index + 1}] ${link.text}\n   URL: ${link.url}\n   Context: ${link.context || 'No context'}`
      ).join('\n\n');

      const prioritizationPrompt = `
You are an AI Link Prioritization Specialist. Rank links by their potential value for research.

RESEARCH QUERY: "${query}"
FOCUS AREAS: ${focusAreas.join(', ')}

${this.customInstructions ? `\nCUSTOM REQUIREMENTS:\n${this.customInstructions}\n` : ''}

CURRENT KNOWLEDGE GAPS:
${currentKnowledge.substring(0, 500)}...

AVAILABLE LINKS:
${linkContext}

PRIORITIZATION CRITERIA:
1. **Relevance to Focus Areas**: How well does the link address specific gaps?
2. **Authority**: Official docs > Developer guides > API refs > Tutorials > Forums
3. **Technical Depth**: Detailed technical information over general overviews
4. **Uniqueness**: New information vs redundant content
5. **Custom Instruction Alignment**: Direct relevance to custom requirements

Respond with JSON only:
{
  "prioritizedUrls": ["most_valuable_url", "second_most_valuable", ...],
  "reasoning": "Explanation of prioritization logic"
}

Return URLs in priority order (most valuable first), limit to top 10.
`;

      const response = await this.aiService.generateResponse(prioritizationPrompt, {
        temperature: 0.3,
        maxTokens: 600
      });

      const result = this.parseLinkPrioritization(response);

      // Map URLs back to link objects and maintain order
      const prioritizedLinks: ExtractedLink[] = [];
      const urlToLink = new Map(links.map(link => [link.url, link]));

      for (const url of result.prioritizedUrls || []) {
        const link = urlToLink.get(url);
        if (link) {
          prioritizedLinks.push(link);
        }
      }

      // Add any remaining links not in prioritized list
      const prioritizedUrls = new Set(result.prioritizedUrls || []);
      const remainingLinks = links.filter(link => !prioritizedUrls.has(link.url));

      return [...prioritizedLinks, ...remainingLinks];

    } catch (error) {
      // Fallback: return original order
      return links;
    }
  }

  // Helper methods for parsing AI responses
  private parseAIDecision(response: string): SearchDecision {
    try {
      const cleaned = this.cleanJsonResponse(response);
      const parsed = JSON.parse(cleaned);

      return {
        proceed: parsed.proceed ?? true,
        selectedLinks: Array.isArray(parsed.selectedLinks) ? parsed.selectedLinks : [],
        reason: parsed.reason || 'No reason provided',
        confidence: Math.max(0, Math.min(1, parsed.confidence ?? 0.7)),
        searchStrategy: ['depth', 'breadth', 'focused', 'pivot'].includes(parsed.searchStrategy)
          ? parsed.searchStrategy : 'breadth',
        refinedQuery: parsed.refinedQuery || undefined
      };
    } catch (error) {
      return {
        proceed: true,
        selectedLinks: [],
        reason: 'Failed to parse AI response',
        confidence: 0.5,
        searchStrategy: 'breadth'
      };
    }
  }

  private parseContentAssessment(response: string): ContentQualityAssessment {
    try {
      const cleaned = this.cleanJsonResponse(response);
      const parsed = JSON.parse(cleaned);

      return {
        relevanceScore: Math.max(0, Math.min(1, parsed.relevanceScore ?? 0.5)),
        completenessScore: Math.max(0, Math.min(1, parsed.completenessScore ?? 0.5)),
        qualityScore: Math.max(0, Math.min(1, parsed.qualityScore ?? 0.5)),
        missingAspects: Array.isArray(parsed.missingAspects) ? parsed.missingAspects : [],
        nextActions: Array.isArray(parsed.nextActions) ? parsed.nextActions : ['continue_depth'],
        reasoning: parsed.reasoning || 'No reasoning provided'
      };
    } catch (error) {
      return {
        relevanceScore: 0.5,
        completenessScore: 0.5,
        qualityScore: 0.5,
        missingAspects: ['Unable to assess'],
        nextActions: ['continue_depth'],
        reasoning: 'Failed to parse AI response'
      };
    }
  }

  private parseDepthDecision(response: string): DepthDecision {
    try {
      const cleaned = this.cleanJsonResponse(response);
      const parsed = JSON.parse(cleaned);

      return {
        continueToNextDepth: parsed.continueToNextDepth ?? false,
        newQuery: parsed.newQuery || undefined,
        focusAreas: Array.isArray(parsed.focusAreas) ? parsed.focusAreas : [],
        maxAdditionalPages: Math.max(0, Math.min(15, parsed.maxAdditionalPages ?? 5)),
        reason: parsed.reason || 'No reason provided',
        confidence: Math.max(0, Math.min(1, parsed.confidence ?? 0.5))
      };
    } catch (error) {
      return {
        continueToNextDepth: false,
        focusAreas: [],
        maxAdditionalPages: 5,
        reason: 'Failed to parse AI response',
        confidence: 0.3
      };
    }
  }

  private parseQueryRefinement(response: string): { refinedQueries: string[]; reasoning: string } {
    try {
      const cleaned = this.cleanJsonResponse(response);
      const parsed = JSON.parse(cleaned);

      return {
        refinedQueries: Array.isArray(parsed.refinedQueries) ? parsed.refinedQueries : [],
        reasoning: parsed.reasoning || 'No reasoning provided'
      };
    } catch (error) {
      return {
        refinedQueries: [],
        reasoning: 'Failed to parse AI response'
      };
    }
  }

  private parseLinkPrioritization(response: string): { prioritizedUrls: string[]; reasoning: string } {
    try {
      const cleaned = this.cleanJsonResponse(response);
      const parsed = JSON.parse(cleaned);

      return {
        prioritizedUrls: Array.isArray(parsed.prioritizedUrls) ? parsed.prioritizedUrls : [],
        reasoning: parsed.reasoning || 'No reasoning provided'
      };
    } catch (error) {
      return {
        prioritizedUrls: [],
        reasoning: 'Failed to parse AI response'
      };
    }
  }

  private cleanJsonResponse(content: string): string {
    // Remove markdown code blocks and clean response
    let cleaned = content
      .replace(/```json\s*\n?/gi, '')
      .replace(/```javascript\s*\n?/gi, '')
      .replace(/```\s*\n?/gi, '')
      .replace(/```\s*$/g, '')
      .trim();

    // Find JSON start
    const jsonMatch = cleaned.match(/[\{\[]/);
    if (jsonMatch) {
      cleaned = cleaned.substring(jsonMatch.index!);
    }

    // Find JSON end
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
}