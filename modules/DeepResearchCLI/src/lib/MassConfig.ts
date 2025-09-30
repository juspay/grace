import { ResearchConfig, AIConfig } from '../types';

/**
 * Configuration interface for MassResearcher
 */
export interface MassConfig {
  /** AI service configuration */
  ai?: Partial<AIConfig>;
  /** Research behavior configuration */
  research?: Partial<ResearchConfig>;
}

/**
 * Comprehensive configuration options for MASS researcher
 */
export interface MassConfigDetailed extends MassConfig {
  /** Storage configuration */
  storage?: {
    /** Directory for storing research data */
    dataDirectory?: string;
    /** File for storing research history */
    historyFile?: string;
  };
  /** Debugging configuration */
  debug?: {
    /** Enable debug logging */
    enabled?: boolean;
    /** Debug log file path */
    logFile?: string;
  };
  /** Browser configuration */
  browser?: {
    /** Run browser in headless mode */
    headless?: boolean;
    /** Browser timeout in milliseconds */
    timeout?: number;
  };
  /** Proxy configuration */
  proxy?: {
    /** List of proxy URLs */
    list?: string[];
    /** Rotate proxies for requests */
    rotate?: boolean;
  };
}