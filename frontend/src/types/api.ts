/**
 * TypeScript type definitions for DOTbot API
 * Generated from backend Pydantic schemas
 */

export interface ScrapeRequest {
  url: string;
  question?: string;
  max_depth?: number;
  // scrape_mode removed - always use "auto"
  categories?: string[];
  export_format?: 'csv' | 'json' | 'db';
}

export interface AIBehaviorReport {
  url: string;
  excerpt: string;
  full_text: string;
  categories: string[];
  source: string;
  date?: string;
  stance?: string;
  tone?: string;
  confidence: number; // Now 1-100 range
  keywords: string[];
  reasoning: string;
}

export interface ScrapeResult {
  structured_data: Array<Record<string, any>>;
  ai_reports?: AIBehaviorReport[];
  metadata: Record<string, any>;
  scrape_mode: string;
  success: boolean;
  error?: string;
}

export interface WorkflowOutput {
  success: boolean;
  result?: ScrapeResult;
  export_path?: string;
  error?: string;
  metadata: Record<string, any>;
}

export interface EvaluationMetrics {
  recall?: number;
  precision_llm?: number;
  semantic_fidelity?: number;
  faithfulness?: number;
  coverage?: number;
  novelty_score?: number;
  llm_agreement?: number;
  extraction_accuracy?: number;
  runtime?: number;
  success_rate?: number;
  completeness?: number;
  consistency?: number;
  evaluation_timestamp: string;
  evaluation_mode: string;
}

export interface WorkflowStatus {
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  start_time: string;
  current_step: string;
  step_description?: string;
  url: string;
  progress?: number;
  completed_time?: string;
  error?: string;
}

export interface AgentStep {
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: string;
  details?: string;
}