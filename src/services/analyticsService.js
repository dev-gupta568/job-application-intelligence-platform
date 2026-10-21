import { apiRequest } from './apiClient.js'

export function getDashboardAnalytics(token, { weeks = 12, months = 6, signal } = {}) {
  const query = new URLSearchParams({
    weeks: String(weeks),
    months: String(months),
  })
  return apiRequest(`/analytics/dashboard?${query}`, { token, signal })
}
