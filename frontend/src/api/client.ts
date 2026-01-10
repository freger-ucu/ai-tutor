/**
 * API Client
 *
 * Base client for communicating with the AI Tutor backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Base fetch wrapper with common configuration
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * API client with typed methods
 */
export const api = {
  /**
   * Health check
   */
  health: () => request<{ status: string }>('/api/v1/health'),

  // TODO: Add more API methods as endpoints are implemented
  // teacher: { ... },
  // student: { ... },
  // benchmark: { ... },
};

export default api;
