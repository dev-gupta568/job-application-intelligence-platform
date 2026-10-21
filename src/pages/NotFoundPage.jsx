import { Link } from 'react-router-dom'

function NotFoundPage() {
  return (
    <main className="not-found-page">
      <p className="eyebrow">404 — PAGE NOT FOUND</p>
      <h1>This page isn’t in your workspace.</h1>
      <Link className="not-found-link" to="/">Return to the home page</Link>
    </main>
  )
}

export default NotFoundPage
