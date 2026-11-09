-- ============================================================================
-- Repeat solves give 1/4 XP, and "I was correct" XP is computed on the server.
-- Run AFTER add_problem_history.sql. Safe to re-run.
--
-- Run this at the same time you push the site: the new practice page calls
-- override_practice_xp(p_problem_id), and the old page's override button
-- (which sent its own XP amount) stops working once this runs.
--
-- Changes:
--  * award_practice_xp: if the user has solved this problem before (in practice
--    or a mock), a correct answer gives floor(XP / 4). Wrong-answer penalties
--    are unchanged. The result is saved to problem_history in the same call.
--  * award_practice_xp now reads the problem's difficulty and topic from the
--    problems table instead of trusting what the browser sends (the browser's
--    values are only used if the problem has none stored).
--  * override_practice_xp(p_problem_id): replaces the old version that took an
--    XP amount from the browser (anyone could give themselves any XP). It now
--    undoes the last practice result for that problem and awards what a
--    correct answer would have given, once.
-- ============================================================================

-- Shared: add XP to one category column and to xp_general. Not callable from the API.
create or replace function public.apply_practice_xp(p_problem_type text, p_delta integer)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_problem_type = 'algebra' then
    update user_profiles
       set xp_algebra = greatest(0, xp_algebra + p_delta),
           xp_general = greatest(0, xp_general + p_delta)
     where id = auth.uid();
  elsif p_problem_type = 'geometry' then
    update user_profiles
       set xp_geometry = greatest(0, xp_geometry + p_delta),
           xp_general  = greatest(0, xp_general + p_delta)
     where id = auth.uid();
  elsif p_problem_type = 'number_theory' then
    update user_profiles
       set xp_number_theory = greatest(0, xp_number_theory + p_delta),
           xp_general       = greatest(0, xp_general + p_delta)
     where id = auth.uid();
  elsif p_problem_type = 'counting' then
    update user_profiles
       set xp_counting = greatest(0, xp_counting + p_delta),
           xp_general  = greatest(0, xp_general + p_delta)
     where id = auth.uid();
  else
    update user_profiles
       set xp_general = greatest(0, xp_general + p_delta)
     where id = auth.uid();
  end if;
end;
$$;

revoke all on function public.apply_practice_xp(text, integer) from public, anon, authenticated;


-- Practice submit ------------------------------------------------------------
create or replace function public.award_practice_xp(p_problem_id integer, p_user_answer text, p_problem_type text, p_problem_difficulty numeric)
returns jsonb
language plpgsql
security definer
set search_path = public
as $function$
declare
  v_uid uuid := auth.uid();
  v_key text := p_problem_id::text;
  v_aime_answer int;
  v_answer text;
  v_source text;
  v_type_db text;
  v_diff_db text;
  v_type text;
  v_diff numeric;
  v_correct_answer text;
  v_is_amc boolean;
  v_solved_before boolean := false;
  v_history jsonb;
  is_correct boolean;
  xp_reward int;
  xp_change int;
  user_current_xp int;
  current_level int;
  penalty_base int;
  penalty_mult numeric;
begin
  -- Get the problem's answers and source
  select aime_answer, answer, source, type::text, difficulty::text
    into v_aime_answer, v_answer, v_source, v_type_db, v_diff_db
    from problems
   where id = p_problem_id;

  if not found then
    raise exception 'Problem % not found', p_problem_id;
  end if;

  -- Use the stored topic and difficulty; the browser's values are only a fallback
  v_type := coalesce(nullif(trim(v_type_db), ''), p_problem_type);
  v_diff := case when v_diff_db ~ '^\s*[0-9]+(\.[0-9]+)?\s*$' then trim(v_diff_db)::numeric
                 else p_problem_difficulty end;

  -- Has this user solved it before? (practice or mock)
  if v_uid is not null then
    select coalesce((problem_history -> v_key ->> 'ever_correct')::boolean, false)
      into v_solved_before
      from user_profiles
     where id = v_uid;
    v_solved_before := coalesce(v_solved_before, false);
  end if;

  -- Check if it's an AMC problem (uses letter answers)
  v_is_amc := (v_source ilike '%AMC 8%' or v_source ilike '%AMC 10%' or v_source ilike '%AMC 12%'
               or v_source ilike '%AMC8%' or v_source ilike '%AMC10%' or v_source ilike '%AMC12%');

  if v_is_amc then
    v_correct_answer := upper(trim(coalesce(v_answer, '')));
    is_correct := (upper(trim(p_user_answer)) = v_correct_answer);
  else
    if v_aime_answer is not null then
      v_correct_answer := cast(v_aime_answer % 1000 as text);
    else
      v_correct_answer := coalesce(v_answer, '');
    end if;
    is_correct := (p_user_answer = v_correct_answer);
  end if;
  is_correct := coalesce(is_correct, false);

  -- XP reward based on difficulty
  xp_reward := case
    when v_diff <= 1 then 5
    when v_diff <= 1.5 then 10
    when v_diff <= 2 then 15
    when v_diff <= 2.5 then 25
    when v_diff <= 3 then 35
    when v_diff <= 3.5 then 50
    when v_diff <= 4 then 70
    when v_diff <= 4.5 then 95
    when v_diff <= 5 then 125
    when v_diff <= 5.5 then 160
    when v_diff <= 6 then 195
    when v_diff <= 6.5 then 235
    when v_diff <= 7 then 280
    when v_diff <= 7.5 then 330
    when v_diff <= 8 then 380
    when v_diff <= 8.5 then 430
    when v_diff <= 9 then 460
    when v_diff <= 9.5 then 480
    else 500
  end;

  if is_correct then
    -- Already solved before: floor of a quarter of the XP
    xp_change := case when v_solved_before then xp_reward / 4 else xp_reward end;
  else
    if v_type = 'algebra' then
      select coalesce(xp_algebra, 0) into user_current_xp from user_profiles where id = v_uid;
    elsif v_type = 'geometry' then
      select coalesce(xp_geometry, 0) into user_current_xp from user_profiles where id = v_uid;
    elsif v_type = 'number_theory' then
      select coalesce(xp_number_theory, 0) into user_current_xp from user_profiles where id = v_uid;
    elsif v_type = 'counting' then
      select coalesce(xp_counting, 0) into user_current_xp from user_profiles where id = v_uid;
    else
      select coalesce(xp_general, 0) into user_current_xp from user_profiles where id = v_uid;
    end if;
    user_current_xp := coalesce(user_current_xp, 0);

    current_level := case
      when user_current_xp < 500 then greatest(1, 1 + user_current_xp / 50)
      when user_current_xp < 1500 then 10 + (user_current_xp - 500) / 100
      when user_current_xp < 3000 then 20 + (user_current_xp - 1500) / 150
      when user_current_xp < 5000 then 30 + (user_current_xp - 3000) / 200
      when user_current_xp < 7500 then 40 + (user_current_xp - 5000) / 250
      when user_current_xp < 11000 then 50 + (user_current_xp - 7500) / 350
      when user_current_xp < 15500 then 60 + (user_current_xp - 11000) / 450
      when user_current_xp < 21000 then 70 + (user_current_xp - 15500) / 550
      when user_current_xp < 28000 then 80 + (user_current_xp - 21000) / 700
      when user_current_xp < 37000 then 90 + (user_current_xp - 28000) / 900
      else least(105, 100 + (user_current_xp - 37000) / 2500)
    end;

    if current_level < 50 then
      xp_change := 0;
    else
      penalty_base := case
        when current_level <= 60 then 10
        when current_level <= 70 then 25
        when current_level <= 80 then 60
        when current_level <= 90 then 150
        when current_level <= 100 then 300
        else 450
      end;
      penalty_mult := case
        when v_diff <= 2 then 1.5
        when v_diff <= 3.5 then 1.0
        when v_diff <= 5 then 0.7
        when v_diff <= 6.5 then 0.5
        when v_diff <= 8 then 0.3
        else 0.2
      end;
      xp_change := -round(penalty_base * penalty_mult);
    end if;
  end if;

  perform apply_practice_xp(v_type, xp_change);

  -- Save to problem history, plus what's needed to undo it with "I was correct"
  if v_uid is not null then
    perform record_problem_results(jsonb_build_array(jsonb_build_object('id', p_problem_id, 'correct', is_correct)));
    update user_profiles
       set problem_history = jsonb_set(problem_history, array[v_key],
             (problem_history -> v_key) || jsonb_build_object(
               'last_xp', xp_change,
               'last_full_xp', xp_reward,
               'last_repeat', v_solved_before,
               'last_type', v_type))
     where id = v_uid
       and problem_history ? v_key;
    select problem_history -> v_key into v_history from user_profiles where id = v_uid;
  end if;

  return jsonb_build_object(
    'correct', is_correct,
    'xp_change', xp_change,
    'correct_answer', v_correct_answer,
    'repeat', v_solved_before,
    'full_xp', xp_reward,
    'history', v_history
  );
end;
$function$;


-- "I was correct" ------------------------------------------------------------
drop function if exists public.override_practice_xp(text, integer);

create or replace function public.override_practice_xp(p_problem_id integer)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_uid    uuid := auth.uid();
  v_key    text := p_problem_id::text;
  v_entry  jsonb;
  v_reward int;
  v_amount int;
  v_repeat boolean;
begin
  if v_uid is null then
    raise exception 'Not authenticated';
  end if;

  select problem_history -> v_key into v_entry
    from user_profiles where id = v_uid for update;

  -- Only the latest practice result can be overridden, and only once
  if v_entry is null
     or v_entry ->> 'status' is distinct from 'incorrect'
     or v_entry -> 'last_full_xp' is null then
    raise exception 'Nothing to override for this problem';
  end if;

  v_repeat := coalesce((v_entry ->> 'last_repeat')::boolean, false);
  v_reward := case when v_repeat then (v_entry ->> 'last_full_xp')::int / 4
                   else (v_entry ->> 'last_full_xp')::int end;
  -- Undo the penalty (last_xp <= 0) and give the correct-answer XP
  v_amount := v_reward - coalesce((v_entry ->> 'last_xp')::int, 0);

  perform apply_practice_xp(v_entry ->> 'last_type', v_amount);
  perform record_problem_results(jsonb_build_array(jsonb_build_object('id', p_problem_id, 'correct', true, 'override', true)));

  update user_profiles
     set problem_history = jsonb_set(problem_history, array[v_key],
           (problem_history -> v_key) || jsonb_build_object('last_xp', v_reward))
   where id = v_uid;

  return jsonb_build_object(
    'xp_change', v_amount,
    'repeat', v_repeat,
    'history', (select problem_history -> v_key from user_profiles where id = v_uid)
  );
end;
$$;

revoke all on function public.override_practice_xp(integer) from public, anon;
grant execute on function public.override_practice_xp(integer) to authenticated;
