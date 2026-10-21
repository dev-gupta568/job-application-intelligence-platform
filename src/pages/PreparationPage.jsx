import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'
import { ApiError } from '../services/apiClient.js'
import { listApplications } from '../services/applicationService.js'
import {
  analyzeApplicationSkills,
  listSkillMatches,
} from '../services/skillMatchingService.js'

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value))
}

function SkillList({ skills, emptyMessage }) {
  if (skills.length === 0) {
    return <p className="intelligence-empty">{emptyMessage}</p>
  }
  return (
    <ul className="skill-chip-list">
      {skills.map((skill) => <li key={skill}>{skill}</li>)}
    </ul>
  )
}

function AnalysisDetails({ analysis }) {
  return (
    <section className="analysis-result" aria-labelledby="analysis-result-title">
      <div className="analysis-score-heading">
        <div>
          <p className="eyebrow">RULE-BASED SKILL CHECK</p>
          <h2 id="analysis-result-title">{analysis.company_name} · {analysis.job_title}</h2>
        </div>
        <strong className="match-score">{Number(analysis.match_percentage).toFixed(2)}%</strong>
      </div>
      <p className="analysis-formula">
        {analysis.matching_skills.length} matching skills ÷ {analysis.job_keywords.length} recognized job requirements.
      </p>
      <div className="analysis-columns">
        <article className="analysis-section">
          <h3>Matching skills</h3>
          <SkillList skills={analysis.matching_skills} emptyMessage="No matching skills were found." />
        </article>
        <article className="analysis-section">
          <h3>Missing skills</h3>
          <SkillList skills={analysis.missing_skills} emptyMessage="All recognized requirements match your skill list." />
        </article>
        <article className="analysis-section">
          <h3>Important keywords</h3>
          <SkillList skills={analysis.important_keywords} emptyMessage="No emphasized keywords were identified." />
        </article>
      </div>
      <div className="analysis-columns analysis-advice">
        <article className="analysis-section">
          <h3>Skills to consider learning</h3>
          <SkillList skills={analysis.suggested_skills_to_learn} emptyMessage="No recognized gaps to prioritize." />
          <p className="intelligence-help">
            Suggestions are based on missing recognized terms, not a prediction about hiring.
          </p>
        </article>
        <article className="analysis-section">
          <h3>Resume tailoring checklist</h3>
          <ul className="resume-checklist">
            {analysis.resume_checklist.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </article>
      </div>
      <p className="algorithm-caption">
        {analysis.algorithm_version} · Important keywords are requirements listed in the application or terms
        repeated in the job description. The description itself is not retained in analysis history.
      </p>
    </section>
  )
}

function PreparationPage() {
  const { accessToken, logout } = useAuth()
  const navigate = useNavigate()
  const [applications, setApplications] = useState([])
  const [history, setHistory] = useState([])
  const [selectedApplicationId, setSelectedApplicationId] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [skillsInput, setSkillsInput] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [selectedComparisonIds, setSelectedComparisonIds] = useState([])
  const hasInitializedSelection = useRef(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState('')

  const handleRequestError = useCallback((requestError) => {
    if (requestError instanceof ApiError && requestError.status === 401) {
      logout()
      navigate('/login', { replace: true, state: { from: '/preparation' } })
      return
    }
    setError(requestError instanceof Error ? requestError.message : 'The request failed.')
  }, [logout, navigate])

  const loadData = useCallback(async (signal) => {
    setIsLoading(true)
    setError('')
    try {
      const [applicationPage, comparisons] = await Promise.all([
        listApplications(accessToken, {}, signal),
        listSkillMatches(accessToken, signal),
      ])
      setApplications(applicationPage.items)
      setHistory(comparisons)
      if (!hasInitializedSelection.current && applicationPage.items.length > 0) {
        hasInitializedSelection.current = true
        setSelectedApplicationId(applicationPage.items[0].id)
        setJobDescription(applicationPage.items[0].job_description || '')
      }
    } catch (requestError) {
      if (!signal?.aborted) {
        handleRequestError(requestError)
      }
    } finally {
      if (!signal?.aborted) {
        setIsLoading(false)
      }
    }
  }, [accessToken, handleRequestError])

  useEffect(() => {
    const controller = new AbortController()
    queueMicrotask(() => {
      if (!controller.signal.aborted) {
        loadData(controller.signal)
      }
    })
    return () => controller.abort()
  }, [loadData])

  function selectApplication(event) {
    const applicationId = event.target.value
    setSelectedApplicationId(applicationId)
    const application = applications.find((item) => item.id === applicationId)
    setJobDescription(application?.job_description || '')
    setAnalysis(null)
  }

  async function runAnalysis(event) {
    event.preventDefault()
    const application = applications.find((item) => item.id === selectedApplicationId)
    if (!application) {
      setError('Add an application before analyzing a job description.')
      return
    }
    const userSkills = skillsInput
      .split(/[,\n]/)
      .map((skill) => skill.trim())
      .filter(Boolean)

    setIsAnalyzing(true)
    setError('')
    try {
      const result = await analyzeApplicationSkills(accessToken, application.id, {
        job_description: jobDescription.trim() || null,
        user_skills: userSkills,
      })
      setAnalysis(result)
      setHistory((current) => [result, ...current.filter((item) => item.id !== result.id)])
    } catch (requestError) {
      handleRequestError(requestError)
    } finally {
      setIsAnalyzing(false)
    }
  }

  function toggleComparison(id) {
    setSelectedComparisonIds((current) => (
      current.includes(id)
        ? current.filter((selectedId) => selectedId !== id)
        : current.length < 4
          ? [...current, id]
          : current
    ))
  }

  const selectedComparisons = history.filter((item) => selectedComparisonIds.includes(item.id))
  const selectedApplication = applications.find((item) => item.id === selectedApplicationId)

  return (
    <div className="dashboard-page intelligence-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">ROLE-READY PREPARATION</p>
          <h1>Job skill analysis</h1>
          <p className="page-subtitle">
            See how the skills you enter line up with recognized requirements in a saved role.
          </p>
        </div>
      </div>

      <p className="intelligence-disclosure">
        This is a transparent, rule-based keyword comparison—not AI, an ATS score, or a hiring prediction.
        It recognizes common technology and workplace terms, plus custom terms included in your skills or
        the application&apos;s required-skills list. Unrecognized phrases in a posting are not included in the score.
      </p>

      {error && <p className="inline-error" role="alert">{error}</p>}

      <div className="intelligence-layout">
        <form className="intelligence-form" onSubmit={runAnalysis}>
          <p className="eyebrow">COMPARE A ROLE</p>
          <h2>Job description</h2>
          <label>
            Saved application
            <select
              disabled={applications.length === 0}
              onChange={selectApplication}
              value={selectedApplicationId}
            >
              {applications.length === 0
                ? <option value="">Add an application first</option>
                : applications.map((application) => (
                  <option key={application.id} value={application.id}>
                    {application.company_name} — {application.job_title}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Job description
            <textarea
              maxLength={30000}
              onChange={(event) => setJobDescription(event.target.value)}
              placeholder="Paste the role description, or add required skills to the application."
              rows="9"
              value={jobDescription}
            />
          </label>
          <label>
            Your skills
            <textarea
              onChange={(event) => setSkillsInput(event.target.value)}
              placeholder="Python, React, PostgreSQL"
              required
              rows="3"
              value={skillsInput}
            />
            <span className="field-hint">Separate skills with commas or new lines.</span>
          </label>
          <p className="intelligence-help">
            {selectedApplication?.required_skills?.length
              ? `This application also lists: ${selectedApplication.required_skills.join(', ')}`
              : 'Add required skills to the application to include custom job terms.'}
          </p>
          <button
            className="primary-button"
            disabled={isAnalyzing || isLoading || applications.length === 0}
            type="submit"
          >
            {isAnalyzing ? 'Analyzing…' : 'Analyze skill match'}
          </button>
        </form>

        <div className="intelligence-results">
          {analysis ? (
            <AnalysisDetails analysis={analysis} />
          ) : (
            <section className="dashboard-empty intelligence-placeholder">
              <span className="empty-mark" aria-hidden="true">A</span>
              <p className="eyebrow">Transparent analysis</p>
              <h2>Your match breakdown will appear here.</h2>
              <p>
                Choose an application, enter your skills and a job description, then run the comparison.
              </p>
            </section>
          )}
        </div>
      </div>

      <section className="comparison-history" aria-labelledby="comparison-history-title">
        <div className="list-heading">
          <div>
            <p className="eyebrow">OPPORTUNITY COMPARISON</p>
            <h2 id="comparison-history-title">Saved skill analyses</h2>
          </div>
          <span>{history.length} saved</span>
        </div>
        <p className="intelligence-help">
          Select up to four saved opportunities to compare their scores and skill gaps side by side.
          Each analysis saves the skill list you supplied; use the same list for a fair comparison.
        </p>
        {isLoading ? (
          <p className="list-state" role="status">Loading saved analyses…</p>
        ) : history.length === 0 ? (
          <p className="list-state">Your saved comparisons will appear here after an analysis.</p>
        ) : (
          <div className="comparison-history-list">
            {history.map((item) => (
              <label className="comparison-history-item" key={item.id}>
                <input
                  checked={selectedComparisonIds.includes(item.id)}
                  disabled={!selectedComparisonIds.includes(item.id) && selectedComparisonIds.length >= 4}
                  onChange={() => toggleComparison(item.id)}
                  type="checkbox"
                />
                <span>
                  <strong>{item.company_name} · {item.job_title}</strong>
                  <small>{formatDate(item.created_at)} · {item.matching_skills.length}/{item.job_keywords.length} matched</small>
                </span>
                <b>{Number(item.match_percentage).toFixed(2)}%</b>
              </label>
            ))}
          </div>
        )}
        {selectedComparisons.length > 1 && (
          <div className="comparison-table-wrap">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th scope="col">Opportunity</th>
                  <th scope="col">Match</th>
                  <th scope="col">Matching skills</th>
                  <th scope="col">Skill gaps</th>
                </tr>
              </thead>
              <tbody>
                {selectedComparisons.map((item) => (
                  <tr key={item.id}>
                    <th scope="row">{item.company_name} · {item.job_title}</th>
                    <td>{Number(item.match_percentage).toFixed(2)}%</td>
                    <td>{item.matching_skills.join(', ') || 'None detected'}</td>
                    <td>{item.missing_skills.join(', ') || 'None detected'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

export default PreparationPage
