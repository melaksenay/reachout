CREATE TABLE public.influencer (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    handle TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    bio_text TEXT,
    follower_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- index on the handle for faster lookups during API calls
CREATE INDEX idx_influencer_handle ON public.influencer(handle);