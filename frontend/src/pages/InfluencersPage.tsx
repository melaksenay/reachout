import { useEffect, useState } from 'react'
import { api, type Influencer } from '../lib/api'

export default function InfluencersPage() {
  const [influencers, setInfluencers] = useState<Influencer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getInfluencers()
      .then(setInfluencers)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

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
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
