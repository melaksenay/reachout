import { useEffect, useState, useCallback } from 'react'
import { api, type CampaignWithInfluencer, PIPELINE_STAGES, type PipelineStage } from '../lib/api'
import KanbanColumn from '../components/KanbanColumn'

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<CampaignWithInfluencer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCampaigns = useCallback(async () => {
    try {
      const data = await api.getCampaigns()
      setCampaigns(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load campaigns')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCampaigns()
  }, [fetchCampaigns])

  const handleStatusChange = useCallback(
    async (campaignId: string, newStatus: PipelineStage) => {
      // Optimistic update
      setCampaigns(prev =>
        prev.map(c =>
          c.id === campaignId ? { ...c, status: newStatus, status_updated_at: new Date().toISOString() } : c,
        ),
      )
      try {
        await api.updateCampaignStatus(campaignId, newStatus)
      } catch {
        // Revert on failure
        await fetchCampaigns()
      }
    },
    [fetchCampaigns],
  )

  const handleNotesChange = useCallback(
    async (campaignId: string, notes: string) => {
      try {
        await api.updateCampaignNotes(campaignId, notes)
      } catch {
        // Silently fail — notes will be stale but not lost locally
      }
    },
    [],
  )

  const handleMessageChange = useCallback(
    async (campaignId: string, message: string) => {
      try {
        await api.updateCampaignMessage(campaignId, message)
      } catch {
        // Silently fail — message is preserved locally
      }
    },
    [],
  )

  if (loading) return <p className="text-gray-500 p-4">Loading pipeline...</p>
  if (error) return <p className="text-red-600 p-4">Error: {error}</p>

  const campaignsByStage = (stage: PipelineStage) =>
    campaigns.filter(c => c.status === stage)

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Pipeline</h1>

      {campaigns.length === 0 ? (
        <p className="text-gray-500">
          No campaigns yet. Go to <span className="font-medium">Discover</span> to find influencers,
          then draft messages from the <span className="font-medium">Influencers</span> page.
        </p>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {PIPELINE_STAGES.map(stage => (
            <KanbanColumn
              key={stage}
              stage={stage}
              campaigns={campaignsByStage(stage)}
              onStatusChange={handleStatusChange}
              onNotesChange={handleNotesChange}
              onMessageChange={handleMessageChange}
            />
          ))}
        </div>
      )}
    </div>
  )
}
