import '../styles/app.css'
import { Link } from 'react-router-dom'

const plannedAreas = [
  {
    number: '01',
    title: 'Applications',
    description: 'Keep each opportunity and its next step in one place.',
  },
  {
    number: '02',
    title: 'Preparation',
    description: 'Connect interviews, notes, and resume versions to a role.',
  },
  {
    number: '03',
    title: 'Insights',
    description: 'Understand your progress with metrics based on saved data.',
  },
]

function ProjectHomePage() {
  return (
    <main className="setup-page">
      <header className="topbar">
        <Link className="brand" to="/" aria-label="Application Atlas home">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>Application Atlas</span>
        </Link>
        <div className="home-actions">
          <Link className="home-login" to="/login">Sign in</Link>
          <Link className="home-register" to="/register">Create account</Link>
        </div>
        <span className="phase-label">
          <span className="phase-dot" aria-hidden="true" />
          Project setup
        </span>
      </header>

      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">A calmer way to navigate your job search</p>
        <h1 id="page-title">
          Make your next
          <br />
          <span>move with clarity.</span>
        </h1>
        <p className="hero-copy">
          One thoughtful workspace for the opportunities you pursue, the
          conversations you have, and the progress you make.
        </p>
        <div className="setup-note" role="status">
          <span className="note-icon" aria-hidden="true">i</span>
          <p>
            Sign in to a private workspace for your applications, interviews,
            and next steps.
          </p>
        </div>
      </section>

      <section className="roadmap" aria-labelledby="roadmap-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Built for the whole process</p>
            <h2 id="roadmap-title">Your search, in perspective.</h2>
          </div>
          <span className="roadmap-count">03 focus areas</span>
        </div>

        <div className="roadmap-grid">
          {plannedAreas.map((area) => (
            <article className="roadmap-card" key={area.number}>
              <span className="card-number">{area.number}</span>
              <h3>{area.title}</h3>
              <p>{area.description}</p>
              <span className="card-arrow" aria-hidden="true">↗</span>
            </article>
          ))}
        </div>
      </section>

      <footer className="page-footer">
        <span>Application Atlas</span>
        <span>Built one useful step at a time.</span>
      </footer>
    </main>
  )
}

export default ProjectHomePage
