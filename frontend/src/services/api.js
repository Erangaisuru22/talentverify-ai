const API_URL = import.meta.env.VITE_API_URL || '';

export async function apiRequest(path, options = {}) {
  let response;
  try {
    const headers = new Headers(options.headers || {});
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error('Unable to connect to the FastAPI backend at http://127.0.0.1:8000.');
  }

  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(text || `The server returned an invalid response (${response.status}).`);
  }
  if (!response.ok) {
    const validation = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join(', ')
      : data.detail;
    throw new Error(validation || data.message || `Request failed (${response.status}).`);
  }
  return data;
}

export function apiJson(path, method, data) {
  return apiRequest(path, { method, body: JSON.stringify(data) });
}

export function apiForm(path, formData) {
  return apiRequest(path, { method: 'POST', body: formData });
}
