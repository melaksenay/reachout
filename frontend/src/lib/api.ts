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
  status_updated_at: string
  notes: string | null
  last_updated: string
}

export interface CampaignWithInfluencer extends OutreachCampaign {
  influencer_handle: string
  influencer_platform: string
  influencer_url: string
  influencer_follower_count: number | null
}

export const PIPELINE_STAGES = [
  'discovered', 'drafted', 'sent', 'replied',
  'negotiating', 'closed', 'rejected',
] as const
export type PipelineStage = typeof PIPELINE_STAGES[number]

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export interface UserSettings {
  id: string
  brand_description: string | null
  updated_at: string
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

  getCampaigns: (status?: string) =>
    request<CampaignWithInfluencer[]>(
      `${BASE}/campaigns${status ? `?status=${status}` : ''}`,
    ),

  updateCampaignStatus: (campaignId: string, status: PipelineStage) =>
    request<OutreachCampaign>(
      `${BASE}/campaigns/${campaignId}/status`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      },
    ),

  updateCampaignNotes: (campaignId: string, notes: string) =>
    request<OutreachCampaign>(
      `${BASE}/campaigns/${campaignId}/notes`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes }),
      },
    ),

  updateCampaignMessage: (campaignId: string, message: string) =>
    request<OutreachCampaign>(
      `${BASE}/campaigns/${campaignId}/message`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ generated_message: message }),
      },
    ),

  getSettings: () =>
    request<UserSettings>(`${BASE}/settings`),

  updateSettings: (brandDescription: string) =>
    request<UserSettings>(
      `${BASE}/settings`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_description: brandDescription }),
      },
    ),
}
