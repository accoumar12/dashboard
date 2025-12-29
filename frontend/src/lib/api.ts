/**
 * API client for the SQL Dashboard backend.
 */

import axios from 'axios';
import type { DatabaseSchema, QueryRequest, QueryResponse } from '../types';

/**
 * Health check response.
 */
export interface HealthCheckResponse {
  status: string;
}

/**
 * Upload response interface.
 */
export interface UploadResponse {
  session_id: string;
  redirect_url: string;
  file_size_mb: number;
  expires_at: string;
}

/**
 * Create a session-specific API client.
 */
export const createApiClient = (sessionId: string) => {
  return axios.create({
    baseURL: `/api/${sessionId}`,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};

/**
 * Upload a database file.
 */
export const uploadDatabase = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post<UploadResponse>('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = (progressEvent.loaded / progressEvent.total) * 100;
        onProgress(progress);
      }
    },
  });

  return response.data;
};

/**
 * Check if the backend is healthy.
 */
export const checkHealth = async (): Promise<HealthCheckResponse> => {
  const response = await axios.get<HealthCheckResponse>('/api/health');
  return response.data;
};

/**
 * Get database schema information for a specific session.
 */
export const getSchema = async (sessionId: string): Promise<DatabaseSchema> => {
  const api = createApiClient(sessionId);
  const response = await api.get<DatabaseSchema>('/schema');
  return response.data;
};

/**
 * Query a table with filters and pagination for a specific session.
 */
export const queryTable = async (
  sessionId: string,
  request: QueryRequest
): Promise<QueryResponse> => {
  const api = createApiClient(sessionId);
  const response = await api.post<QueryResponse>('/query', request);
  return response.data;
};

/**
 * Get distinct column values for a specific session.
 */
export const getColumnValues = async (
  sessionId: string,
  table: string,
  column: string,
  limit: number = 100
): Promise<string[]> => {
  const api = createApiClient(sessionId);
  const response = await api.get<{ values: string[] }>(
    `/column-values/${table}/${column}?limit=${limit}`
  );
  return response.data.values;
};
