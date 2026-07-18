const MEMBER3_API_BASE = import.meta.env.VITE_MEMBER3_API_BASE || '/member3/api/v1';

async function request(path, { token, body, ...options } = {}) {
  const response = await fetch(`${MEMBER3_API_BASE}${path}`, {
    cache: 'no-store',
    headers: {
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    body: body ? JSON.stringify(body) : undefined,
    ...options,
  });

  if (response.status === 204) return null;

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.error?.details?.[0]?.message || payload.error?.message || `接口请求失败：HTTP ${response.status}`;
    throw new Error(`${path}：HTTP ${response.status}，${message}`);
  }

  return payload.data;
}

function queryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key === 'from' ? 'from_date' : key, value);
    }
  });
  const text = query.toString();
  return text ? `?${text}` : '';
}

export function getProfile(token) {
  return request('/profile', { token });
}

export function updateProfile(token, body) {
  return request('/profile', { method: 'PATCH', token, body });
}

export function getFoods(params = {}) {
  return request(`/foods${queryString(params)}`);
}

export function listRecords(token, kind, params = {}) {
  return request(`/${kind}-records${queryString(params)}`, { token });
}

export function createRecord(token, kind, body) {
  return request(`/${kind}-records`, { method: 'POST', token, body });
}

export function updateRecord(token, kind, id, body) {
  return request(`/${kind}-records/${id}`, { method: 'PATCH', token, body });
}

export function deleteRecord(token, kind, id) {
  return request(`/${kind}-records/${id}`, { method: 'DELETE', token });
}

export function getDailySummary(token, kind, params = {}) {
  return request(`/${kind}-records/daily-summary${queryString(params)}`, { token });
}
