/**
 * URL validation utilities - TypeScript equivalent of Python utils
 */

import { URL } from 'url';

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

export function validateUrl(urlString: string): ValidationResult {
  if (!urlString || urlString.trim() === '') {
    return { isValid: false, error: 'Empty URL' };
  }

  try {
    const url = new URL(urlString.trim());
    
    // Check if protocol is HTTP or HTTPS
    if (!['http:', 'https:'].includes(url.protocol)) {
      return { isValid: false, error: 'URL must use HTTP or HTTPS protocol' };
    }

    // Check if hostname is valid
    if (!url.hostname || url.hostname.length === 0) {
      return { isValid: false, error: 'Invalid hostname' };
    }

    return { isValid: true };
  } catch (error) {
    return { isValid: false, error: 'Invalid URL format' };
  }
}

export function deduplicateUrls(urls: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  
  for (const url of urls) {
    const normalized = url.trim().toLowerCase();
    if (!seen.has(normalized)) {
      seen.add(normalized);
      result.push(url.trim());
    }
  }
  
  return result;
}

export function validateUrlsBatch(urls: string[]): {
  validUrls: string[];
  invalidUrls: Array<{ url: string; error: string }>;
} {
  const validUrls: string[] = [];
  const invalidUrls: Array<{ url: string; error: string }> = [];
  
  for (const url of urls) {
    const validation = validateUrl(url);
    if (validation.isValid) {
      validUrls.push(url);
    } else {
      invalidUrls.push({ url, error: validation.error || 'Unknown error' });
    }
  }
  
  return { validUrls, invalidUrls };
}