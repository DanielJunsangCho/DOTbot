/**
 * API client for DOTbot backend
 * Following CLAUDE.md frontend standards with proper error handling
 */

import axios, { AxiosResponse } from 'axios';
import { ScrapeRequest, WorkflowOutput, WorkflowStatus } from '../types/api';

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',
  timeout: 120000, // 2 minute timeout for initial requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Separate instance for async operations with shorter timeout
export const asyncApi = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',
  timeout: 10000, // 10 second timeout for status checks
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Add interceptors for async API as well
asyncApi.interceptors.request.use(
  (config) => {
    console.log(`Async API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

asyncApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Async API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Execute AI behavior analysis workflow
 */
export async function analyzeAIBehavior(request: ScrapeRequest): Promise<WorkflowOutput> {
  const response: AxiosResponse<WorkflowOutput> = await api.post(
    '/workflow/ai-behavior', 
    request
  );
  return response.data;
}

/**
 * Execute general scraping workflow
 */
export async function executeGeneralScrape(request: ScrapeRequest): Promise<WorkflowOutput> {
  const response: AxiosResponse<WorkflowOutput> = await api.post(
    '/workflow/general-scrape', 
    request
  );
  return response.data;
}

/**
 * Execute unified workflow (auto-detects analysis type)
 */
export async function executeUnifiedWorkflow(request: ScrapeRequest): Promise<WorkflowOutput> {
  const response: AxiosResponse<WorkflowOutput> = await api.post(
    '/workflow/execute', 
    request
  );
  return response.data;
}

/**
 * Get workflow status by ID
 */
export async function getWorkflowStatus(workflowId: string): Promise<WorkflowStatus | null> {
  try {
    const response: AxiosResponse<WorkflowStatus> = await api.get(
      `/workflow/status/${workflowId}`
    );
    return response.data;
  } catch (error) {
    // Return null if workflow not found
    return null;
  }
}

/**
 * Cancel running workflow
 */
export async function cancelWorkflow(workflowId: string): Promise<boolean> {
  try {
    await api.post(`/workflow/cancel/${workflowId}`);
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Get service health status
 */
export async function getHealthStatus(): Promise<{ status: string; service: string }> {
  const response = await api.get('/health');
  return response.data;
}

/**
 * Download export file
 */
export async function downloadExport(exportId: string): Promise<Blob> {
  const response = await api.get(`/scraping/export/${exportId}`, {
    responseType: 'blob'
  });
  return response.data;
}

/**
 * Get evaluation metrics summary
 */
export async function getMetricsSummary(days: number = 30): Promise<any> {
  const response = await api.get(`/evaluation/metrics/summary?days=${days}`);
  return response.data;
}

/**
 * Submit async AI behavior analysis workflow
 */
export async function submitAsyncAIBehaviorAnalysis(request: ScrapeRequest): Promise<{ task_id: string; estimated_duration_minutes: number }> {
  const asyncRequest = {
    ...request,
    max_concurrent_articles: 5,  // Reasonable concurrency
    timeout_minutes: 10          // 10 minute max timeout
  };
  
  const response: AxiosResponse<{ task_id: string; estimated_duration_minutes: number }> = await api.post(
    '/scraping/async-scrape',
    asyncRequest
  );
  return response.data;
}

/**
 * Get async task status and progress
 */
export async function getAsyncTaskStatus(taskId: string): Promise<{
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  total_items: number;
  completed_items: number;
  failed_items: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  duration_seconds: number;
} | null> {
  try {
    const response = await asyncApi.get(`/scraping/tasks/${taskId}/status`);
    return response.data;
  } catch (error: any) {
    if (error?.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Get async task results
 */
export async function getAsyncTaskResults(taskId: string): Promise<{
  task_id: string;
  status: string;
  results: WorkflowOutput;
  summary: {
    total_pages: number;
    successful_pages: number;
    failed_pages: number;
    ai_reports_found: number;
    total_processing_time: number;
  };
} | null> {
  try {
    const response = await asyncApi.get(`/scraping/tasks/${taskId}/results`);
    return response.data;
  } catch (error: any) {
    if (error?.response?.status === 404) {
      return null;
    }
    throw error;
  }
}