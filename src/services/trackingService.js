import { apiRequest } from './apiClient.js'

export function listInterviews(token, signal) {
  return apiRequest('/interviews', { token, signal })
}

export function createInterview(token, applicationId, interview) {
  return apiRequest(`/applications/${applicationId}/interviews`, {
    method: 'POST',
    token,
    body: interview,
  })
}

export function updateInterview(token, interviewId, updates) {
  return apiRequest(`/interviews/${interviewId}`, {
    method: 'PATCH',
    token,
    body: updates,
  })
}

export function listFollowUps(token, signal) {
  return apiRequest('/follow-ups', { token, signal })
}

export function createFollowUp(token, applicationId, followUp) {
  return apiRequest(`/applications/${applicationId}/follow-ups`, {
    method: 'POST',
    token,
    body: followUp,
  })
}

export function updateFollowUp(token, followUpId, updates) {
  return apiRequest(`/follow-ups/${followUpId}`, {
    method: 'PATCH',
    token,
    body: updates,
  })
}

export function listApplicationActivities(token, applicationId, signal) {
  return apiRequest(`/applications/${applicationId}/activities`, { token, signal })
}

export function createApplicationActivity(token, applicationId, activity) {
  return apiRequest(`/applications/${applicationId}/activities`, {
    method: 'POST',
    token,
    body: activity,
  })
}
