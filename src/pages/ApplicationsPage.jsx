import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ApplicationTimeline from '../components/ApplicationTimeline.jsx'
import { useAuth } from '../hooks/useAuth.js'
import { ApiError } from '../services/apiClient.js'
import {
  createApplication,
  deleteApplication,
  listApplications,
  updateApplication,
} from '../services/applicationService.js'

const STATUSES = [
  'Interested',
  'Applied',
  'Assessment',
  'Interview',
  'Offer',
  'Rejected',
  'Withdrawn',
]

const EMPTY_FILTERS = {
  search: '',
  status: '',
  sort_by: 'applied_on',
  sort_order: 'desc',
}

function statusClass(status) {
  return `status-badge status-${status.toLowerCase()}`
}

function ApplicationsPage() {
  const { accessToken, logout } = useAuth()
  const navigate = useNavigate()
  const [applications, setApplications] = useState([])
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [filterDraft, setFilterDraft] = useState(EMPTY_FILTERS)
  const [editingApplication, setEditingApplication] = useState(null)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [timelineApplication, setTimelineApplication] = useState(null)

  const handleRequestError = useCallback((requestError) => {
    if (requestError instanceof ApiError && requestError.status === 401) {
      logout()
      navigate('/login', { replace: true, state: { from: '/applications' } })
      return
    }
    setError(
      requestError instanceof Error
        ? requestError.message
        : 'The request failed. Please try again.',
    )
  }, [logout, navigate])

  const loadApplications = useCallback(async (signal) => {
    setIsLoading(true)
    setError('')
    try {
      const result = await listApplications(accessToken, filters, signal)
      setApplications(result.items)
    } catch (requestError) {
      if (!signal?.aborted) {
        handleRequestError(requestError)
      }
    } finally {
      if (!signal?.aborted) {
        setIsLoading(false)
      }
    }
  }, [accessToken, filters, handleRequestError])

  useEffect(() => {
    const controller = new AbortController()
    queueMicrotask(() => {
      if (!controller.signal.aborted) {
        loadApplications(controller.signal)
      }
    })
    return () => controller.abort()
  }, [loadApplications])

  function applyFilters(event) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const nextFilters = {
      search: formData.get('search').toString().trim(),
      status: formData.get('status').toString(),
      sort_by: formData.get('sort_by').toString(),
      sort_order: formData.get('sort_order').toString(),
    }
    setFilterDraft(nextFilters)
    setFilters(nextFilters)
  }

  function openCreateForm() {
    setEditingApplication(null)
    setIsFormOpen(true)
    setError('')
    setNotice('')
  }

  function openEditForm(application) {
    setEditingApplication(application)
    setIsFormOpen(true)
    setError('')
    setNotice('')
  }

  async function saveApplication(event) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const skills = formData.get('required_skills').toString()
      .split(',')
      .map((skill) => skill.trim())
      .filter(Boolean)
    const payload = {
      company_name: formData.get('company_name').toString().trim(),
      job_title: formData.get('job_title').toString().trim(),
      status: formData.get('status').toString(),
      required_skills: skills,
    }
    const optionalFields = [
      'location',
      'work_mode',
      'employment_type',
      'job_posting_url',
      'job_description',
      'applied_on',
      'deadline',
      'notes',
    ]
    for (const field of optionalFields) {
      const value = formData.get(field).toString().trim()
      if (value) {
        payload[field] = value
      } else if (editingApplication) {
        payload[field] = null
      }
    }

    setIsSaving(true)
    setError('')
    setNotice('')
    try {
      if (editingApplication) {
        await updateApplication(accessToken, editingApplication.id, payload)
        setNotice('Application updated.')
      } else {
        await createApplication(accessToken, payload)
        setNotice('Application saved.')
      }
      setIsFormOpen(false)
      setEditingApplication(null)
      await loadApplications()
    } catch (requestError) {
      handleRequestError(requestError)
    } finally {
      setIsSaving(false)
    }
  }

  async function removeApplication(application) {
    const confirmed = window.confirm(
      `Delete the ${application.job_title} application at ${application.company_name}?`,
    )
    if (!confirmed) {
      return
    }

    setError('')
    setNotice('')
    try {
      await deleteApplication(accessToken, application.id)
      setNotice('Application deleted.')
      await loadApplications()
    } catch (requestError) {
      handleRequestError(requestError)
    }
  }

  return (
    <div className="dashboard-page applications-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">OPPORTUNITY TRACKING</p>
          <h1>Applications</h1>
          <p className="page-subtitle">
            Keep every opportunity and its next step in one place.
          </p>
        </div>
        <button className="primary-button" onClick={openCreateForm} type="button">
          Add application
        </button>
      </div>

      {notice && <p className="inline-notice" role="status">{notice}</p>}
      {error && <p className="inline-error" role="alert">{error}</p>}

      {isFormOpen && (
        <section className="application-editor" aria-labelledby="application-form-title">
          <div className="editor-heading">
            <div>
              <p className="eyebrow">{editingApplication ? 'EDIT RECORD' : 'NEW OPPORTUNITY'}</p>
              <h2 id="application-form-title">
                {editingApplication ? 'Update application' : 'Add an application'}
              </h2>
            </div>
            <button
              className="text-button"
              onClick={() => {
                setIsFormOpen(false)
                setEditingApplication(null)
              }}
              type="button"
            >
              Cancel
            </button>
          </div>
          <form
            className="application-form"
            key={editingApplication?.id || 'new'}
            onSubmit={saveApplication}
          >
            <label>
              Company name
              <input
                defaultValue={editingApplication?.company_name || ''}
                maxLength={200}
                name="company_name"
                required
              />
            </label>
            <label>
              Job title
              <input
                defaultValue={editingApplication?.job_title || ''}
                maxLength={200}
                name="job_title"
                required
              />
            </label>
            <label>
              Status
              <select defaultValue={editingApplication?.status || 'Interested'} name="status">
                {STATUSES.map((status) => <option key={status}>{status}</option>)}
              </select>
            </label>
            <label>
              Location
              <input defaultValue={editingApplication?.location || ''} maxLength={200} name="location" />
            </label>
            <label>
              Work mode
              <select defaultValue={editingApplication?.work_mode || ''} name="work_mode">
                <option value="">Not specified</option>
                <option>Remote</option>
                <option>Hybrid</option>
                <option>On-site</option>
              </select>
            </label>
            <label>
              Employment type
              <select defaultValue={editingApplication?.employment_type || ''} name="employment_type">
                <option value="">Not specified</option>
                <option>Full-time</option>
                <option>Part-time</option>
                <option>Contract</option>
                <option>Internship</option>
                <option>Temporary</option>
                <option>Volunteer</option>
                <option>Freelance</option>
              </select>
            </label>
            <label>
              Applied on
              <input defaultValue={editingApplication?.applied_on || ''} name="applied_on" type="date" />
            </label>
            <label>
              Application deadline
              <input defaultValue={editingApplication?.deadline || ''} name="deadline" type="date" />
            </label>
            <label className="form-field-wide">
              Job posting URL
              <input
                defaultValue={editingApplication?.job_posting_url || ''}
                maxLength={2048}
                name="job_posting_url"
                type="url"
              />
            </label>
            <label className="form-field-wide">
              Job description
              <textarea
                defaultValue={editingApplication?.job_description || ''}
                maxLength={30000}
                name="job_description"
                placeholder="Paste the role description to analyze its recognized skill requirements."
                rows="5"
              />
            </label>
            <label className="form-field-wide">
              Required skills
              <input
                defaultValue={editingApplication?.required_skills?.join(', ') || ''}
                name="required_skills"
                placeholder="Python, PostgreSQL, React"
              />
              <span className="field-hint">Separate skills with commas.</span>
            </label>
            <label className="form-field-wide">
              Notes
              <textarea defaultValue={editingApplication?.notes || ''} name="notes" rows="3" />
            </label>
            <div className="form-actions form-field-wide">
              <button className="primary-button" disabled={isSaving} type="submit">
                {isSaving ? 'Saving…' : editingApplication ? 'Save changes' : 'Save application'}
              </button>
            </div>
          </form>
        </section>
      )}

      <form className="application-filters" onSubmit={applyFilters}>
        <label>
          Search
          <input
            defaultValue={filterDraft.search}
            key={`search-${filterDraft.search}`}
            maxLength={200}
            name="search"
            placeholder="Company or job title"
          />
        </label>
        <label>
          Status
          <select defaultValue={filterDraft.status} key={`status-${filterDraft.status}`} name="status">
            <option value="">All statuses</option>
            {STATUSES.map((status) => <option key={status}>{status}</option>)}
          </select>
        </label>
        <label>
          Sort by
          <select defaultValue={filterDraft.sort_by} key={`sort-${filterDraft.sort_by}`} name="sort_by">
            <option value="applied_on">Application date</option>
            <option value="deadline">Deadline</option>
          </select>
        </label>
        <label>
          Order
          <select defaultValue={filterDraft.sort_order} key={`order-${filterDraft.sort_order}`} name="sort_order">
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>
        </label>
        <button className="secondary-button" type="submit">Apply filters</button>
      </form>

      <section className="application-list" aria-labelledby="application-list-title">
        <div className="list-heading">
          <h2 id="application-list-title">Your opportunities</h2>
          <span>{applications.length} shown (up to 100)</span>
        </div>
        {isLoading ? (
          <div className="list-state" role="status">Loading your applications…</div>
        ) : applications.length === 0 ? (
          <div className="list-state">
            <h3>No applications found</h3>
            <p>Add an opportunity or adjust your search filters.</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="applications-table">
              <thead>
                <tr>
                  <th scope="col">Company / role</th>
                  <th scope="col">Location</th>
                  <th scope="col">Applied</th>
                  <th scope="col">Status</th>
                  <th scope="col">Next follow-up</th>
                  <th scope="col"><span className="visually-hidden">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {applications.map((application) => (
                  <tr key={application.id}>
                    <td>
                      <strong>{application.company_name}</strong>
                      <span>{application.job_title}</span>
                    </td>
                    <td>{application.location || '—'}</td>
                    <td>{application.applied_on || '—'}</td>
                    <td>
                      <span className={statusClass(application.status)}>{application.status}</span>
                    </td>
                    <td>
                      {application.next_follow_up_at
                        ? new Date(application.next_follow_up_at).toLocaleDateString()
                        : '—'}
                    </td>
                    <td>
                      <div className="row-actions">
                        <button
                          className="text-button"
                          onClick={() => openEditForm(application)}
                          type="button"
                        >
                          Edit
                        </button>
                        <button
                          className="text-button"
                          onClick={() => setTimelineApplication(
                            timelineApplication?.id === application.id ? null : application,
                          )}
                          type="button"
                        >
                          {timelineApplication?.id === application.id ? 'Close timeline' : 'Timeline'}
                        </button>
                        <button
                          className="text-button danger-button"
                          onClick={() => removeApplication(application)}
                          type="button"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      {timelineApplication && <ApplicationTimeline application={timelineApplication} />}
    </div>
  )
}

export default ApplicationsPage
