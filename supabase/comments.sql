-- جدول تعليقات الموقع. انسخي هذا كله والصقيه في SQL Editor في Supabase ثم اضغطي Run.
create table if not exists public.comments (
  id bigint generated always as identity primary key,
  slug text not null check (char_length(slug) between 1 and 100),
  name text not null check (char_length(btrim(name)) between 1 and 40),
  body text not null check (char_length(btrim(body)) between 1 and 1000),
  created_at timestamptz not null default now()
);

create index if not exists comments_slug_idx on public.comments (slug, created_at);

alter table public.comments enable row level security;

-- أي زائر يقرأ التعليقات ويضيف تعليقًا، ولا أحد يعدّل أو يحذف إلا صاحبة الموقع من لوحة Supabase
drop policy if exists "anyone can read comments" on public.comments;
create policy "anyone can read comments" on public.comments for select to anon using (true);
drop policy if exists "anyone can add a comment" on public.comments;
create policy "anyone can add a comment" on public.comments for insert to anon with check (true);

-- الزائر يرسل الاسم والنص ورابط المقال فقط؛ الرقم والتاريخ يضعهما الخادم
revoke insert, update, delete on public.comments from anon;
grant select on public.comments to anon;
grant insert (slug, name, body) on public.comments to anon;
