import { supabase } from './supabaseClient'

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
  const { data: { session } } = await supabase.auth.getSession()
  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string> ?? {}),
  }
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }

  const res = await fetch(url, { ...options, headers })
  if (res.status === 401) {
    await supabase.auth.signOut()
    window.location.href = '/login'
    throw new Error('Session expired')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export interface InfluencerNote {
  id: string
  influencer_id: string
  body: string
  created_at: string
}

export interface Tag {
  id: string
  name: string
}

export interface InfluencerDetail {
  influencer: Influencer
  campaigns: OutreachCampaign[]
  notes: InfluencerNote[]
  tags: Tag[]
}

export interface InfluencerFilters {
  platform?: string
  min_followers?: number
  max_followers?: number
  tag?: string
}

export interface UserSettings {
  id: string
  brand_description: string | null
  updated_at: string
}

export interface DashboardData {
  total_influencers: number
  total_campaigns: number
  campaigns_by_status: Record<string, number>
  response_rate: number
  recent_campaigns: CampaignWithInfluencer[]
}

export const api = {
  getDashboard: () =>
    request<DashboardData>(`${BASE}/dashboard`),

  getInfluencers: (filters?: InfluencerFilters) => {
    const params = new URLSearchParams()
    if (filters?.platform) params.set('platform', filters.platform)
    if (filters?.min_followers != null) params.set('min_followers', String(filters.min_followers))
    if (filters?.max_followers != null) params.set('max_followers', String(filters.max_followers))
    if (filters?.tag) params.set('tag', filters.tag)
    const qs = params.toString()
    return request<Influencer[]>(`${BASE}/influencers${qs ? `?${qs}` : ''}`)
  },

  getInfluencerDetail: (influencerId: string) =>
    request<InfluencerDetail>(`${BASE}/influencers/${influencerId}`),

  addNote: (influencerId: string, body: string) =>
    request<InfluencerNote>(
      `${BASE}/influencers/${influencerId}/notes`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body }),
      },
    ),

  deleteNote: (influencerId: string, noteId: string) =>
    request<{ ok: boolean }>(
      `${BASE}/influencers/${influencerId}/notes/${noteId}`,
      { method: 'DELETE' },
    ),

  getTags: () =>
    request<Tag[]>(`${BASE}/tags`),

  addTag: (influencerId: string, name: string) =>
    request<Tag>(
      `${BASE}/influencers/${influencerId}/tags`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      },
    ),

  removeTag: (influencerId: string, tagId: string) =>
    request<{ ok: boolean }>(
      `${BASE}/influencers/${influencerId}/tags/${tagId}`,
      { method: 'DELETE' },
    ),

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
