import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type DashboardData, PIPELINE_STAGES } from '../lib/api'

const STAGE_COLORS: Record<string, string> = {
  discovered: 'bg-gray-100 text-gray-700 border-gray-200',
  drafted: 'bg-blue-100 text-blue-700 border-blue-200',
  sent: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  replied: 'bg-green-100 text-green-700 border-green-200',
  negotiating: 'bg-purple-100 text-purple-700 border-purple-200',
  closed: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  rejected: 'bg-red-100 text-red-700 border-red-200',
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getDashboard()
      .then(setData)
      .catch(err => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-gray-500">Loading dashboard...</p>
  if (error || !data) return <p className="text-red-600">Error: {error ?? 'No data'}</p>

  const activeCampaigns = data.total_campaigns -
    (data.campaigns_by_status['closed'] ?? 0) -
    (data.campaigns_by_status['rejected'] ?? 0)

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Top stat cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="border rounded-lg p-5">
          <p className="text-sm text-gray-500 mb-1">Total Influencers</p>
          <p className="text-3xl font-bold">{data.total_influencers}</p>
        </div>
        <div className="border rounded-lg p-5">
          <p className="text-sm text-gray-500 mb-1">Active Campaigns</p>
          <p className="text-3xl font-bold">{activeCampaigns}</p>
        </div>
        <div className="border rounded-lg p-5">
          <p className="text-sm text-gray-500 mb-1">Response Rate</p>
          <p className="text-3xl font-bold">{Math.round(data.response_rate * 100)}%</p>
        </div>
      </div>

      {/* Pipeline breakdown */}
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Pipeline</h2>
      <div className="grid grid-cols-7 gap-2 mb-8">
        {PIPELINE_STAGES.map(stage => (
          <div
            key={stage}
            className={`border rounded-lg p-3 text-center ${STAGE_COLORS[stage] ?? ''}`}
          >
            <p className="text-2xl font-bold">{data.campaigns_by_status[stage] ?? 0}</p>
            <p className="text-xs capitalize mt-0.5">{stage}</p>
          </div>
        ))}
      </div>

      {/* Recent activity */}
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Recent Activity</h2>
      {data.recent_campaigns.length === 0 ? (
        <p className="text-sm text-gray-400 italic">
          No campaigns yet.{' '}
          <Link to="/discover" className="text-blue-600 hover:underline">Discover influencers</Link> to get started.
        </p>
      ) : (
        <div className="border rounded-lg divide-y">
          {data.recent_campaigns.map(c => (
            <div key={c.id} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <Link
                  to={`/influencers/${c.influencer_id}`}
                  className="text-sm font-medium text-blue-600 hover:underline"
                >
                  @{c.influencer_handle}
                </Link>
                <span className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded capitalize">
                  {c.influencer_platform}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${STAGE_COLORS[c.status] ?? 'bg-gray-100 text-gray-700'}`}>
                  {c.status}
                </span>
                <span className="text-xs text-gray-400 w-16 text-right">
                  {timeAgo(c.last_updated)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
