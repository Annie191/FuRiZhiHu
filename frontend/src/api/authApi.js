const MEMBER3_API_BASE = import.meta.env.VITE_MEMBER3_API_BASE || '/member3/api/v1';

async function authRequest(path, { token, ...options } = {}) {
  const response = await fetch(`${MEMBER3_API_BASE}${path}`, {
    cache: 'no-store',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.error?.details?.[0]?.message || payload.error?.message || `接口请求失败：HTTP ${response.status}`;
    throw new Error(`${path}：HTTP ${response.status}，${message}`);
  }

  return payload.data;
}

export function login(input) {
  return authRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function register(input) {
  return authRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function getMe(token) {
  return authRequest('/auth/me', { token });
}
