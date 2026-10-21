const sectionDetails = {
  Applications: {
    eyebrow: 'OPPORTUNITY TRACKING',
    description: 'Save roles, track status changes, and keep follow-ups close.',
  },
  Interviews: {
    eyebrow: 'INTERVIEW PLANNING',
    description: 'Keep interview dates, rounds, links, and notes together.',
  },
  Reports: {
    eyebrow: 'PROGRESS & PATTERNS',
    description: 'Review conversion rates and trends calculated from your records.',
  },
  Preparation: {
    eyebrow: 'ROLE-READY PREPARATION',
    description: 'Organize resume versions, skill comparisons, and preparation notes.',
  },
}

function WorkspacePage({ section }) {
  const details = sectionDetails[section]

  return (
    <div className="dashboard-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">{details.eyebrow}</p>
          <h1>{section}</h1>
          <p className="page-subtitle">{details.description}</p>
        </div>
      </div>
      <section className="dashboard-empty workspace-empty" aria-labelledby="workspace-empty-title">
        <span className="empty-mark" aria-hidden="true">A</span>
        <p className="eyebrow">Workspace section</p>
        <h2 id="workspace-empty-title">{section} will use your saved data.</h2>
        <p>
          This page structure is ready. We will connect it to the authenticated
          API before displaying or changing any records.
        </p>
      </section>
    </div>
  )
}

export default WorkspacePage
