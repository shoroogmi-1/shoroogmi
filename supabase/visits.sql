-- إحصاءات الزوار (زوار الموقع + القرّاء الدائمون) في Supabase بدل العدّاد القديم البطيء.
-- انسخي هذا كله والصقيه في SQL Editor في Supabase ثم اضغطي Run (مرة واحدة فقط).
-- الأرقام القديمة محفوظة: ٣٩٤ زائرًا و١١ قارئًا دائمًا (من العدّاد القديم يوم ٢٣ نوفمبر ٢٠٢٦)، والجديد يُضاف إليها.

create schema if not exists private;

-- كل متصفح = زائر برقم عشوائي (لا اسم ولا بريد ولا عنوان)
create table if not exists private.visitors (
  id uuid primary key,
  first_day date not null,
  legacy_returning boolean not null default false,  -- حُسب قارئًا دائمًا في العدّاد القديم
  created_at timestamptz not null default now()
);
-- يوم واحد لكل زيارة: من زار في يومين مختلفين أو أكثر فهو قارئ دائم
create table if not exists private.visits (
  visitor uuid not null references private.visitors (id) on delete cascade,
  day date not null,
  primary key (visitor, day)
);

create table if not exists private.stats_baseline (
  id int primary key default 1 check (id = 1),
  visitors int not null,
  regulars int not null,
  since date not null default current_date
);
insert into private.stats_baseline (id, visitors, regulars) values (1, 394, 11) on conflict (id) do nothing;

-- تسجيل زيارة اليوم (مرة في اليوم لكل متصفح)
create or replace function public.log_visit(p_id uuid, p_first date default null, p_legacy_returning boolean default false)
returns void language plpgsql security definer set search_path = private as $$
declare
  f date := least(greatest(coalesce(p_first, current_date), date '2026-01-01'), current_date);
begin
  insert into private.visitors (id, first_day, legacy_returning) values (p_id, f, coalesce(p_legacy_returning, false))
  on conflict (id) do nothing;
  insert into private.visits (visitor, day) values (p_id, current_date) on conflict do nothing;
  -- زائر قديم (من قبل التحويل): نسجّل يوم أول زيارته ليُعرف أنه رجع
  if f < current_date then
    insert into private.visits (visitor, day) values (p_id, f) on conflict do nothing;
  end if;
end;
$$;
revoke all on function public.log_visit(uuid, date, boolean) from public;
grant execute on function public.log_visit(uuid, date, boolean) to anon;

-- الأرقام المعروضة في الصفحة الرئيسية
create or replace function public.site_stats()
returns table (visitors bigint, regulars bigint)
language sql stable security definer set search_path = private as $$
  select
    b.visitors + (select count(*) from private.visitors v where v.first_day >= b.since),
    b.regulars + (select count(*) from (
      select v.id from private.visitors v join private.visits d on d.visitor = v.id
      where not v.legacy_returning group by v.id having count(*) >= 2) r)
  from private.stats_baseline b;
$$;
revoke all on function public.site_stats() from public;
grant execute on function public.site_stats() to anon;

select * from public.site_stats();
