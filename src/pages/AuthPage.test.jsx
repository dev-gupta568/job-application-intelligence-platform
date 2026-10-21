import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthContext } from '../context/authContext.js'
import AuthPage from './AuthPage.jsx'

function renderLogin(login, initialEntry = '/login') {
  const auth = {
    isLoading: false,
    login,
    register: vi.fn(),
    user: null,
    accessToken: null,
    logout: vi.fn(),
  }

  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/dashboard" element={<h1>Private dashboard</h1>} />
          <Route path="/applications" element={<h1>Private applications</h1>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )

  return auth
}

describe('AuthPage', () => {
  it('trims the email and returns to the requested protected destination', async () => {
    const user = userEvent.setup()
    const login = vi.fn().mockResolvedValue(undefined)
    renderLogin(login, {
      pathname: '/login',
      state: { from: '/applications' },
    })

    await user.type(screen.getByLabelText('Email address'), '  learner@example.com  ')
    await user.type(screen.getByLabelText('Password'), 'a-long-test-password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => expect(login).toHaveBeenCalledWith(
      'learner@example.com',
      'a-long-test-password',
    ))
    expect(await screen.findByRole('heading', { name: 'Private applications' })).toBeInTheDocument()
  })

  it('shows API failures without navigating into the workspace', async () => {
    const user = userEvent.setup()
    const login = vi.fn().mockRejectedValue(new Error('Incorrect email or password.'))
    renderLogin(login)

    await user.type(screen.getByLabelText('Email address'), 'learner@example.com')
    await user.type(screen.getByLabelText('Password'), 'incorrect-password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password.')
    expect(screen.queryByRole('heading', { name: 'Private dashboard' })).not.toBeInTheDocument()
  })

  it('keeps registration passwords at the backend minimum length', () => {
    const auth = {
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      user: null,
      accessToken: null,
      logout: vi.fn(),
    }
    render(
      <AuthContext.Provider value={auth}>
        <MemoryRouter initialEntries={['/register']}>
          <Routes>
            <Route path="/register" element={<AuthPage mode="register" />} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>,
    )

    expect(screen.getByLabelText(/Password/)).toHaveAttribute('minLength', '12')
    expect(screen.getByLabelText('Your name')).toBeRequired()
  })
})
