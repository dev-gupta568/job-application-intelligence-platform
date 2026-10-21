import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'

function AuthPage({ mode }) {
  const isRegister = mode === 'register'
  const [notice, setNotice] = useState('')
  const { isLoading, login, register, user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const destination = location.state?.from || '/dashboard'

  if (user) {
    return <Navigate to={destination} replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setNotice('')
    const formData = new FormData(event.currentTarget)
    const email = formData.get('email').toString().trim()
    const password = formData.get('password').toString()

    try {
      if (isRegister) {
        await register({
          email,
          password,
          display_name: formData.get('display_name').toString().trim(),
        })
      } else {
        await login(email, password)
      }
      navigate(destination, { replace: true })
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Sign-in failed. Please try again.')
    }
  }

  return (
    <main className="auth-page">
      <header className="auth-header">
        <Link className="brand" to="/" aria-label="Application Atlas home">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>Application Atlas</span>
        </Link>
        <Link className="back-link" to="/">Back to home</Link>
      </header>

      <section className="auth-card" aria-labelledby="auth-title">
        <p className="eyebrow">Your job search, organized</p>
        <h1 id="auth-title">{isRegister ? 'Create your account' : 'Welcome back'}</h1>
        <p className="auth-description">
          {isRegister
            ? 'Set up a private workspace for your applications and interviews.'
            : 'Sign in to return to your application workspace.'}
        </p>

        <div className="auth-phase-note" role="status">
          Your account is private. Credentials are sent directly to the backend
          over the configured API connection.
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {isRegister && (
            <label>
              Your name
              <input
                autoComplete="name"
                name="display_name"
                placeholder="e.g. Jordan Davis"
                required
              />
            </label>
          )}
          <label>
            Email address
            <input
              autoComplete="email"
              name="email"
              placeholder="you@example.com"
              required
              type="email"
            />
          </label>
          <label>
            Password
            <input
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              minLength={isRegister ? 12 : undefined}
              name="password"
              required
              type="password"
            />
            {isRegister && <span className="field-hint">Use at least 12 characters.</span>}
          </label>
          <button className="auth-submit" type="submit" disabled={isLoading}>
            {isLoading
              ? 'Connecting…'
              : isRegister
                ? 'Create account'
                : 'Sign in'}
          </button>
          {notice && <p className="auth-notice" role="alert">{notice}</p>}
        </form>

        <p className="auth-switch">
          {isRegister ? 'Already have an account?' : 'New to Application Atlas?'}{' '}
          <Link to={isRegister ? '/login' : '/register'}>
            {isRegister ? 'Sign in' : 'Create an account'}
          </Link>
        </p>
      </section>
      <p className="auth-footnote">Your account and application data are private to you.</p>
    </main>
  )
}

export default AuthPage
