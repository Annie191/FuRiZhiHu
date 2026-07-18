const MEMBER5_API_BASE = import.meta.env.VITE_MEMBER5_API_BASE || '/member5/api';

async function request(path, options = {}) {
  const response = await fetch(`${MEMBER5_API_BASE}${path}`, {
    headers: {
      Accept: 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`${path}：HTTP ${response.status}，接口请求失败`);
  }

  const payload = await response.json();
  if (payload.code !== 0) {
    throw new Error(`${path}：${payload.msg || '接口返回异常'}`);
  }
  return payload.data;
}

export function getDashboardUsers() {
  return request('/dashboard/users');
}

export function getDashboard(userId, { date, city } = {}) {
  const params = new URLSearchParams();
  if (date) params.set('date', date);
  if (city) params.set('city', city);
  const query = params.toString();
  return request(`/dashboard/${userId}${query ? `?${query}` : ''}`);
}

export function getHealthScoreTrend(userId, days = 30) {
  return request(`/trend/${userId}/health-score?days=${days}`);
}

export function getTrendSummary(userId, days = 30) {
  return request(`/trend/${userId}/summary?days=${days}`);
}

export function getDashboardSeries(userId, params = {}) {
  const query = new URLSearchParams();
  if (params.from) query.set('from', params.from);
  if (params.to) query.set('to', params.to);
  const text = query.toString();
  return request(`/dashboard/${userId}/series${text ? `?${text}` : ''}`);
}

export function getDailyReport(userId, date) {
  return request(`/report/${userId}/daily?date=${encodeURIComponent(date)}`);
}

export function getWeeklyReport(userId, params = {}) {
  const query = new URLSearchParams();
  if (params.startDate) query.set('start_date', params.startDate);
  if (params.endDate) query.set('end_date', params.endDate);
  const text = query.toString();
  return request(`/report/${userId}/weekly${text ? `?${text}` : ''}`);
}

export function getPlans(userId, params = {}) {
  const query = new URLSearchParams();
  if (params.from) query.set('from', params.from);
  if (params.to) query.set('to', params.to);
  const text = query.toString();
  return request(`/plans/${userId}${text ? `?${text}` : ''}`);
}

export function getWeather(params = {}) {
  const query = new URLSearchParams();
  if (params.city) query.set('city', params.city);
  if (params.from) query.set('from', params.from);
  if (params.to) query.set('to', params.to);
  const text = query.toString();
  return request(`/weather${text ? `?${text}` : ''}`);
}

export function getCommunityPosts(limit = 20) {
  return request(`/community/posts?limit=${limit}`);
}
