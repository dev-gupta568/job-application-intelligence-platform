import { apiRequest } from './apiClient.js'

export function analyzeApplicationSkills(token, applicationId, analysis) {
  return apiRequest(`/applications/${applicationId}/skill-match`, {
    method: 'POST',
    token,
    body: analysis,
  })
}

export function listSkillMatches(token, signal) {
  return apiRequest('/skill-matches?limit=100', { token, signal })
}
