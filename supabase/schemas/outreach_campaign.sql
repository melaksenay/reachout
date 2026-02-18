CREATE TABLE public.outreach_campaign (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_id UUID NOT NULL REFERENCES public.influencer(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'discovered',
    generated_message TEXT,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create an index on the foreign key to speed up database joins
CREATE INDEX idx_outreach_influencer_id ON public.outreach_campaign(influencer_id);
