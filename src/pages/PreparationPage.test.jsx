import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext } from '../context/authContext.js'
import PreparationPage from './PreparationPage.jsx'

const application = {
  id: 'application-1',
  company_name: 'Northwind',
  job_title: 'Python API Engineer',
  job_description: 'Python engineer with FastAPI and PostgreSQL experience.',
  required_skills: ['FastAPI', 'PostgreSQL'],
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('PreparationPage', () => {
  it('loads saved applications, submits skills, and renders a transparent match analysis', async () => {
    const user = userEvent.setup()
    const savedAnalysis = {
      id: 'comparison-1',
      application_id: application.id,
      company_name: application.company_name,
      job_title: application.job_title,
      job_keywords: ['Python', 'FastAPI', 'PostgreSQL'],
      user_skills: ['Python', 'PostgreSQL'],
      matching_skills: ['Python', 'PostgreSQL'],
      missing_skills: ['FastAPI'],
      important_keywords: ['FastAPI', 'PostgreSQL'],
      match_percentage: '66.67',
      suggested_skills_to_learn: ['FastAPI'],
      resume_checklist: ['Use accurate project examples.'],
      algorithm_version: 'rule-based-v1',
      created_at: '2026-10-21T00:00:00Z',
    }
    const fetchMock = vi.fn(async (url, options = {}) => {
      if (String(url).includes('/applications?')) {
        return jsonResponse({ items: [application], total: 1, page: 1, page_size: 100 })
      }
      if (String(url).includes('/skill-matches')) {
        return jsonResponse([])
      }
      if (String(url).includes('/skill-match') && options.method === 'POST') {
        expect(JSON.parse(options.body)).toEqual({
          job_description: application.job_description,
          user_skills: ['Python', 'PostgreSQL'],
        })
        return jsonResponse(savedAnalysis, 201)
      }
      throw new Error(`Unexpected request: ${options.method || 'GET'} ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(
      <AuthContext.Provider value={{
        accessToken: 'test-token',
        logout: vi.fn(),
      }}>
        <MemoryRouter>
          <PreparationPage />
        </MemoryRouter>
      </AuthContext.Provider>,
    )

    expect(await screen.findByRole('option', { name: 'Northwind — Python API Engineer' })).toBeInTheDocument()
    await user.type(screen.getByRole('textbox', { name: /Your skills/ }), 'Python, PostgreSQL')
    await user.click(screen.getByRole('button', { name: 'Analyze skill match' }))

    expect(await screen.findByText('66.67%', { selector: '.match-score' })).toBeInTheDocument()
    expect(screen.getByText(/2 matching skills ÷ 3 recognized job requirements/)).toBeInTheDocument()
    const gaps = screen.getByRole('heading', { name: 'Missing skills' }).parentElement
    expect(within(gaps).getByText('FastAPI')).toBeInTheDocument()
    expect(await screen.findByText(/rule-based-v1/)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('1 saved')).toBeInTheDocument())
  })

  it('shows API errors instead of displaying a successful-looking empty result', async () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url) => (
      String(url).includes('/applications?')
        ? jsonResponse({ items: [], total: 0, page: 1, page_size: 100 })
        : jsonResponse({ detail: 'Analytics service unavailable.' }, 503)
    )))

    render(
      <AuthContext.Provider value={{
        accessToken: 'test-token',
        logout: vi.fn(),
      }}>
        <MemoryRouter>
          <PreparationPage />
        </MemoryRouter>
      </AuthContext.Provider>,
    )

    expect(await screen.findByRole('alert')).toHaveTextContent('Analytics service unavailable.')
    expect(screen.getByRole('heading', { name: 'Your match breakdown will appear here.' })).toBeInTheDocument()
  })
})
