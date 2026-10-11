-- جدول تقييمات الموقع («قيّمنا» في الصفحة الرئيسية).
-- انسخي هذا كله والصقيه في SQL Editor في Supabase ثم اضغطي Run (مرة واحدة فقط).
create table if not exists public.ratings (
  id bigint generated always as identity primary key,
  stars smallint not null check (stars between 1 and 5),
  name text check (name is null or char_length(btrim(name)) between 1 and 40),
  body text check (body is null or char_length(btrim(body)) between 1 and 500),
  lang text not null default 'ar' check (lang in ('ar', 'en')),
  created_at timestamptz not null default now()
);

create index if not exists ratings_created_idx on public.ratings (created_at desc);

alter table public.ratings enable row level security;

-- الزوّار يرون التقييمات الإيجابية فقط (٤ أو ٥ نجوم ومعها تعليق)؛ السلبية لا تُقرأ من الموقع أبدًا،
-- وتراها صاحبة الموقع وحدها من لوحة Supabase (وتصلها كلها على البريد أيضًا)
drop policy if exists "anyone can read positive ratings" on public.ratings;
create policy "anyone can read positive ratings" on public.ratings
  for select to anon using (stars >= 4 and body is not null);
drop policy if exists "anyone can add a rating" on public.ratings;
create policy "anyone can add a rating" on public.ratings for insert to anon with check (true);

-- الزائر يرسل النجوم والاسم والتعليق واللغة فقط؛ الرقم والتاريخ يضعهما الخادم
revoke insert, update, delete on public.ratings from anon;
grant select on public.ratings to anon;
grant insert (stars, name, body, lang) on public.ratings to anon;
