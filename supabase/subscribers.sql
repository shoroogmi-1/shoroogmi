-- جدول القائمة البريدية للموقع («القائمة البريدية» في الرئيسية وآخر كل مقال).
-- انسخي هذا كله والصقيه في SQL Editor في Supabase ثم اضغطي Run (مرة واحدة فقط).
create table if not exists public.subscribers (
  id bigint generated always as identity primary key,
  email text not null check (char_length(email) between 5 and 254 and email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  lang text not null default 'ar' check (lang in ('ar', 'en')),
  created_at timestamptz not null default now()
);

-- البريد الواحد لا يُسجَّل مرتين (بغض النظر عن الحروف الكبيرة والصغيرة)
create unique index if not exists subscribers_email_idx on public.subscribers (lower(email));

alter table public.subscribers enable row level security;

-- الزائر يستطيع الاشتراك فقط؛ لا يستطيع أحد من الموقع قراءة القائمة أو تعديلها.
-- القائمة تراها صاحبة الموقع وحدها من لوحة Supabase (Table Editor ← subscribers ← Export to CSV).
drop policy if exists "anyone can subscribe" on public.subscribers;
create policy "anyone can subscribe" on public.subscribers for insert to anon with check (true);

revoke select, insert, update, delete on public.subscribers from anon;
grant insert (email, lang) on public.subscribers to anon;
