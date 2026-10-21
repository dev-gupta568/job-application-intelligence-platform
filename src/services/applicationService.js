import { apiRequest } from './apiClient.js'

export function listApplications(token, filters = {}, signal) {
  const query = new URLSearchParams({
    page: '1',
    page_size: '100',
    sort_by: 'applied_on',
    sort_order: 'desc',
  })

  for (const [key, value] of Object.entries(filters)) {
    if (value) {
      query.set(key, value)
    }
  }

  return apiRequest(`/applications?${query}`, { token, signal })
}

export function createApplication(token, application) {
  return apiRequest('/applications', {
    method: 'POST',
    token,
    body: application,
  })
}

export function updateApplication(token, applicationId, updates) {
  return apiRequest(`/applications/${applicationId}`, {
    method: 'PATCH',
    token,
    body: updates,
  })
}

export function deleteApplication(token, applicationId) {
  return apiRequest(`/applications/${applicationId}`, {
    method: 'DELETE',
    token,
  })
}
