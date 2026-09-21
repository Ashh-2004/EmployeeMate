export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

let inMemoryToken = null;

export function setAuthToken(token) {
  inMemoryToken = token;
}

export function getAuthToken() {
  return inMemoryToken;
}

function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (inMemoryToken) {
    headers['Authorization'] = `Bearer ${inMemoryToken}`;
  }
  return headers;
}

export async function loginUser(empId, password) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ emp_id: empId, password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Authentication failed');
  }

  const data = await res.json();
  setAuthToken(data.access_token);
  return data;
}

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (res.ok) {
      const data = await res.json();
      return {
        healthy: data.status === 'healthy',
        llm_provider: data.llm_provider || 'ollama',
        llm_model: data.llm_model || ''
      };
    }
    return { healthy: false, llm_provider: 'offline', llm_model: '' };
  } catch (err) {
    return { healthy: false, llm_provider: 'offline', llm_model: '' };
  }
}

export async function fetchEmployees() {
  try {
    const res = await fetch(`${API_BASE_URL}/employees`, {
      headers: getAuthHeaders(),
    });
    if (res.ok) {
      const data = await res.json();
      return data.data || [];
    }
    return [];
  } catch (err) {
    console.error('Failed to fetch live employees:', err);
    return [];
  }
}

export async function sendChatMessage(prompt, empId, history = [], category = null) {
  const last10 = (history || []).slice(-10);
  const formattedHistory = last10.map((msg) => ({
    role: msg.sender === 'user' ? 'user' : (msg.role || 'assistant'),
    content: msg.text || msg.content || ''
  }));

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      prompt: prompt,
      emp_id: empId,
      category: category,
      history: formattedHistory,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return await response.json();
}

export async function sendChatMessageStream({
  prompt,
  empId,
  history = [],
  category = null,
  onMetadata,
  onToken,
  onError
}) {
  const last10 = (history || []).slice(-10);
  const formattedHistory = last10.map((msg) => ({
    role: msg.sender === 'user' ? 'user' : (msg.role || 'assistant'),
    content: msg.text || msg.content || ''
  }));

  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        prompt: prompt,
        emp_id: empId,
        category: category,
        history: formattedHistory,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;
        const dataStr = trimmed.replace('data: ', '');

        if (dataStr === '[DONE]') {
          return;
        }

        try {
          const parsed = JSON.parse(dataStr);
          if (parsed.type === 'metadata' && onMetadata) {
            onMetadata(parsed);
          } else if (parsed.type === 'token' && onToken) {
            onToken(parsed.token);
          } else if (parsed.type === 'error' && onError) {
            onError(parsed.error);
          }
        } catch (e) {
          console.warn('Failed to parse SSE payload:', dataStr);
        }
      }
    }
  } catch (err) {
    if (onError) onError(err.message);
  }
}
