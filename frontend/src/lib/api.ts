const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchApi(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Portfolio
  getPortfolio: () => fetchApi('/portfolio'),
  getTickerHistory: (ticker: string, days = 90) =>
    fetchApi(`/portfolio/${ticker}/history?days=${days}`),

  // Push
  getDigest: (hours = 24) => fetchApi(`/push/digest?hours=${hours}`),
  getAlerts: (unreadOnly = true) => fetchApi(`/push/alerts?unread_only=${unreadOnly}`),
  getBriefing: (hours = 24) => fetchApi(`/push/briefing?hours=${hours}`),
  markAlertRead: (id: number) => fetchApi(`/push/alerts/${id}/read`, { method: 'POST' }),

  // Pull
  researchCompany: (ticker: string, analysis: string) =>
    fetchApi(`/pull/research/${ticker}?analysis=${analysis}`),
  chat: (message: string) =>
    fetchApi('/pull/chat', { method: 'POST', body: JSON.stringify({ message }) }),

  // Data refresh
  refreshPrices: () => fetchApi('/data/refresh/prices', { method: 'POST' }),
  refreshAnnouncements: (days = 7) =>
    fetchApi(`/data/refresh/announcements?days=${days}`, { method: 'POST' }),
  classifyAnnouncements: () => fetchApi('/data/classify', { method: 'POST' }),

  // Settings
  getSettings: () => fetchApi('/settings'),
  updateSettings: (settings: any) =>
    fetchApi('/settings', { method: 'PUT', body: JSON.stringify(settings) }),
};
