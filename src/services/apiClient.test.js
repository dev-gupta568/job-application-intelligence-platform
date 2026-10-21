import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest } from './apiClient.js'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('apiRequest', () => {
  it('sends bearer tokens in the request without persisting them', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 'account-1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiRequest('/auth/me', { token: 'temporary-token' })

    expect(result).toEqual({ id: 'account-1' })
    expect(fetchMock).toHaveBeenCalledOnce()
    expect(fetchMock.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer temporary-token')
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('exposes API validation errors as typed errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({
          detail: [{ loc: ['body', 'user_skills'], msg: 'Field required' }],
        }), {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(apiRequest('/applications/example/skill-match')).rejects.toMatchObject({
      name: 'ApiError',
      status: 422,
      message: 'user_skills: Field required',
    })
  })

  it('handles no-content responses without attempting to parse a body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))

    await expect(apiRequest('/applications/example', { method: 'DELETE' })).resolves.toBeNull()
  })

  it('rejects successful responses that are not JSON when JSON is expected', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response('not json', { status: 200, headers: { 'Content-Type': 'text/plain' } }),
      ),
    )

    await expect(apiRequest('/auth/me')).rejects.toBeInstanceOf(ApiError)
  })
})
