import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Influencer, type Tag, type InfluencerFilters } from '../lib/api'
import BulkActionBar from '../components/BulkActionBar'

export default function InfluencersPage() {
  const navigate = useNavigate()
  const [influencers, setInfluencers] = useState<Influencer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [draftLoading, setDraftLoading] = useState<Record<string, boolean>>({})
  const [drafted, setDrafted] = useState<Record<string, boolean>>({})
  const [draftErrors, setDraftErrors] = useState<Record<string, string>>({})

  // Filters
  const [platform, setPlatform] = useState('')
  const [minFollowers, setMinFollowers] = useState('')
  const [maxFollowers, setMaxFollowers] = useState('')
  const [tagFilter, setTagFilter] = useState('')
  const [allTags, setAllTags] = useState<Tag[]>([])

  // Bulk selection
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkLoading, setBulkLoading] = useState(false)
  const [tagInput, setTagInput] = useState('')
  const [showTagInput, setShowTagInput] = useState(false)

  const fetchInfluencers = useCallback(async () => {
    setLoading(true)
    setError(null)
    const filters: InfluencerFilters = {}
    if (platform) filters.platform = platform
    if (minFollowers) filters.min_followers = Number(minFollowers)
    if (maxFollowers) filters.max_followers = Number(maxFollowers)
    if (tagFilter) filters.tag = tagFilter
    try {
      const data = await api.getInfluencers(filters)
      setInfluencers(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [platform, minFollowers, maxFollowers, tagFilter])

  useEffect(() => {
    fetchInfluencers()
  }, [fetchInfluencers])

  // Load campaigns and tags once
  useEffect(() => {
    api.getCampaigns().then(campaigns => {
      const existing: Record<string, boolean> = {}
      for (const c of campaigns) {
        existing[c.influencer_id] = true
      }
      setDrafted(existing)
    }).catch(() => {})

    api.getTags().then(setAllTags).catch(() => {})
  }, [])

  const handleAddToPipeline = async (e: React.MouseEvent, influencerId: string) => {
    e.stopPropagation()
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

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selected.size === influencers.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(influencers.map(i => i.id)))
    }
  }

  const undraftedSelected = [...selected].filter(id => !drafted[id])

  const handleBulkDraft = async () => {
    if (undraftedSelected.length === 0) return
    setBulkLoading(true)
    try {
      await api.bulkDraft(undraftedSelected)
      setSelected(new Set())
      // Refresh drafted state
      const campaigns = await api.getCampaigns()
      const existing: Record<string, boolean> = {}
      for (const c of campaigns) existing[c.influencer_id] = true
      setDrafted(existing)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Bulk draft failed')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDelete = async () => {
    if (selected.size === 0) return
    if (!window.confirm(`Delete ${selected.size} influencer(s)? This also removes their campaigns, notes, and tags.`)) return
    setBulkLoading(true)
    try {
      await api.bulkDelete([...selected])
      setSelected(new Set())
      await fetchInfluencers()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Bulk delete failed')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkTag = async () => {
    if (!tagInput.trim()) return
    setBulkLoading(true)
    try {
      await api.bulkTag([...selected], tagInput.trim())
      setSelected(new Set())
      setTagInput('')
      setShowTagInput(false)
      // Refresh tags
      api.getTags().then(setAllTags).catch(() => {})
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Bulk tag failed')
    } finally {
      setBulkLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Influencers</h1>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 mb-4 items-end">
        <div>
          <label className="block text-[10px] text-gray-500 mb-0.5">Platform</label>
          <select
            value={platform}
            onChange={e => setPlatform(e.target.value)}
            className="text-xs border rounded px-2 py-1"
          >
            <option value="">All</option>
            <option value="tiktok">TikTok</option>
            <option value="instagram">Instagram</option>
          </select>
        </div>
        <div>
          <label className="block text-[10px] text-gray-500 mb-0.5">Min followers</label>
          <input
            type="number"
            value={minFollowers}
            onChange={e => setMinFollowers(e.target.value)}
            placeholder="e.g. 1000"
            className="text-xs border rounded px-2 py-1 w-24"
          />
        </div>
        <div>
          <label className="block text-[10px] text-gray-500 mb-0.5">Max followers</label>
          <input
            type="number"
            value={maxFollowers}
            onChange={e => setMaxFollowers(e.target.value)}
            placeholder="e.g. 100000"
            className="text-xs border rounded px-2 py-1 w-24"
          />
        </div>
        <div>
          <label className="block text-[10px] text-gray-500 mb-0.5">Tag</label>
          <select
            value={tagFilter}
            onChange={e => setTagFilter(e.target.value)}
            className="text-xs border rounded px-2 py-1"
          >
            <option value="">All</option>
            {allTags.map(t => (
              <option key={t.id} value={t.name}>{t.name}</option>
            ))}
          </select>
        </div>
        {(platform || minFollowers || maxFollowers || tagFilter) && (
          <button
            onClick={() => { setPlatform(''); setMinFollowers(''); setMaxFollowers(''); setTagFilter('') }}
            className="text-xs text-red-500 hover:underline cursor-pointer"
          >
            Clear filters
          </button>
        )}
      </div>

      {loading && <p className="text-gray-500 text-sm">Loading...</p>}
      {error && <p className="text-red-600 text-sm">Error: {error}</p>}

      {!loading && !error && influencers.length === 0 && (
        <p className="text-gray-500 text-sm">
          {platform || minFollowers || maxFollowers || tagFilter
            ? 'No influencers match these filters.'
            : 'No influencers yet. Try the Discover page.'}
        </p>
      )}

      {!loading && influencers.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b bg-gray-50 text-left">
                <th className="px-2 py-2 w-8">
                  <input
                    type="checkbox"
                    checked={selected.size === influencers.length && influencers.length > 0}
                    onChange={toggleSelectAll}
                    className="cursor-pointer"
                  />
                </th>
                <th className="px-4 py-2">Handle</th>
                <th className="px-4 py-2">Platform</th>
                <th className="px-4 py-2">Followers</th>
                <th className="px-4 py-2">Added</th>
                <th className="px-4 py-2">Pipeline</th>
              </tr>
            </thead>
            <tbody>
              {influencers.map(inf => (
                <tr
                  key={inf.id}
                  onClick={() => navigate(`/influencers/${inf.id}`)}
                  className={`border-b hover:bg-gray-50 cursor-pointer ${selected.has(inf.id) ? 'bg-blue-50' : ''}`}
                >
                  <td className="px-2 py-2" onClick={e => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selected.has(inf.id)}
                      onChange={() => toggleSelect(inf.id)}
                      className="cursor-pointer"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <span className="text-blue-600">@{inf.handle}</span>
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
                          onClick={(e) => handleAddToPipeline(e, inf.id)}
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
      )}

      <BulkActionBar count={selected.size} onClear={() => setSelected(new Set())}>
        <button
          onClick={handleBulkDraft}
          disabled={bulkLoading || undraftedSelected.length === 0}
          className="text-sm bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded disabled:opacity-50 cursor-pointer"
        >
          {bulkLoading ? 'Drafting...' : undraftedSelected.length === 0 ? 'All in Pipeline' : `Draft ${undraftedSelected.length}`}
        </button>
        {showTagInput ? (
          <form
            onSubmit={e => { e.preventDefault(); handleBulkTag() }}
            className="flex items-center gap-1"
          >
            <input
              type="text"
              value={tagInput}
              onChange={e => setTagInput(e.target.value)}
              placeholder="Tag name"
              autoFocus
              className="text-sm px-2 py-1 rounded bg-white text-gray-900 w-28 border border-gray-300"
            />
            <button
              type="submit"
              disabled={bulkLoading || !tagInput.trim()}
              className="text-sm bg-green-500 hover:bg-green-600 text-white px-2 py-1.5 rounded disabled:opacity-50 cursor-pointer"
            >
              Apply
            </button>
            <button
              type="button"
              onClick={() => { setShowTagInput(false); setTagInput('') }}
              className="text-sm text-gray-300 hover:text-white cursor-pointer"
            >
              Cancel
            </button>
          </form>
        ) : (
          <button
            onClick={() => setShowTagInput(true)}
            className="text-sm bg-gray-700 hover:bg-gray-600 text-white px-3 py-1.5 rounded cursor-pointer"
          >
            Tag
          </button>
        )}
        <button
          onClick={handleBulkDelete}
          disabled={bulkLoading}
          className="text-sm bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded disabled:opacity-50 cursor-pointer"
        >
          {bulkLoading ? 'Deleting...' : `Delete ${selected.size}`}
        </button>
      </BulkActionBar>
    </div>
  )
}
