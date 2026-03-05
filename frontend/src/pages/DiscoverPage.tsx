import { useState, type FormEvent } from 'react'
import { api, type Influencer } from '../lib/api'

export default function DiscoverPage() {
  const [niche, setNiche] = useState('')
  const [platform, setPlatform] = useState('tiktok')
  const [searchType, setSearchType] = useState('user')
  const [results, setResults] = useState<Influencer[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setResults([])
    setLoading(true)
    setHasSearched(true)
    try {
      const found = await api.discover(niche, platform, searchType)
      setResults(found)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Discovery failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-xl font-bold mb-4">Discover Influencers</h1>
      <form onSubmit={handleSubmit} className="space-y-3 mb-6">
        <div>
          <label className="block text-sm font-medium mb-1">Niche</label>
          <input
            value={niche}
            onChange={e => setNiche(e.target.value)}
            placeholder={searchType === 'hashtag' ? 'e.g. #fitnessmotivation (no spaces)' : 'e.g. fitness, cooking, tech'}
            required
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Search by</label>
          <select
            value={searchType}
            onChange={e => setSearchType(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="user">Username</option>
            <option value="video">Videos</option>
            <option value="hashtag">Hashtag</option>
          </select>
          {searchType !== 'user' && (
            <p className="text-xs text-gray-500 mt-1">
              Finds creators by their content. Each profile is enriched with follower counts (~5s per creator).
            </p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Platform</label>
          <select
            value={platform}
            onChange={e => setPlatform(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="tiktok">TikTok</option>
            <option value="instagram">Instagram</option>
            <option value="youtube">YouTube</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {loading ? 'Searching... (this takes 10-20s)' : 'Search'}
        </button>
      </form>

      {loading && (
        <p className="text-gray-500 text-sm animate-pulse">
          {searchType === 'user'
            ? 'Scraping TikTok — this can take up to 20 seconds. Please wait...'
            : 'Searching TikTok and enriching profiles — this may take a minute. Please wait...'}
        </p>
      )}

      {error && <p className="text-red-600 text-sm">Error: {error}</p>}

      {!loading && hasSearched && results.length === 0 && !error && (
        <p className="text-gray-500 text-sm">No results found.</p>
      )}

      {results.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-gray-600">{results.length} influencer(s) found</p>
          {results.map(inf => (
            <div key={inf.id} className="border rounded p-3 text-sm">
              <a
                href={inf.url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-blue-600 hover:underline"
              >
                @{inf.handle}
              </a>
              <span className="ml-2 text-gray-500 capitalize">{inf.platform}</span>
              {inf.follower_count != null && (
                <span className="ml-2 text-gray-500">
                  {inf.follower_count.toLocaleString()} followers
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
