import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'
import { ApiError } from '../services/apiClient.js'
import { listApplications } from '../services/applicationService.js'
import {
  createFollowUp,
  createInterview,
  listFollowUps,
  listInterviews,
  updateFollowUp,
  updateInterview,
} from '../services/trackingService.js'

function formatDateTime(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function toIsoDateTime(value) {
  return new Date(value).toISOString()
}

function toLocalDateTimeInput(value) {
  const date = new Date(value)
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  return date.toISOString().slice(0, 16)
}

function InterviewsPage() {
  const { accessToken, logout } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('interviews')
  const [applications, setApplications] = useState([])
  const [interviews, setInterviews] = useState([])
  const [followUps, setFollowUps] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const handleRequestError = useCallback((requestError) => {
    if (requestError instanceof ApiError && requestError.status === 401) {
      logout()
      navigate('/login', { replace: true, state: { from: '/interviews' } })
      return
    }
    setError(requestError instanceof Error ? requestError.message : 'The request failed.')
  }, [logout, navigate])

  const loadTrackingData = useCallback(async (signal) => {
    setIsLoading(true)
    setError('')
    try {
      const [applicationsResult, interviewsResult, followUpsResult] = await Promise.all([
        listApplications(accessToken, {}, signal),
        listInterviews(accessToken, signal),
        listFollowUps(accessToken, signal),
      ])
      setApplications(applicationsResult.items)
      setInterviews(interviewsResult)
      setFollowUps(followUpsResult)
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
        loadTrackingData(controller.signal)
      }
    })
    return () => controller.abort()
  }, [loadTrackingData])

  async function saveInterview(event) {
    event.preventDefault()
    const form = event.currentTarget
    const formData = new FormData(form)
    const payload = {
      round_name: formData.get('round_name').toString().trim(),
      scheduled_at: toIsoDateTime(formData.get('scheduled_at').toString()),
      preparation_notes: formData.get('preparation_notes').toString().trim() || null,
    }
    const meetingUrl = formData.get('meeting_url').toString().trim()
    if (meetingUrl) {
      payload.meeting_url = meetingUrl
    }

    setIsSaving(true)
    setError('')
    setNotice('')
    try {
      await createInterview(
        accessToken,
        formData.get('application_id').toString(),
        payload,
      )
      form.reset()
      setNotice('Interview scheduled.')
      await loadTrackingData()
    } catch (requestError) {
      handleRequestError(requestError)
    } finally {
      setIsSaving(false)
    }
  }

  async function saveFollowUp(event) {
    event.preventDefault()
    const form = event.currentTarget
    const formData = new FormData(form)
    const payload = {
      title: formData.get('title').toString().trim(),
      due_at: toIsoDateTime(formData.get('due_at').toString()),
      notes: formData.get('notes').toString().trim() || null,
    }

    setIsSaving(true)
    setError('')
    setNotice('')
    try {
      await createFollowUp(
        accessToken,
        formData.get('application_id').toString(),
        payload,
      )
      form.reset()
      setNotice('Follow-up reminder saved.')
      await loadTrackingData()
    } catch (requestError) {
      handleRequestError(requestError)
    } finally {
      setIsSaving(false)
    }
  }

  async function saveInterviewUpdates(event, interview) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const scheduledAt = formData.get('scheduled_at').toString()
    const meetingUrl = formData.get('meeting_url').toString().trim()
    const payload = {
      round_name: formData.get('round_name').toString().trim(),
      scheduled_at: toIsoDateTime(scheduledAt),
      meeting_url: meetingUrl || null,
      preparation_notes: formData.get('preparation_notes').toString().trim() || null,
      feedback: formData.get('feedback').toString().trim() || null,
      status: formData.get('status').toString(),
    }
    setIsSaving(true)
    setError('')
    try {
      await updateInterview(accessToken, interview.id, payload)
      setNotice('Interview details updated.')
      await loadTrackingData()
    } catch (requestError) {
      handleRequestError(requestError)
    } finally {
      setIsSaving(false)
    }
  }

  async function saveFollowUpUpdates(event, followUp) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const payload = {
      title: formData.get('title').toString().trim(),
      due_at: toIsoDateTime(formData.get('due_at').toString()),
      notes: formData.get('notes').toString().trim() || null,
    }
    setIsSaving(true)
    setError('')
    try {
      await updateFollowUp(accessToken, followUp.id, payload)
      setNotice('Follow-up reminder updated.')
      await loadTrackingData()
    } catch (requestError) {
      handleRequestError(requestError)
    } finally {
      setIsSaving(false)
    }
  }

  async function completeFollowUp(followUp) {
    setError('')
    try {
      await updateFollowUp(accessToken, followUp.id, { completed: true })
      setNotice('Follow-up marked complete.')
      await loadTrackingData()
    } catch (requestError) {
      handleRequestError(requestError)
    }
  }

  const applicationOptions = applications.map((application) => (
    <option key={application.id} value={application.id}>
      {application.company_name} — {application.job_title}
    </option>
  ))

  return (
    <div className="dashboard-page tracking-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">INTERVIEW PLANNING</p>
          <h1>Interviews & follow-ups</h1>
          <p className="page-subtitle">
            Schedule conversations, keep preparation notes close, and remember each next step.
          </p>
        </div>
      </div>

      {notice && <p className="inline-notice" role="status">{notice}</p>}
      {error && <p className="inline-error" role="alert">{error}</p>}

      <div className="tracking-tabs" role="tablist" aria-label="Tracking sections">
        <button
          aria-selected={activeTab === 'interviews'}
          aria-controls="interviews-panel"
          className={activeTab === 'interviews' ? 'tracking-tab is-active' : 'tracking-tab'}
          id="interviews-tab"
          onClick={() => setActiveTab('interviews')}
          role="tab"
          type="button"
        >
          Interviews <span>{interviews.length}</span>
        </button>
        <button
          aria-selected={activeTab === 'follow-ups'}
          aria-controls="follow-ups-panel"
          className={activeTab === 'follow-ups' ? 'tracking-tab is-active' : 'tracking-tab'}
          id="follow-ups-tab"
          onClick={() => setActiveTab('follow-ups')}
          role="tab"
          type="button"
        >
          Follow-ups <span>{followUps.filter((item) => !item.completed_at).length}</span>
        </button>
      </div>

      {activeTab === 'interviews' ? (
        <section
          aria-labelledby="interviews-tab"
          className="tracking-layout"
          id="interviews-panel"
          role="tabpanel"
        >
          <form className="tracking-form" onSubmit={saveInterview}>
            <p className="eyebrow">SCHEDULE A ROUND</p>
            <h2>New interview</h2>
            <label>
              Application
              <select disabled={applications.length === 0} name="application_id" required>
                {applications.length === 0
                  ? <option value="">Add an application first</option>
                  : applicationOptions}
              </select>
            </label>
            <label>
              Interview round
              <input maxLength={120} name="round_name" placeholder="Technical interview" required />
            </label>
            <label>
              Date and time
              <input min={new Date().toISOString().slice(0, 16)} name="scheduled_at" required type="datetime-local" />
            </label>
            <label>
              Meeting link
              <input maxLength={2048} name="meeting_url" placeholder="https://…" type="url" />
            </label>
            <label>
              Preparation notes
              <textarea name="preparation_notes" rows="3" />
            </label>
            <button className="primary-button" disabled={isSaving || applications.length === 0} type="submit">
              {isSaving ? 'Saving…' : 'Schedule interview'}
            </button>
          </form>

          <section className="tracking-list" aria-labelledby="interview-list-title">
            <div className="list-heading">
              <h2 id="interview-list-title">Your interview rounds</h2>
              <span>{interviews.length} total</span>
            </div>
            {isLoading ? (
              <p className="list-state" role="status">Loading interviews…</p>
            ) : interviews.length === 0 ? (
              <div className="list-state">
                <h3>No interviews scheduled</h3>
                <p>Schedule a round when an employer invites you to speak.</p>
              </div>
            ) : (
              <div className="tracking-cards">
                {interviews.map((interview) => (
                  <article className="tracking-card" key={interview.id}>
                    <div className="tracking-card-heading">
                      <div>
                        <p className="eyebrow">{interview.company_name}</p>
                        <h3>{interview.round_name}</h3>
                        <p>{interview.job_title}</p>
                      </div>
                      <span className={`tracking-status status-${interview.status.toLowerCase()}`}>
                        {interview.status}
                      </span>
                    </div>
                    <p className="tracking-date">{formatDateTime(interview.scheduled_at)}</p>
                    {interview.meeting_url && (
                      <a href={interview.meeting_url} rel="noreferrer" target="_blank">
                        Open meeting link
                      </a>
                    )}
                    {interview.preparation_notes && (
                      <p className="tracking-notes">{interview.preparation_notes}</p>
                    )}
                    {interview.feedback && (
                      <p className="tracking-notes"><strong>Feedback:</strong> {interview.feedback}</p>
                    )}
                    <details className="tracking-edit">
                      <summary>Edit notes or record feedback</summary>
                      <form onSubmit={(event) => saveInterviewUpdates(event, interview)}>
                        <label>
                          Round
                          <input defaultValue={interview.round_name} maxLength={120} name="round_name" required />
                        </label>
                        <label>
                          Date and time
                          <input
                            defaultValue={toLocalDateTimeInput(interview.scheduled_at)}
                            name="scheduled_at"
                            required
                            type="datetime-local"
                          />
                        </label>
                        <label>
                          Meeting link
                          <input defaultValue={interview.meeting_url || ''} maxLength={2048} name="meeting_url" type="url" />
                        </label>
                        <label>
                          Preparation notes
                          <textarea defaultValue={interview.preparation_notes || ''} name="preparation_notes" rows="2" />
                        </label>
                        <label>
                          Feedback
                          <textarea defaultValue={interview.feedback || ''} name="feedback" rows="2" />
                        </label>
                        <label>
                          Status
                          <select defaultValue={interview.status} name="status">
                            <option>Scheduled</option>
                            <option>Completed</option>
                            <option>Cancelled</option>
                          </select>
                        </label>
                        <button className="secondary-button" disabled={isSaving} type="submit">Save interview</button>
                      </form>
                    </details>
                  </article>
                ))}
              </div>
            )}
          </section>
        </section>
      ) : (
        <section
          aria-labelledby="follow-ups-tab"
          className="tracking-layout"
          id="follow-ups-panel"
          role="tabpanel"
        >
          <form className="tracking-form" onSubmit={saveFollowUp}>
            <p className="eyebrow">REMEMBER THE NEXT STEP</p>
            <h2>New follow-up</h2>
            <label>
              Application
              <select disabled={applications.length === 0} name="application_id" required>
                {applications.length === 0
                  ? <option value="">Add an application first</option>
                  : applicationOptions}
              </select>
            </label>
            <label>
              Reminder
              <input maxLength={200} name="title" placeholder="Email the recruiter" required />
            </label>
            <label>
              Due date and time
              <input name="due_at" required type="datetime-local" />
            </label>
            <label>
              Notes
              <textarea name="notes" rows="3" />
            </label>
            <button className="primary-button" disabled={isSaving || applications.length === 0} type="submit">
              {isSaving ? 'Saving…' : 'Save reminder'}
            </button>
          </form>

          <section className="tracking-list" aria-labelledby="follow-up-list-title">
            <div className="list-heading">
              <h2 id="follow-up-list-title">Your reminders</h2>
              <span>{followUps.length} total</span>
            </div>
            {isLoading ? (
              <p className="list-state" role="status">Loading reminders…</p>
            ) : followUps.length === 0 ? (
              <div className="list-state">
                <h3>No follow-ups yet</h3>
                <p>Add a reminder for a recruiter message or your next application task.</p>
              </div>
            ) : (
              <div className="tracking-cards">
                {followUps.map((followUp) => {
                  const overdue = !followUp.completed_at && new Date(followUp.due_at) < new Date()
                  return (
                    <article
                      className={`tracking-card${followUp.completed_at ? ' is-complete' : ''}`}
                      key={followUp.id}
                    >
                      <div className="tracking-card-heading">
                        <div>
                          <p className="eyebrow">{followUp.company_name}</p>
                          <h3>{followUp.title}</h3>
                          <p>{followUp.job_title}</p>
                        </div>
                        <span className={`tracking-status${overdue ? ' is-overdue' : ''}`}>
                          {followUp.completed_at ? 'Completed' : overdue ? 'Overdue' : 'Open'}
                        </span>
                      </div>
                      <p className="tracking-date">{formatDateTime(followUp.due_at)}</p>
                      {followUp.notes && <p className="tracking-notes">{followUp.notes}</p>}
                      {!followUp.completed_at && (
                        <div className="tracking-card-actions">
                          <button className="text-button" onClick={() => completeFollowUp(followUp)} type="button">
                            Mark complete
                          </button>
                        </div>
                      )}
                      <details className="tracking-edit">
                        <summary>Edit reminder</summary>
                        <form onSubmit={(event) => saveFollowUpUpdates(event, followUp)}>
                          <label>
                            Reminder
                            <input defaultValue={followUp.title} maxLength={200} name="title" required />
                          </label>
                          <label>
                            Due date and time
                            <input
                              defaultValue={toLocalDateTimeInput(followUp.due_at)}
                              name="due_at"
                              required
                              type="datetime-local"
                            />
                          </label>
                          <label>
                            Notes
                            <textarea defaultValue={followUp.notes || ''} name="notes" rows="2" />
                          </label>
                          <button className="secondary-button" disabled={isSaving} type="submit">Save reminder</button>
                        </form>
                      </details>
                    </article>
                  )
                })}
              </div>
            )}
          </section>
        </section>
      )}
    </div>
  )
}

export default InterviewsPage
