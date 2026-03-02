import { useEffect, useState } from 'react'
import { api, type Influencer, type OutreachCampaign } from '../lib/api'

export default function CampaignsPage() {
  const [influencers, setInfluencers] = useState<Influencer[]>([])
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)

  const [draftLoading, setDraftLoading] = useState<Record<string, boolean>>({})
  const [campaigns, setCampaigns] = useState<Record<string, OutreachCampaign>>({})
  const [draftErrors, setDraftErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    api.getInfluencers()
      .then(setInfluencers)
      .catch(err => setListError(err.message))
      .finally(() => setListLoading(false))
  }, [])

  const handleDraft = async (influencerId: string) => {
    setDraftLoading(prev => ({ ...prev, [influencerId]: true }))
    setDraftErrors(prev => ({ ...prev, [influencerId]: '' }))
    try {
      const campaign = await api.draftCampaign(influencerId)
      setCampaigns(prev => ({ ...prev, [influencerId]: campaign }))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to draft'
      setDraftErrors(prev => ({ ...prev, [influencerId]: msg }))
    } finally {
      setDraftLoading(prev => ({ ...prev, [influencerId]: false }))
    }
  }

  if (listLoading) return <p className="text-gray-500">Loading influencers...</p>
  if (listError) return <p className="text-red-600">Error: {listError}</p>
  if (influencers.length === 0) {
    return <p className="text-gray-500">No influencers yet. Try the Discover page first.</p>
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Campaigns</h1>
      <div className="space-y-4">
        {influencers.map(inf => (
          <div key={inf.id} className="border rounded p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="font-medium">@{inf.handle}</span>
                <span className="ml-2 text-sm text-gray-500 capitalize">{inf.platform}</span>
              </div>
              <button
                onClick={() => handleDraft(inf.id)}
                disabled={!!draftLoading[inf.id]}
                className="text-sm bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 disabled:opacity-50 cursor-pointer"
              >
                {draftLoading[inf.id]
                  ? 'Drafting...'
                  : campaigns[inf.id]
                    ? 'Re-draft'
                    : 'Draft Message'}
              </button>
            </div>

            {draftErrors[inf.id] && (
              <p className="text-red-600 text-sm">{draftErrors[inf.id]}</p>
            )}

            {campaigns[inf.id] && (
              <div className="mt-2 bg-gray-50 rounded p-3 text-sm">
                <p className="text-xs text-gray-500 mb-1 uppercase tracking-wide">
                  Status: {campaigns[inf.id].status}
                </p>
                <p className="whitespace-pre-wrap">{campaigns[inf.id].generated_message}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
