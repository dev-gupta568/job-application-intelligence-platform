import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'

const navigation = [
  { label: 'Overview', to: '/dashboard' },
  { label: 'Applications', to: '/applications' },
  { label: 'Interviews', to: '/interviews' },
  { label: 'Reports', to: '/reports' },
  { label: 'Preparation', to: '/preparation' },
]

function AppLayout({ children }) {
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="workspace">
      <aside className="sidebar" aria-label="Main navigation">
        <Link className="workspace-brand" to="/" aria-label="Application Atlas home">
          <span className="workspace-brand-mark" aria-hidden="true">A</span>
          <span>Application Atlas</span>
        </Link>

        <p className="sidebar-label">WORKSPACE</p>
        <nav className="sidebar-nav">
          {navigation.map((item) => (
            <NavLink
              className={({ isActive }) => `nav-link${isActive ? ' is-active' : ''}`}
              key={item.to}
              to={item.to}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="sidebar-avatar" aria-hidden="true">
            {user?.display_name?.trim().charAt(0).toUpperCase() || 'A'}
          </span>
          <span className="sidebar-account">
            <strong>{user?.display_name || 'Account'}</strong>
            <span>{user?.email || 'Account settings later'}</span>
          </span>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="workspace-topbar">
          <span className="breadcrumb">Personal workspace</span>
          <div className="topbar-actions">
            <span className="topbar-note">A focused space for your next move</span>
            <button className="logout-button" onClick={handleLogout} type="button">
              Sign out
            </button>
          </div>
        </header>
        <main className="workspace-content">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  )
}

export default AppLayout
