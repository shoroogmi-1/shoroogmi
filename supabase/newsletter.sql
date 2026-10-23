-- الإرسال التلقائي للمقالات الجديدة إلى القائمة البريدية.
-- انسخي هذا كله والصقيه في SQL Editor في Supabase ثم اضغطي Run (مرة واحدة فقط، بعد subscribers.sql).
-- في النتيجة يظهر «رمز الإرسال»: انسخيه وضعيه في GitHub باسم NEWSLETTER_TOKEN (ولا ترسليه لأحد).

create schema if not exists private;

-- رمز سري يثبت أن الطلب من أداة الإرسال في GitHub
create table if not exists private.newsletter_config (
  id int primary key default 1 check (id = 1),
  token text not null default replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '')
);
insert into private.newsletter_config (id) values (1) on conflict (id) do nothing;

-- لكل مشترك رابط إلغاء اشتراك خاص به
alter table public.subscribers add column if not exists unsub_token uuid not null default gen_random_uuid();

-- قائمة المشتركين لأداة الإرسال فقط (بالرمز السري)
create or replace function public.newsletter_recipients(p_token text)
returns table (email text, lang text, unsub_token uuid)
language plpgsql stable security definer set search_path = public, private as $$
begin
  if not exists (select 1 from private.newsletter_config c where c.token = p_token) then
    raise exception 'wrong newsletter token';  -- رمز خاطئ: خطأ صريح بدل قائمة فارغة
  end if;
  return query select s.email, s.lang, s.unsub_token from public.subscribers s order by s.id;
end;
$$;
revoke all on function public.newsletter_recipients(text) from public;
grant execute on function public.newsletter_recipients(text) to anon;

-- إلغاء الاشتراك من الرابط في آخر كل رسالة
create or replace function public.unsubscribe(p_token uuid)
returns boolean language plpgsql security definer set search_path = public as $$
begin
  delete from public.subscribers where unsub_token = p_token;
  return found;
end;
$$;
revoke all on function public.unsubscribe(uuid) from public;
grant execute on function public.unsubscribe(uuid) to anon;

select token as "رمز الإرسال: انسخيه إلى GitHub باسم NEWSLETTER_TOKEN" from private.newsletter_config;
