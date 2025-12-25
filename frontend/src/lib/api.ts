/**
 * API client for the SQL Dashboard backend.
 */

import axios from 'axios';
import type { DatabaseSchema, QueryRequest, QueryResponse } from '../types';

/**
 * Axios instance configured for the dashboard API.
 */
export const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Health check response.
 */
export interface HealthCheckResponse {
  status: string;
}

/**
 * Check if the backend is healthy.
 */
export const checkHealth = async (): Promise<HealthCheckResponse> => {
  const response = await api.get<HealthCheckResponse>('/health');
  return response.data;
};

/**
 * Get database schema information.
 */
export const getSchema = async (): Promise<DatabaseSchema> => {
  const response = await api.get<DatabaseSchema>('/schema');
  return response.data;
};

/**
 * Query a table with filters and pagination.
 */
export const queryTable = async (request: QueryRequest): Promise<QueryResponse> => {
  const response = await api.post<QueryResponse>('/query', request);
  return response.data;
};
