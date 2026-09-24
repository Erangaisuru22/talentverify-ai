/**
 * @file api.js
 * @description Centralized HTTP communication client for TalentVerifyAI frontend.
 * Provides unified request wrappers around the Fetch API with automated JSON serialization,
 * FormData detection, error extraction, and backend connectivity troubleshooting messages.
 */

// Base backend URL configured via environment variables (falls back to relative path for proxying)
const API_URL = import.meta.env.VITE_API_URL || '';

/**
 * Executes an HTTP request against the FastAPI backend with enhanced error parsing.
 *
 * @param {string} path - Target API endpoint relative path (e.g., '/api/auth').
 * @param {RequestInit} [options={}] - Standard Fetch options (method, headers, body, etc.).
 * @returns {Promise<any>} Parsed JSON response from the server.
 * @throws {Error} Human-readable error message explaining failure or validation details.
 */
export async function apiRequest(path, options = {}) {
  let response;
  try {
    // Configure default headers
    const headers = new Headers(options.headers || {});

    // Automatically set Content-Type to application/json for raw objects/strings (excluding FormData)
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    // Perform the HTTP fetch request
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    // Network connectivity failure (e.g., backend server not reachable or offline)
    throw new Error('Unable to connect to the FastAPI backend at http://127.0.0.1:8000.');
  }

  // Parse response body safely
  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    // Handle proxy failures or HTML error pages from Vite or reverse proxy
    if (response.status >= 500 && (text.includes('Proxy') || text.includes('ECONNREFUSED') || !text)) {
      throw new Error('Unable to connect to the backend server. Please make sure the FastAPI backend is running on http://127.0.0.1:8000.');
    }
    throw new Error(text || `The server returned an invalid response (${response.status}).`);
  }

  // Handle non-2xx HTTP responses and extract detailed FastAPI validation errors
  if (!response.ok) {
    if (response.status === 500 && !data.detail && !data.message) {
      throw new Error('Unable to reach the backend service (FastAPI on port 8000). Please start the backend.');
    }
    // FastAPI validation errors often come as an array in 'detail'
    const validation = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join(', ')
      : data.detail;
    throw new Error(validation || data.message || `Request failed (${response.status}).`);
  }

  return data;
}

/**
 * Helper to execute a JSON-body API request.
 *
 * @param {string} path - Target API endpoint path.
 * @param {string} method - HTTP method ('POST', 'PUT', 'PATCH', etc.).
 * @param {any} data - JavaScript payload to serialize as JSON.
 * @returns {Promise<any>}
 */
export function apiJson(path, method, data) {
  return apiRequest(path, { method, body: JSON.stringify(data) });
}

/**
 * Helper to upload multipart/form-data (e.g. CV files, documents).
 *
 * @param {string} path - Target API endpoint path.
 * @param {FormData} formData - FormData instance with file and form fields.
 * @returns {Promise<any>}
 */
export function apiForm(path, formData) {
  return apiRequest(path, { method: 'POST', body: formData });
}

