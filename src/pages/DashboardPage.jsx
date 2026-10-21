import { useCallback, useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'
import { ApiError } from '../services/apiClient.js'
import { getDashboardAnalytics } from '../services/analyticsService.js'

const STATUS_COLORS = {
  Interested: '#a9b3ad',
  Applied: '#4b9282',
  Assessment: '#d3a44d',
  Interview: '#527db5',
  Offer: '#6b9a4c',
  Rejected: '#bf7063',
  Withdrawn: '#89928d',
}

const METRICS = [
  { key: 'total_applications', label: 'Total applications' },
  { key: 'applied_jobs', label: 'Applied' },
  { key: 'interviews_scheduled', label: 'Upcoming interviews' },
  { key: 'offers_received', label: 'Offers received' },
  { key: 'rejected_applications', label: 'Rejected' },
  { key: 'application_success_rate', label: 'Offer success rate', suffix: '%' },
]

function formatDateTime(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatPeriod(period, range) {
  const date = new Date(`${period}T00:00:00`)
  if (range === 'months') {
    return new Intl.DateTimeFormat(undefined, {
      month: 'short',
      year: '2-digit',
    }).format(date)
  }
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  }).format(date)
}

function formatActivity(activity) {
  if (activity.event_type === 'status_changed') {
    return `Status changed from ${activity.previous_status} to ${activity.new_status}`
  }
  if (activity.event_type === 'application_created') {
    return 'Application added'
  }
  if (activity.details) {
    return activity.details
  }
  return activity.event_type.replaceAll('_', ' ')
}

function DashboardPage() {
  const { accessToken, logout } = useAuth()
  const navigate = useNavigate()
  const [analytics, setAnalytics] = useState(null)
  const [range, setRange] = useState('weeks')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadCount, setReloadCount] = useState(0)

  const loadAnalytics = useCallback(async (signal) => {
    setIsLoading(true)
    setError('')
    try {
      const result = await getDashboardAnalytics(accessToken, {
        weeks: range === 'weeks' ? 12 : 1,
        months: range === 'months' ? 6 : 1,
        signal,
      })
      setAnalytics(result)
    } catch (requestError) {
      if (!signal?.aborted) {
        setAnalytics(null)
        if (requestError instanceof ApiError && requestError.status === 401) {
          logout()
          navigate('/login', { replace: true, state: { from: '/dashboard' } })
        } else {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Could not load dashboard analytics.',
          )
        }
      }
    } finally {
      if (!signal?.aborted) {
        setIsLoading(false)
      }
    }
  }, [accessToken, logout, navigate, range])

  useEffect(() => {
    const controller = new AbortController()
    queueMicrotask(() => {
      if (!controller.signal.aborted) {
        loadAnalytics(controller.signal)
      }
    })
    return () => controller.abort()
  }, [loadAnalytics, reloadCount])

  const chartData = analytics
    ? range === 'weeks'
      ? analytics.weekly_applications
      : analytics.monthly_applications
    : []
  const statusData = analytics
    ? Object.entries(analytics.status_distribution)
      .map(([name, value]) => ({ name, value }))
      .filter((item) => item.value > 0)
    : []

  return (
    <div className="dashboard-page analytics-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">OVERVIEW</p>
          <h1>Your search at a glance</h1>
          <p className="page-subtitle">
            A clear view of your opportunities and next steps.
          </p>
        </div>
        <label className="range-picker">
          Activity range
          <select
            aria-label="Activity chart range"
            onChange={(event) => setRange(event.target.value)}
            value={range}
          >
            <option value="weeks">Last 12 weeks</option>
            <option value="months">Last 6 months</option>
          </select>
        </label>
      </div>

      {error && (
        <div className="inline-error analytics-error" role="alert">
          <span>{error}</span>
          <button onClick={() => setReloadCount((count) => count + 1)} type="button">
            Try again
          </button>
        </div>
      )}

      <section className="metric-grid analytics-metric-grid" aria-label="Dashboard metrics">
        {METRICS.map((metric) => (
          <article className="metric-card" key={metric.key} aria-busy={isLoading}>
            <span>{metric.label}</span>
            {isLoading ? (
              <span className="metric-skeleton" aria-label="Loading metric" />
            ) : (
              <strong>
                {analytics ? `${analytics[metric.key]}${metric.suffix || ''}` : '—'}
              </strong>
            )}
            <small>
              {!analytics && !isLoading
                ? 'Unavailable until data loads'
                : metric.key === 'application_success_rate'
                ? 'Offers ÷ submitted applications'
                : metric.key === 'interviews_scheduled'
                  ? 'Scheduled interviews in the future'
                  : 'From your saved applications'}
            </small>
          </article>
        ))}
      </section>

      <section className="analytics-grid" aria-label="Application analytics">
        <article className="analytics-card trend-card">
          <div className="analytics-card-heading">
            <div>
              <h2>Applications submitted</h2>
              <p>{range === 'weeks' ? 'Weekly' : 'Monthly'} totals from your records</p>
            </div>
            {analytics && <span>{analytics.submitted_applications} submitted total</span>}
          </div>
          {isLoading ? (
            <div className="chart-state" role="status">Loading chart…</div>
          ) : chartData.length === 0 ? (
            <div className="chart-state">
              {error ? 'Chart unavailable until the API connection is restored.' : 'Application activity will appear here.'}
            </div>
          ) : (
            <div className="trend-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="#edf0ec" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    axisLine={false}
                    dataKey="period"
                    tickFormatter={(period) => formatPeriod(period, range)}
                    tickLine={false}
                    tick={{ fill: '#829089', fontSize: 10 }}
                    minTickGap={18}
                  />
                  <YAxis
                    allowDecimals={false}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#829089', fontSize: 10 }}
                  />
                  <Tooltip
                    labelFormatter={(period) => formatPeriod(period, range)}
                    formatter={(value) => [value, 'Applications']}
                  />
                  <Bar
                    dataKey="applications"
                    fill="#4b9282"
                    radius={[4, 4, 0, 0]}
                    isAnimationActive={false}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </article>

        <article className="analytics-card status-card">
          <div className="analytics-card-heading">
            <div>
              <h2>Status distribution</h2>
              <p>Current stage of each opportunity</p>
            </div>
          </div>
          {isLoading ? (
            <div className="chart-state" role="status">Loading status totals…</div>
          ) : statusData.length === 0 ? (
            <div className="chart-state">
              {error ? 'Status totals unavailable until the API connection is restored.' : 'Add an application to see status totals.'}
            </div>
          ) : (
            <div className="status-chart-wrap">
              <div className="status-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius="58%"
                      outerRadius="84%"
                      paddingAngle={2}
                      isAnimationActive={false}
                    >
                      {statusData.map((item) => (
                        <Cell fill={STATUS_COLORS[item.name]} key={item.name} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <ul className="status-legend">
                {Object.entries(analytics.status_distribution).map(([name, value]) => (
                  <li key={name}>
                    <span>
                      <i style={{ background: STATUS_COLORS[name] }} />
                      {name}
                    </span>
                    <strong>{value}</strong>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </article>
      </section>

      <p className="metric-formula">
        Interview conversion = applications with a non-cancelled interview ÷ submitted applications.
        Offer conversion and success rate = applications at Offer ÷ submitted applications.
        Interested roles are not included as submitted.
      </p>

      <section className="dashboard-lower-grid">
        <article className="analytics-card">
          <div className="analytics-card-heading">
            <div>
              <h2>Upcoming interviews</h2>
              <p>Your next scheduled conversations</p>
            </div>
          </div>
          {isLoading ? (
            <p className="feed-state" role="status">Loading interviews…</p>
          ) : error ? (
            <p className="feed-state">Interviews unavailable until the API connection is restored.</p>
          ) : analytics?.upcoming_interviews.length ? (
            <ul className="dashboard-feed">
              {analytics.upcoming_interviews.map((interview) => (
                <li key={interview.id}>
                  <span className="feed-date">{formatDateTime(interview.scheduled_at)}</span>
                  <strong>{interview.company_name} · {interview.job_title}</strong>
                  <span>{interview.round_name}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="feed-state">No upcoming interviews scheduled.</p>
          )}
        </article>

        <article className="analytics-card">
          <div className="analytics-card-heading">
            <div>
              <h2>Follow-ups</h2>
              <p>Overdue and due within 30 days</p>
            </div>
          </div>
          {isLoading ? (
            <p className="feed-state" role="status">Loading follow-ups…</p>
          ) : error ? (
            <p className="feed-state">Follow-ups unavailable until the API connection is restored.</p>
          ) : analytics?.upcoming_follow_ups.length ? (
            <ul className="dashboard-feed">
              {analytics.upcoming_follow_ups.map((followUp) => (
                <li key={followUp.id}>
                  <span className={followUp.overdue ? 'feed-date overdue-label' : 'feed-date'}>
                    {followUp.overdue ? 'Overdue · ' : 'Due · '}
                    {formatDateTime(followUp.due_at)}
                  </span>
                  <strong>{followUp.title}</strong>
                  <span>{followUp.company_name} · {followUp.job_title}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="feed-state">No incomplete follow-ups due in the next 30 days.</p>
          )}
        </article>

        <article className="analytics-card activity-card">
          <div className="analytics-card-heading">
            <div>
              <h2>Recent activity</h2>
              <p>Latest changes in your application timeline</p>
            </div>
          </div>
          {isLoading ? (
            <p className="feed-state" role="status">Loading activity…</p>
          ) : error ? (
            <p className="feed-state">Activity unavailable until the API connection is restored.</p>
          ) : analytics?.recent_activity.length ? (
            <ul className="dashboard-feed">
              {analytics.recent_activity.map((activity) => (
                <li key={activity.id}>
                  <span className="feed-date">{formatDateTime(activity.occurred_at)}</span>
                  <strong>{activity.company_name} · {activity.job_title}</strong>
                  <span>{formatActivity(activity)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="feed-state">Your application activity will appear here.</p>
          )}
        </article>
      </section>
    </div>
  )
}

export default DashboardPage
