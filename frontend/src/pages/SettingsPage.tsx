import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function SettingsPage() {
  const [brandDescription, setBrandDescription] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    api.getSettings()
      .then(settings => {
        setBrandDescription(settings.brand_description ?? '')
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)
    try {
      await api.updateSettings(brandDescription)
      setMessage({ type: 'success', text: 'Settings saved.' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save'
      setMessage({ type: 'error', text: msg })
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-gray-500">Loading settings...</p>

  return (
    <div className="max-w-xl">
      <h1 className="text-xl font-bold mb-4">Settings</h1>

      <label className="block text-sm font-medium text-gray-700 mb-1">
        Brand Description
      </label>
      <p className="text-xs text-gray-500 mb-2">
        Describe your brand/product in 2-3 sentences. This is included in every AI-generated outreach message.
      </p>
      <textarea
        value={brandDescription}
        onChange={e => setBrandDescription(e.target.value)}
        rows={4}
        placeholder="e.g. We make organic vegan teff crackers. Our target audience is health-conscious foodies aged 20-35."
        className="w-full border rounded p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-300"
      />

      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving || !brandDescription.trim()}
          className="bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {saving ? 'Saving...' : 'Save'}
        </button>

        {message && (
          <span className={`text-sm ${message.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
            {message.text}
          </span>
        )}
      </div>
    </div>
  )
}
