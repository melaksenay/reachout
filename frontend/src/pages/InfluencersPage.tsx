import { useEffect, useState } from 'react'
import { api, type Influencer } from '../lib/api'

export default function InfluencersPage() {
  const [influencers, setInfluencers] = useState<Influencer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [draftLoading, setDraftLoading] = useState<Record<string, boolean>>({})
  const [drafted, setDrafted] = useState<Record<string, boolean>>({})
  const [draftErrors, setDraftErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    api.getInfluencers()
      .then(setInfluencers)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  // Check which influencers already have campaigns
  useEffect(() => {
    api.getCampaigns().then(campaigns => {
      const existing: Record<string, boolean> = {}
      for (const c of campaigns) {
        existing[c.influencer_id] = true
      }
      setDrafted(existing)
    }).catch(() => {})
  }, [])

  const handleAddToPipeline = async (influencerId: string) => {
    setDraftLoading(prev => ({ ...prev, [influencerId]: true }))
    setDraftErrors(prev => ({ ...prev, [influencerId]: '' }))
    try {
      await api.draftCampaign(influencerId)
      setDrafted(prev => ({ ...prev, [influencerId]: true }))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add'
      setDraftErrors(prev => ({ ...prev, [influencerId]: msg }))
    } finally {
      setDraftLoading(prev => ({ ...prev, [influencerId]: false }))
    }
  }

  if (loading) return <p className="text-gray-500">Loading influencers...</p>
  if (error) return <p className="text-red-600">Error: {error}</p>
  if (influencers.length === 0) {
    return <p className="text-gray-500">No influencers yet. Try the Discover page.</p>
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Influencers</h1>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b bg-gray-50 text-left">
              <th className="px-4 py-2">Handle</th>
              <th className="px-4 py-2">Platform</th>
              <th className="px-4 py-2">Followers</th>
              <th className="px-4 py-2">Added</th>
              <th className="px-4 py-2">Pipeline</th>
            </tr>
          </thead>
          <tbody>
            {influencers.map(inf => (
              <tr key={inf.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-2">
                  <a
                    href={inf.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    @{inf.handle}
                  </a>
                </td>
                <td className="px-4 py-2 capitalize">{inf.platform}</td>
                <td className="px-4 py-2">
                  {inf.follower_count != null
                    ? inf.follower_count.toLocaleString()
                    : '\u2014'}
                </td>
                <td className="px-4 py-2 text-gray-500">
                  {new Date(inf.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-2">
                  {drafted[inf.id] ? (
                    <span className="text-xs text-green-600 font-medium">In Pipeline</span>
                  ) : (
                    <>
                      <button
                        onClick={() => handleAddToPipeline(inf.id)}
                        disabled={!!draftLoading[inf.id]}
                        className="text-xs bg-blue-600 text-white px-2.5 py-1 rounded hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                      >
                        {draftLoading[inf.id] ? 'Adding...' : 'Add to Pipeline'}
                      </button>
                      {draftErrors[inf.id] && (
                        <p className="text-red-500 text-xs mt-0.5">{draftErrors[inf.id]}</p>
                      )}
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
