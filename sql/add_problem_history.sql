-- ============================================================================
-- Problem history: remember which problems each user got right or wrong.
-- Run once in the Supabase SQL editor. Safe to re-run.
--
-- user_profiles.problem_history is a jsonb object keyed by problem id:
--
--   {
--     "1234": {
--       "status": "correct" | "incorrect",  -- result of the most recent attempt
--       "ever_correct": true,               -- solved it at least once (for future XP rules)
--       "attempts": 2,                      -- graded attempts (skips/blank answers are never recorded)
--       "correct_count": 1,
--       "overridden": true,                 -- present when the latest result came from "I was correct"
--       "first_at": "2026-11-09T02:30:00Z",
--       "last_at":  "2026-11-10T18:02:11Z"
--     },
--     ...
--   }
--
-- Only the record_problem_results() function below can change this column.
-- A browser that tries to write it directly (insert/update through the API)
-- has its change silently dropped by the trigger, so later XP logic can trust it.
-- ============================================================================

-- 1. Column ------------------------------------------------------------------
alter table public.user_profiles
  add column if not exists problem_history jsonb not null default '{}'::jsonb;


-- 2. Write function ----------------------------------------------------------
-- p_results: json array of { "id": <problem id>, "correct": true|false, "override": true|false }
--   override = true  -> the user pressed "I was correct": flip the latest result to
--                       correct without counting another attempt.
-- Returns the updated entries, keyed by problem id.
create or replace function public.record_problem_results(p_results jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_uid      uuid := auth.uid();
  v_now      timestamptz := now();
  v_hist     jsonb;
  v_item     jsonb;
  v_key      text;
  v_correct  boolean;
  v_override boolean;
  v_prev     jsonb;
  v_entry    jsonb;
  v_changed  jsonb := '{}'::jsonb;
begin
  if v_uid is null then
    raise exception 'Not authenticated';
  end if;
  if p_results is null or jsonb_typeof(p_results) <> 'array' then
    raise exception 'p_results must be a JSON array';
  end if;
  if jsonb_array_length(p_results) > 100 then
    raise exception 'Too many results in one call (max 100)';
  end if;

  -- Make sure the profile row exists (ignored if other required columns block it).
  begin
    insert into user_profiles (id) values (v_uid) on conflict (id) do nothing;
  exception when others then
    null;
  end;

  select coalesce(problem_history, '{}'::jsonb)
    into v_hist
    from user_profiles
   where id = v_uid
   for update;

  if not found then
    return '{}'::jsonb;
  end if;

  for v_item in select value from jsonb_array_elements(p_results) loop
    v_key := v_item->>'id';
    continue when v_key is null or v_key !~ '^[0-9]+$';
    continue when not exists (select 1 from problems where id = v_key::bigint);

    v_correct := (v_item->>'correct')::boolean;
    continue when v_correct is null;
    v_override := coalesce((v_item->>'override')::boolean, false);
    v_prev := v_hist->v_key;

    if v_override then
      v_entry := coalesce(v_prev, jsonb_build_object(
                   'attempts', 1, 'correct_count', 0, 'first_at', to_jsonb(v_now)))
              || jsonb_build_object(
                   'status', 'correct',
                   'ever_correct', true,
                   'overridden', true,
                   'correct_count', coalesce((v_prev->>'correct_count')::int, 0)
                                    + case when v_prev->>'status' = 'correct' then 0 else 1 end,
                   'last_at', to_jsonb(v_now));
    else
      v_entry := jsonb_build_object(
        'status',        case when v_correct then 'correct' else 'incorrect' end,
        'ever_correct',  coalesce((v_prev->>'ever_correct')::boolean, false) or v_correct,
        'attempts',      coalesce((v_prev->>'attempts')::int, 0) + 1,
        'correct_count', coalesce((v_prev->>'correct_count')::int, 0) + case when v_correct then 1 else 0 end,
        'first_at',      coalesce(v_prev->'first_at', to_jsonb(v_now)),
        'last_at',       to_jsonb(v_now));
    end if;

    v_hist    := jsonb_set(v_hist, array[v_key], v_entry, true);
    v_changed := v_changed || jsonb_build_object(v_key, v_entry);
  end loop;

  update user_profiles set problem_history = v_hist where id = v_uid;
  return v_changed;
end;
$$;

revoke all on function public.record_problem_results(jsonb) from public, anon;
grant execute on function public.record_problem_results(jsonb) to authenticated;


-- 3. Block direct writes from the browser ------------------------------------
-- record_problem_results runs as its owner (security definer), so it passes.
-- Anything coming straight from the API as anon/authenticated keeps the old value.
create or replace function public.protect_problem_history()
returns trigger
language plpgsql
as $$
begin
  if current_user in ('anon', 'authenticated') then
    if tg_op = 'INSERT' then
      new.problem_history := '{}'::jsonb;
    elsif new.problem_history is distinct from old.problem_history then
      new.problem_history := old.problem_history;
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists protect_problem_history on public.user_profiles;
create trigger protect_problem_history
  before insert or update on public.user_profiles
  for each row execute function public.protect_problem_history();


-- 4. Reading it (RLS check) --------------------------------------------------
-- The site reads problem_history with a normal select on the user's own row,
-- the same way it already reads xp_* columns, so no new policy is needed if
-- users can already select their own profile. Check what's there with:
--
--   select policyname, cmd, roles, qual
--     from pg_policies
--    where schemaname = 'public' and tablename = 'user_profiles';
--
-- If a SELECT policy lets *everyone* read user_profiles (e.g. qual = true for a
-- leaderboard), every user's problem history becomes readable too. In that case
-- consider limiting that policy, or exposing only the leaderboard columns via a view.
