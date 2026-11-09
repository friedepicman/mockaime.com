// Per-user record of which problems were answered right or wrong.
// Stored in user_profiles.problem_history and written only through the
// record_problem_results() Postgres function (see add_problem_history.sql).
// Skipped / blank problems are never recorded.
window.ProblemHistory = (function () {
  let history = {};
  let loadedFor = null;

  async function load(client, user) {
    history = {};
    loadedFor = null;
    if (!client || !user) return history;
    try {
      const { data, error } = await client
        .from('user_profiles')
        .select('problem_history')
        .eq('id', user.id)
        .maybeSingle();
      if (error) {
        console.warn('Could not load problem history:', error.message);
        return history;
      }
      history = (data && data.problem_history) || {};
      loadedFor = user.id;
    } catch (err) {
      console.warn('Could not load problem history:', err);
    }
    return history;
  }

  function get(problemId) {
    if (problemId === null || problemId === undefined) return null;
    return history[String(problemId)] || null;
  }

  // Update the local copy with an entry the server returned
  function set(problemId, entry) {
    if (problemId === null || problemId === undefined || !entry) return;
    history[String(problemId)] = entry;
  }

  // results: [{ id, correct: bool, override?: bool }]
  async function record(client, user, results) {
    if (!client || !user || !Array.isArray(results)) return;
    const clean = results
      .filter(r => r && r.id !== null && r.id !== undefined && typeof r.correct === 'boolean')
      .map(r => ({ id: r.id, correct: r.correct, override: !!r.override }));
    if (clean.length === 0) return;
    try {
      const { data, error } = await client.rpc('record_problem_results', { p_results: clean });
      if (error) {
        console.warn('Could not save problem history:', error.message);
        return;
      }
      if (data && loadedFor === user.id) Object.assign(history, data);
    } catch (err) {
      console.warn('Could not save problem history:', err);
    }
  }

  function formatDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d)) return '';
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  }

  // Small pill saying how the user did last time; '' if never attempted.
  function badgeHtml(problemId) {
    const entry = get(problemId);
    if (!entry) return '';
    const correct = entry.status === 'correct';
    const attempts = entry.attempts || 1;
    let title = `${correct ? 'Answered correctly' : 'Answered incorrectly'} last time` +
      (entry.last_at ? ` (${formatDate(entry.last_at)})` : '') +
      ` · ${attempts} attempt${attempts === 1 ? '' : 's'}`;
    if (!correct && entry.ever_correct) title += ' · solved it on an earlier attempt';
    const label = correct ? '✓ Solved before' : '✗ Missed before';
    return `<span class="history-badge ${correct ? 'history-correct' : 'history-incorrect'}" title="${title}">${label}</span>`;
  }

  function injectStyles() {
    if (document.getElementById('problem-history-styles')) return;
    const style = document.createElement('style');
    style.id = 'problem-history-styles';
    style.textContent = `
      .history-badge {
        display: inline-block;
        padding: 2px 10px;
        margin-left: 8px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        vertical-align: middle;
        white-space: nowrap;
        cursor: default;
      }
      .problem-meta .history-badge { margin-left: 0; padding: 4px 12px; font-size: 13px; }
      .history-badge.history-correct { background: #d4edda; color: #155724; }
      .history-badge.history-incorrect { background: #f8d7da; color: #721c24; }
      [data-theme="dark"] .history-badge.history-correct { background: rgba(40, 167, 69, 0.2); color: #7ee2a0; }
      [data-theme="dark"] .history-badge.history-incorrect { background: rgba(220, 53, 69, 0.2); color: #f5a3ab; }
    `;
    document.head.appendChild(style);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectStyles);
  } else {
    injectStyles();
  }

  // True if the user has answered this problem correctly before
  function solvedBefore(problemId) {
    const entry = get(problemId);
    return !!(entry && entry.ever_correct);
  }

  return { load, get, set, record, badgeHtml, solvedBefore };
})();
