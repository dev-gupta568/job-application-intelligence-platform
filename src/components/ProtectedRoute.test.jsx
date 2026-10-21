import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { AuthContext } from '../context/authContext.js'
import ProtectedRoute from './ProtectedRoute.jsx'

function SignInDestination() {
  const location = useLocation()
  return <h1>Sign in to continue from {location.state?.from}</h1>
}

function renderProtectedRoute(auth) {
  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={['/applications']}>
        <Routes>
          <Route
            path="/applications"
            element={<ProtectedRoute><h1>Private applications</h1></ProtectedRoute>}
          />
          <Route path="/login" element={<SignInDestination />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects signed-out users to login with their requested path', () => {
    renderProtectedRoute({ user: null, isLoading: false })

    expect(screen.getByRole('heading', {
      name: 'Sign in to continue from /applications',
    })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Private applications' })).not.toBeInTheDocument()
  })

  it('waits for account checking instead of briefly showing a private route', () => {
    renderProtectedRoute({ user: null, isLoading: true })

    expect(screen.getByText('Checking your account…')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Private applications' })).not.toBeInTheDocument()
  })

  it('renders the protected page for a signed-in user', () => {
    renderProtectedRoute({
      user: { id: 'user-1', display_name: 'Learner' },
      isLoading: false,
    })

    expect(screen.getByRole('heading', { name: 'Private applications' })).toBeInTheDocument()
  })
})
