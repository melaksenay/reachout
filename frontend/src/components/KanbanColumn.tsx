import { type CampaignWithInfluencer, type PipelineStage } from '../lib/api'
import CampaignCard from './CampaignCard'

interface KanbanColumnProps {
  stage: PipelineStage
  campaigns: CampaignWithInfluencer[]
  onStatusChange: (campaignId: string, status: PipelineStage) => Promise<void>
  onNotesChange: (campaignId: string, notes: string) => Promise<void>
  onMessageChange: (campaignId: string, message: string) => Promise<void>
  selectedCampaigns?: Set<string>
  onToggleSelect?: (campaignId: string) => void
}

const STAGE_COLORS: Record<string, string> = {
  drafted: 'bg-blue-100 text-blue-700',
  sent: 'bg-yellow-100 text-yellow-700',
  replied: 'bg-green-100 text-green-700',
  negotiating: 'bg-purple-100 text-purple-700',
  closed: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
}

export default function KanbanColumn({ stage, campaigns, onStatusChange, onNotesChange, onMessageChange, selectedCampaigns, onToggleSelect }: KanbanColumnProps) {
  return (
    <div className="flex flex-col min-w-65 max-w-70 shrink-0">
      {/* Column header */}
      <div className="flex items-center gap-2 mb-3 px-1">
        <h3 className="text-sm font-semibold capitalize">{stage}</h3>
        <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${STAGE_COLORS[stage] ?? 'bg-gray-100 text-gray-700'}`}>
          {campaigns.length}
        </span>
      </div>

      {/* Card list */}
      <div className="flex flex-col gap-2 overflow-y-auto pr-1" style={{ maxHeight: 'calc(100vh - 200px)' }}>
        {campaigns.length === 0 && (
          <p className="text-xs text-gray-400 italic px-1">No campaigns</p>
        )}
        {campaigns.map(campaign => (
          <CampaignCard
            key={campaign.id}
            campaign={campaign}
            onStatusChange={onStatusChange}
            onNotesChange={onNotesChange}
            onMessageChange={onMessageChange}
            selected={selectedCampaigns?.has(campaign.id)}
            onToggleSelect={onToggleSelect}
          />
        ))}
      </div>
    </div>
  )
}
