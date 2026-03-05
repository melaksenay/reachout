import { useRef, useCallback, useState } from 'react'
import { type CampaignWithInfluencer, PIPELINE_STAGES, type PipelineStage } from '../lib/api'

interface CampaignCardProps {
  campaign: CampaignWithInfluencer
  onStatusChange: (campaignId: string, status: PipelineStage) => Promise<void>
  onNotesChange: (campaignId: string, notes: string) => Promise<void>
  onMessageChange: (campaignId: string, message: string) => Promise<void>
  selected?: boolean
  onToggleSelect?: (campaignId: string) => void
}

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export default function CampaignCard({ campaign, onStatusChange, onNotesChange, onMessageChange, selected, onToggleSelect }: CampaignCardProps) {
  const [notesValue, setNotesValue] = useState(campaign.notes ?? '')
  const [messageValue, setMessageValue] = useState(campaign.generated_message ?? '')
  const [editingMessage, setEditingMessage] = useState(false)
  const [statusLoading, setStatusLoading] = useState(false)
  const notesDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const messageDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleNotesInput = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const val = e.target.value
      setNotesValue(val)
      if (notesDebounceRef.current) clearTimeout(notesDebounceRef.current)
      notesDebounceRef.current = setTimeout(() => {
        onNotesChange(campaign.id, val)
      }, 1000)
    },
    [campaign.id, onNotesChange],
  )

  const handleMessageInput = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const val = e.target.value
      setMessageValue(val)
      if (messageDebounceRef.current) clearTimeout(messageDebounceRef.current)
      messageDebounceRef.current = setTimeout(() => {
        onMessageChange(campaign.id, val)
      }, 1000)
    },
    [campaign.id, onMessageChange],
  )

  const handleStatusChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newStatus = e.target.value as PipelineStage
    setStatusLoading(true)
    try {
      await onStatusChange(campaign.id, newStatus)
    } finally {
      setStatusLoading(false)
    }
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-3 space-y-2 ${selected ? 'border-blue-400 ring-1 ring-blue-200' : 'border-gray-200'}`}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {onToggleSelect && (
            <input
              type="checkbox"
              checked={!!selected}
              onChange={() => onToggleSelect(campaign.id)}
              className="cursor-pointer"
            />
          )}
          <a
            href={campaign.influencer_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-blue-600 hover:underline text-sm"
          >
            @{campaign.influencer_handle}
          </a>
          <span className="ml-1.5 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded capitalize">
            {campaign.influencer_platform}
          </span>
        </div>
        {campaign.influencer_follower_count != null && (
          <span className="text-xs text-gray-400">
            {campaign.influencer_follower_count.toLocaleString()} followers
          </span>
        )}
      </div>

      {/* Message — click to edit */}
      {messageValue ? (
        editingMessage ? (
          <div>
            <textarea
              value={messageValue}
              onChange={handleMessageInput}
              rows={4}
              className="w-full text-xs border rounded p-2 resize-none text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-300"
            />
            <button
              onClick={() => setEditingMessage(false)}
              className="text-[10px] text-gray-400 hover:text-gray-600 mt-0.5"
            >
              Done editing
            </button>
          </div>
        ) : (
          <div
            onClick={() => setEditingMessage(true)}
            className="text-xs text-gray-600 bg-gray-50 rounded p-2 cursor-pointer hover:bg-gray-100 transition-colors"
            title="Click to edit message"
          >
            <p className="line-clamp-3 whitespace-pre-wrap">{messageValue}</p>
            <span className="text-[10px] text-gray-400 mt-1 block">Click to edit</span>
          </div>
        )
      ) : (
        <p className="text-xs text-gray-400 italic">No message generated yet</p>
      )}

      {/* Move to dropdown */}
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-400">Move to:</label>
        <select
          value={campaign.status}
          onChange={handleStatusChange}
          disabled={statusLoading}
          className="text-xs border rounded px-1.5 py-1 bg-white disabled:opacity-50"
        >
          {PIPELINE_STAGES.map(stage => (
            <option key={stage} value={stage}>
              {stage}
            </option>
          ))}
        </select>
      </div>

      {/* Notes */}
      <textarea
        value={notesValue}
        onChange={handleNotesInput}
        placeholder="Add notes..."
        rows={2}
        className="w-full text-xs border rounded p-1.5 resize-none text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-300"
      />

      {/* Timestamp */}
      <p className="text-[10px] text-gray-400">
        Updated {timeAgo(campaign.status_updated_at)}
      </p>
    </div>
  )
}
