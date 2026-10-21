const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
).replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function getErrorMessage(payload, status) {
  if (typeof payload?.detail === 'string') {
    return payload.detail
  }

  if (Array.isArray(payload?.detail)) {
    return payload.detail
      .map((issue) => `${issue.loc?.slice(1).join('.') || 'Input'}: ${issue.msg}`)
      .join(' ')
  }

  return `The API request failed with status ${status}.`
}

export async function apiRequest(path, { method = 'GET', token, body, signal } = {}) {
  const headers = new Headers({ Accept: 'application/json' })
  let requestBody

  if (body instanceof URLSearchParams) {
    headers.set('Content-Type', 'application/x-www-form-urlencoded')
    requestBody = body
  } else if (body !== undefined) {
    headers.set('Content-Type', 'application/json')
    requestBody = JSON.stringify(body)
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: requestBody,
    signal,
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    throw new ApiError(getErrorMessage(payload, response.status), response.status)
  }

  if (response.status === 204) {
    return null
  }

  if (!contentType.includes('application/json')) {
    throw new ApiError('The API returned an unexpected non-JSON response.', response.status)
  }

  return payload
}
