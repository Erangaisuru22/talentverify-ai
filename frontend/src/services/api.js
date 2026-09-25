/**
 * ============================================================================
 * @file api.js
 * @description Centralized HTTP communication client for TalentVerifyAI frontend.
 * 
 * CORE RESPONSIBILITIES:
 * 1. Unified HTTP request wrapper around modern browser Fetch API.
 * 2. Automated JSON serialization and FormData detection.
 * 3. Graceful error extraction (FastAPI validation arrays, network timeouts).
 * 4. Human-readable connection troubleshooting diagnostics for users and developers.
 * ============================================================================
 */

// ----------------------------------------------------------------------------
// JavaScript Keyword: `const`
// Declares an immutable reference to the base backend URL from environment variables.
// Fallback to empty string for Vite reverse-proxy configuration.
// ----------------------------------------------------------------------------
const API_URL = import.meta.env.VITE_API_URL || '';

/**
 * ----------------------------------------------------------------------------
 * JavaScript Keywords: `export async function`
 * - `export`: Makes this function accessible to other modules via `import { apiRequest }`.
 * - `async`: Defines an asynchronous function returning a Promise.
 * - `function`: Declares an executable function block with named arguments.
 * ----------------------------------------------------------------------------
 * Executes an HTTP request against the FastAPI backend with enhanced error parsing.
 *
 * @param {string} path - Target API endpoint relative path (e.g., '/api/auth').
 * @param {RequestInit} [options={}] - Standard Fetch options (method, headers, body, etc.).
 * @returns {Promise<any>} Parsed JSON response payload from the server.
 * @throws {Error} Human-readable error message explaining failure or validation details.
 */
export async function apiRequest(path, options = {}) {
  // JavaScript Keyword: `let`
  // Declares a block-scoped variable that can be reassigned later.
  let response;

  // JavaScript Keyword: `try...catch`
  // Robust exception handling block to prevent unexpected network errors from crashing the UI.
  try {
    // JavaScript Keyword: `new`
    // Instantiates a new object from a constructor (Headers class).
    const headers = new Headers(options.headers || {});

    // JavaScript Keywords: `if`, `instanceof`
    // - `if`: Evaluates condition.
    // - `instanceof`: Checks if the object is an instance of a specific class (FormData).
    // Automatically set Content-Type to application/json for objects (excluding file FormData)
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    // JavaScript Keyword: `await`
    // Pauses execution non-blockingly until the Fetch HTTP Promise resolves.
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    // JavaScript Keyword: `throw new Error(...)`
    // Creates and throws a new Error object when connection fails.
    throw new Error('Unable to connect to the FastAPI backend at http://127.0.0.1:8000.');
  }

  // Parse raw response text safely before converting to JSON
  const text = await response.text();
  let data = {};
  try {
    // Ternary operator: if text exists, parse JSON, else return empty object
    data = text ? JSON.parse(text) : {};
  } catch {
    // Handle reverse proxy failures or HTML 500 pages from Vite
    if (response.status >= 500 && (text.includes('Proxy') || text.includes('ECONNREFUSED') || !text)) {
      throw new Error('Unable to connect to the backend server. Please make sure the FastAPI backend is running on http://127.0.0.1:8000.');
    }
    throw new Error(text || `The server returned an invalid response (${response.status}).`);
  }

  // Handle non-2xx HTTP status codes and extract FastAPI validation details
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

  // JavaScript Keyword: `return`
  // Supplies the successfully parsed data back to the caller.
  return data;
}

/**
 * Helper function to execute a JSON-body API request.
 *
 * @param {string} path - Target API endpoint path.
 * @param {string} method - HTTP method ('POST', 'PUT', 'PATCH', etc.).
 * @param {any} data - JavaScript payload to serialize as JSON string.
 * @returns {Promise<any>}
 */
export function apiJson(path, method, data) {
  return apiRequest(path, { method, body: JSON.stringify(data) });
}

/**
 * Helper function to upload multipart/form-data (e.g., CV documents, profile photos).
 *
 * @param {string} path - Target API endpoint path.
 * @param {FormData} formData - FormData instance with file and form fields.
 * @returns {Promise<any>}
 */
export function apiForm(path, formData) {
  return apiRequest(path, { method: 'POST', body: formData });
}
