const BASE = '/api/v1'

export interface Influencer {
  id: string
  platform: string
  handle: string
  url: string
  bio_text: string | null
  follower_count: number | null
  created_at: string
}

export interface OutreachCampaign {
  id: string
  influencer_id: string
  status: string
  generated_message: string | null
  last_updated: string
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  getInfluencers: () =>
    request<Influencer[]>(`${BASE}/influencers`),

  discover: (niche: string, platform = 'tiktok') =>
    request<Influencer[]>(
      `${BASE}/discover?niche=${encodeURIComponent(niche)}&platform=${encodeURIComponent(platform)}`,
      { method: 'POST' },
    ),

  draftCampaign: (influencerId: string) =>
    request<OutreachCampaign>(
      `${BASE}/campaigns/${influencerId}/draft`,
      { method: 'POST' },
    ),
}
