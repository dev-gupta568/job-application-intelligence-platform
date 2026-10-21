import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'
import { ApiError } from '../services/apiClient.js'
import {
  createApplicationActivity,
  listApplicationActivities,
} from '../services/trackingService.js'

function formatDateTime(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function activityTitle(activity) {
  if (activity.event_type === 'status_changed') {
    return `Status changed from ${activity.previous_status} to ${activity.new_status}`
  }
  if (activity.event_type === 'application_created') {
    return 'Application added'
  }
  return activity.details || activity.event_type.replaceAll('_', ' ')
}

function ApplicationTimeline({ application }) {
  const { accessToken, logout } = useAuth()
  const navigate = useNavigate()
  const [activities, setActivities] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [reloadCount, setReloadCount] = useState(0)

  const loadActivities = useCallback(async (signal) => {
    setIsLoading(true)
    setError('')
    try {
      const result = await listApplicationActivities(accessToken, application.id, signal)
      setActivities(result)
    } catch (requestError) {
      if (!signal?.aborted) {
        if (requestError instanceof ApiError && requestError.status === 401) {
          logout()
          navigate('/login', { replace: true, state: { from: '/applications' } })
        } else {
          setError(requestError instanceof Error ? requestError.message : 'Could not load activity.')
        }
      }
    } finally {
      if (!signal?.aborted) {
        setIsLoading(false)
      }
    }
  }, [accessToken, application.id, logout, navigate])

  useEffect(() => {
    const controller = new AbortController()
    queueMicrotask(() => {
      if (!controller.signal.aborted) {
        loadActivities(controller.signal)
      }
    })
    return () => controller.abort()
  }, [loadActivities, reloadCount])

  async function addActivity(event) {
    event.preventDefault()
    const form = event.currentTarget
    const formData = new FormData(form)
    const activity = {
      event_type: formData.get('event_type').toString(),
      details: formData.get('details').toString().trim(),
    }
    setIsSaving(true)
    setError('')
    try {
      await createApplicationActivity(accessToken, application.id, activity)
      form.reset()
      setReloadCount((count) => count + 1)
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 401) {
        logout()
        navigate('/login', { replace: true, state: { from: '/applications' } })
      } else {
        setError(requestError instanceof Error ? requestError.message : 'Could not add activity.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="application-timeline" aria-labelledby="timeline-title">
      <div className="list-heading">
        <div>
          <p className="eyebrow">APPLICATION HISTORY</p>
          <h2 id="timeline-title">{application.company_name} · {application.job_title}</h2>
        </div>
      </div>
      {error && <p className="inline-error" role="alert">{error}</p>}
      <form className="timeline-form" onSubmit={addActivity}>
        <label>
          Activity type
          <select name="event_type">
            <option value="recruiter_communication">Recruiter communication</option>
            <option value="note_added">Preparation note</option>
          </select>
        </label>
        <label>
          What happened?
          <textarea maxLength={5000} name="details" required rows="2" />
        </label>
        <button className="primary-button" disabled={isSaving} type="submit">
          {isSaving ? 'Saving…' : 'Add to timeline'}
        </button>
      </form>
      {isLoading ? (
        <p className="list-state" role="status">Loading application history…</p>
      ) : activities.length === 0 ? (
        <p className="list-state">No activity recorded yet.</p>
      ) : (
        <ol className="timeline-list">
          {activities.map((activity) => (
            <li key={activity.id}>
              <span className="timeline-dot" aria-hidden="true" />
              <div>
                <strong>{activityTitle(activity)}</strong>
                <time dateTime={activity.occurred_at}>{formatDateTime(activity.occurred_at)}</time>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

export default ApplicationTimeline
