import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, type InfluencerDetail, type Tag } from '../lib/api'

export default function InfluencerDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<InfluencerDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Notes state
  const [noteBody, setNoteBody] = useState('')
  const [noteLoading, setNoteLoading] = useState(false)

  // Refresh state
  const [refreshing, setRefreshing] = useState(false)

  // Tags state
  const [tagInput, setTagInput] = useState('')
  const [allTags, setAllTags] = useState<Tag[]>([])

  const fetchDetail = useCallback(async () => {
    if (!id) return
    try {
      const detail = await api.getInfluencerDetail(id)
      setData(detail)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchDetail()
    api.getTags().then(setAllTags).catch(() => {})
  }, [fetchDetail])

  const handleAddNote = async () => {
    if (!id || !noteBody.trim()) return
    setNoteLoading(true)
    try {
      const note = await api.addNote(id, noteBody.trim())
      setData(prev => prev ? { ...prev, notes: [note, ...prev.notes] } : prev)
      setNoteBody('')
    } catch { /* ignore */ }
    finally { setNoteLoading(false) }
  }

  const handleDeleteNote = async (noteId: string) => {
    if (!id) return
    try {
      await api.deleteNote(id, noteId)
      setData(prev => prev ? { ...prev, notes: prev.notes.filter(n => n.id !== noteId) } : prev)
    } catch { /* ignore */ }
  }

  const handleAddTag = async () => {
    if (!id || !tagInput.trim()) return
    try {
      const tag = await api.addTag(id, tagInput.trim().toLowerCase())
      setData(prev => {
        if (!prev) return prev
        if (prev.tags.some(t => t.id === tag.id)) return prev
        return { ...prev, tags: [...prev.tags, tag] }
      })
      // Refresh global tags list
      if (!allTags.some(t => t.id === tag.id)) {
        setAllTags(prev => [...prev, tag])
      }
      setTagInput('')
    } catch { /* ignore */ }
  }

  const handleRemoveTag = async (tagId: string) => {
    if (!id) return
    try {
      await api.removeTag(id, tagId)
      setData(prev => prev ? { ...prev, tags: prev.tags.filter(t => t.id !== tagId) } : prev)
    } catch { /* ignore */ }
  }

  const handleRefresh = async () => {
    if (!id) return
    setRefreshing(true)
    try {
      const updated = await api.refreshProfile(id)
      setData(prev => prev ? { ...prev, influencer: updated } : prev)
    } catch { /* ignore */ }
    finally { setRefreshing(false) }
  }

  const handleQuickTag = async (tag: Tag) => {
    if (!id) return
    if (data?.tags.some(t => t.id === tag.id)) return
    try {
      await api.addTag(id, tag.name)
      setData(prev => prev ? { ...prev, tags: [...prev.tags, tag] } : prev)
    } catch { /* ignore */ }
  }

  if (loading) return <p className="text-gray-500">Loading...</p>
  if (error || !data) return <p className="text-red-600">Error: {error ?? 'Not found'}</p>

  const { influencer, campaigns, notes, tags } = data

  return (
    <div className="max-w-3xl">
      {/* Back link */}
      <Link to="/influencers" className="text-sm text-blue-600 hover:underline">
        &larr; Back to Influencers
      </Link>

      {/* Profile header */}
      <div className="mt-4 mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">@{influencer.handle}</h1>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded capitalize">
            {influencer.platform}
          </span>
        </div>
        <div className="flex gap-4 mt-1 text-sm text-gray-500 items-center">
          {influencer.follower_count != null ? (
            <span>{influencer.follower_count.toLocaleString()} followers</span>
          ) : (
            <span className="text-gray-400 italic">No follower data</span>
          )}
          <button
            type="button"
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-blue-500 hover:underline text-sm cursor-pointer disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : influencer.follower_count == null ? 'Fetch profile data' : 'Refresh'}
          </button>
          <a href={influencer.url} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">
            View profile
          </a>
          <span>Added {new Date(influencer.created_at).toLocaleDateString()}</span>
        </div>
        {influencer.bio_text && (
          <p className="mt-2 text-sm text-gray-700">{influencer.bio_text}</p>
        )}
      </div>

      {/* Tags */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold mb-2">Tags</h2>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {tags.map(tag => (
            <span key={tag.id} className="inline-flex items-center gap-1 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
              {tag.name}
              <button
                type="button"
                onClick={() => handleRemoveTag(tag.id)}
                className="text-blue-400 hover:text-blue-600 cursor-pointer"
              >
                &times;
              </button>
            </span>
          ))}
          {tags.length === 0 && <span className="text-xs text-gray-400 italic">No tags</span>}
        </div>

        <form onSubmit={e => { e.preventDefault(); handleAddTag() }} className="flex gap-2 items-center">
          <input
            value={tagInput}
            onChange={e => setTagInput(e.target.value)}
            placeholder="Add tag..."
            className="text-xs border rounded px-2 py-1 w-32"
          />
          <button type="submit" className="text-xs text-blue-600 hover:underline cursor-pointer">
            Add
          </button>
        </form>

        {/* Quick-add from existing tags */}
        {allTags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {allTags
              .filter(t => !tags.some(assigned => assigned.id === t.id))
              .slice(0, 10)
              .map(t => (
                <button
                  type="button"
                  key={t.id}
                  onClick={() => handleQuickTag(t)}
                  className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded hover:bg-gray-200 cursor-pointer"
                >
                  + {t.name}
                </button>
              ))}
          </div>
        )}
      </section>

      {/* Campaigns timeline */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold mb-2">Campaigns ({campaigns.length})</h2>
        {campaigns.length === 0 ? (
          <p className="text-xs text-gray-400 italic">No campaigns yet</p>
        ) : (
          <div className="space-y-2">
            {campaigns.map(c => (
              <div key={c.id} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-medium bg-blue-50 text-blue-700 px-2 py-0.5 rounded capitalize">
                    {c.status}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(c.last_updated).toLocaleDateString()}
                  </span>
                </div>
                {c.generated_message && (
                  <p className="text-xs text-gray-600 whitespace-pre-wrap mt-1">{c.generated_message}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Notes */}
      <section>
        <h2 className="text-sm font-semibold mb-2">Notes ({notes.length})</h2>

        <form onSubmit={e => { e.preventDefault(); handleAddNote() }} className="flex gap-2 mb-3">
          <input
            value={noteBody}
            onChange={e => setNoteBody(e.target.value)}
            placeholder="Add a note..."
            className="flex-1 text-sm border rounded px-3 py-1.5"
          />
          <button
            type="submit"
            disabled={noteLoading || !noteBody.trim()}
            className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
          >
            {noteLoading ? 'Adding...' : 'Add'}
          </button>
        </form>

        {notes.length === 0 ? (
          <p className="text-xs text-gray-400 italic">No notes yet</p>
        ) : (
          <div className="space-y-2">
            {notes.map(note => (
              <div key={note.id} className="flex justify-between items-start border rounded p-2.5 text-sm">
                <div>
                  <p className="text-gray-700">{note.body}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">
                    {new Date(note.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleDeleteNote(note.id)}
                  className="text-xs text-red-400 hover:text-red-600 ml-2 shrink-0 cursor-pointer"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
