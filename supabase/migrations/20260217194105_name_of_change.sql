
  create table "public"."influencer" (
    "id" uuid not null default gen_random_uuid(),
    "platform" text not null,
    "handle" text not null,
    "url" text not null,
    "bio_text" text,
    "follower_count" integer,
    "created_at" timestamp with time zone not null default now()
      );



  create table "public"."outreach_campaign" (
    "id" uuid not null default gen_random_uuid(),
    "influencer_id" uuid not null,
    "status" text not null default 'discovered'::text,
    "generated_message" text,
    "last_updated" timestamp with time zone not null default now()
      );


CREATE INDEX idx_influencer_handle ON public.influencer USING btree (handle);

CREATE INDEX idx_outreach_influencer_id ON public.outreach_campaign USING btree (influencer_id);

CREATE UNIQUE INDEX influencer_handle_key ON public.influencer USING btree (handle);

CREATE UNIQUE INDEX influencer_pkey ON public.influencer USING btree (id);

CREATE UNIQUE INDEX outreach_campaign_pkey ON public.outreach_campaign USING btree (id);

alter table "public"."influencer" add constraint "influencer_pkey" PRIMARY KEY using index "influencer_pkey";

alter table "public"."outreach_campaign" add constraint "outreach_campaign_pkey" PRIMARY KEY using index "outreach_campaign_pkey";

alter table "public"."influencer" add constraint "influencer_handle_key" UNIQUE using index "influencer_handle_key";

alter table "public"."outreach_campaign" add constraint "outreach_campaign_influencer_id_fkey" FOREIGN KEY (influencer_id) REFERENCES public.influencer(id) ON DELETE CASCADE not valid;

alter table "public"."outreach_campaign" validate constraint "outreach_campaign_influencer_id_fkey";

grant delete on table "public"."influencer" to "anon";

grant insert on table "public"."influencer" to "anon";

grant references on table "public"."influencer" to "anon";

grant select on table "public"."influencer" to "anon";

grant trigger on table "public"."influencer" to "anon";

grant truncate on table "public"."influencer" to "anon";

grant update on table "public"."influencer" to "anon";

grant delete on table "public"."influencer" to "authenticated";

grant insert on table "public"."influencer" to "authenticated";

grant references on table "public"."influencer" to "authenticated";

grant select on table "public"."influencer" to "authenticated";

grant trigger on table "public"."influencer" to "authenticated";

grant truncate on table "public"."influencer" to "authenticated";

grant update on table "public"."influencer" to "authenticated";

grant delete on table "public"."influencer" to "service_role";

grant insert on table "public"."influencer" to "service_role";

grant references on table "public"."influencer" to "service_role";

grant select on table "public"."influencer" to "service_role";

grant trigger on table "public"."influencer" to "service_role";

grant truncate on table "public"."influencer" to "service_role";

grant update on table "public"."influencer" to "service_role";

grant delete on table "public"."outreach_campaign" to "anon";

grant insert on table "public"."outreach_campaign" to "anon";

grant references on table "public"."outreach_campaign" to "anon";

grant select on table "public"."outreach_campaign" to "anon";

grant trigger on table "public"."outreach_campaign" to "anon";

grant truncate on table "public"."outreach_campaign" to "anon";

grant update on table "public"."outreach_campaign" to "anon";

grant delete on table "public"."outreach_campaign" to "authenticated";

grant insert on table "public"."outreach_campaign" to "authenticated";

grant references on table "public"."outreach_campaign" to "authenticated";

grant select on table "public"."outreach_campaign" to "authenticated";

grant trigger on table "public"."outreach_campaign" to "authenticated";

grant truncate on table "public"."outreach_campaign" to "authenticated";

grant update on table "public"."outreach_campaign" to "authenticated";

grant delete on table "public"."outreach_campaign" to "service_role";

grant insert on table "public"."outreach_campaign" to "service_role";

grant references on table "public"."outreach_campaign" to "service_role";

grant select on table "public"."outreach_campaign" to "service_role";

grant trigger on table "public"."outreach_campaign" to "service_role";

grant truncate on table "public"."outreach_campaign" to "service_role";

grant update on table "public"."outreach_campaign" to "service_role";


