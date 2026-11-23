-- الردود على التعليقات + ردّ الكاتبة الموثّق باسمها (بلا شارة ولا إطار).
-- انسخي هذا كله والصقيه في SQL Editor في Supabase ثم اضغطي Run (مرة واحدة فقط، بعد comments.sql).
-- في النتيجة يظهر «رمز الكاتبة»: افتحي به الرابط المكتوب في النتيجة مرة واحدة من جهازك، ولا ترسليه لأحد.

-- ١) كل تعليق قد يكون ردًّا على تعليق آخر، وردود الكاتبة معلَّمة
alter table public.comments add column if not exists parent_id bigint references public.comments (id) on delete cascade;
alter table public.comments add column if not exists is_author boolean not null default false;
create index if not exists comments_parent_idx on public.comments (parent_id);

-- الزائر يستطيع الرد على تعليق (يرسل رقمه)، لكنه لا يستطيع أبدًا وضع علامة ردّ الكاتبة
grant insert (slug, name, body, parent_id) on public.comments to anon;

-- ٢) رمز سري يثبت أن الرد من الكاتبة نفسها
create schema if not exists private;
create table if not exists private.author_config (
  id int primary key default 1 check (id = 1),
  token text not null default replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '')
);
insert into private.author_config (id) values (1) on conflict (id) do nothing;

-- ٣) ردّ الكاتبة: يقبل فقط مع الرمز الصحيح
create or replace function public.author_reply(p_token text, p_parent bigint, p_body text, p_name text default 'شروق المحمادي')
returns public.comments
language plpgsql security definer set search_path = public, private as $$
declare
  parent public.comments;
  saved public.comments;
begin
  if not exists (select 1 from private.author_config c where c.token = p_token) then
    raise exception 'wrong author token';
  end if;
  select * into parent from public.comments where id = p_parent;
  if not found then
    raise exception 'comment not found';
  end if;
  insert into public.comments (slug, name, body, parent_id, is_author)
  values (parent.slug, p_name, btrim(p_body), coalesce(parent.parent_id, parent.id), true)
  returning * into saved;
  return saved;
end;
$$;
revoke all on function public.author_reply(text, bigint, text, text) from public;
grant execute on function public.author_reply(text, bigint, text, text) to anon;

-- ٤) للتأكد من الرمز (يظهر زر «ردّ» للكاتبة فقط إن كان الرمز صحيحًا)
create or replace function public.is_author_token(p_token text)
returns boolean language sql stable security definer set search_path = private as $$
  select exists (select 1 from private.author_config c where c.token = p_token);
$$;
revoke all on function public.is_author_token(text) from public;
grant execute on function public.is_author_token(text) to anon;

select 'https://shoroogmi.com/?author=' || token as "رابط الكاتبة: افتحيه مرة واحدة من جوالك/الآيباد ولا ترسليه لأحد"
from private.author_config;
