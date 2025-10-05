export interface ResearchConfig {
  maxDepth: number;
  maxPagesPerDepth: number;
  maxTotalPages: number;
  maxConcurrentPages: number;
  linkRelevanceThreshold: number;
  timeoutPerPage: number;
  respectRobotsTxt: boolean;
  dataDirectory: string;
  historyFile: string;
  interactiveMode: boolean;
  enableDeepLinkCrawling: boolean;
  maxLinksPerPage: number;
  deepCrawlDepth: number;
  aiDrivenCrawling: boolean;
  aiLinkRanking: boolean;
  aiCompletenessCheck: boolean;
  searchResultsPerQuery : number;
}

export interface AIConfig {
  provider: 'litellm' | 'vertex' | 'anthropic';
  apiKey?: string;
  baseUrl?: string;
  modelId: string;
  projectId?: string;
  location?: string;
  customInstructionsFile?: string;
  customInstructions?: string;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  engine: string;
  score: number;
}

export interface PageData {
  url: string;
  title: string;
  content: string;
  links: ExtractedLink[];
  depth: number;
  relevanceScore: number;
  aiContent?: string;
  fetchTime: number;
  processingTime: number;
  error?: string;
  metadata?: {
    duration?: number;
    isPdf?: boolean;
    pdfPages?: number;
    pdfInfo?: any;
    [key: string]: any;
  };
}

export interface ExtractedLink {
  url: string;
  text: string;
  context?: string;
  relevanceScore: number;
}

export interface ResearchSession {
  id: string;
  query: string;
  startTime: number;
  endTime?: number;
  status: 'running' | 'completed' | 'cancelled' | 'failed';
  totalPages: number;
  maxDepthReached: number;
  finalAnswer?: string;
  confidence?: number;
  metadata: {
    totalLinksFound: number;
    errorCount: number;
    aiTokensUsed: number;
  };
}

export interface LogEntry {
  timestamp: number;
  type: 'search' | 'fetch' | 'process' | 'analysis' | 'error' | 'info' | 'warning';
  message: string;
  data?: any;
  depth?: number;
  url?: string;
  expandable?: boolean;
  expanded?: boolean;
  children?: LogEntry[];
}

export interface UserAction {
  type: 'skip' | 'cancel' | 'input' | 'expand' | 'collapse' | 'next';
  data?: any;
}