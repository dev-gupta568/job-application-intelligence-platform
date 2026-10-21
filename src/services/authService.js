import { apiRequest } from './apiClient.js'

export function registerAccount(details) {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: details,
  })
}

export function loginAccount(email, password) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: new URLSearchParams({ username: email, password }),
  })
}

export function getCurrentUser(token) {
  return apiRequest('/auth/me', { token })
}
