// Loads every row of the problems table in pages, retrying a page that fails
// instead of silently stopping (which used to drop all later problems).
// Returns { problems, complete } — complete is false if a page still failed
// after all retries, so the page can warn the user.
window.fetchAllProblems = async function (client, options = {}) {
  const pageSize = options.pageSize || 1000;
  const maxRetries = options.maxRetries ?? 3;
  const onProgress = options.onProgress || (() => {});
  let columns = options.columns || '*';

  const problems = [];
  let from = 0;

  while (true) {
    let data = null;
    let lastError = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      const res = await client
        .from('problems')
        .select(columns)
        .order('id')
        .range(from, from + pageSize - 1);

      if (!res.error) {
        data = res.data || [];
        break;
      }

      lastError = res.error;
      // A listed column doesn't exist: fall back to all columns and retry right away
      if (res.error.code === '42703' && columns !== '*') {
        console.warn('Problem loader: column missing, loading all columns instead', res.error.message);
        columns = '*';
        attempt--;
        continue;
      }
      if (attempt < maxRetries) {
        await new Promise(r => setTimeout(r, 500 * Math.pow(2, attempt)));
      }
    }

    if (data === null) {
      console.error(`Problem loader: rows from ${from} failed after ${maxRetries + 1} tries`, lastError);
      return { problems, complete: false };
    }
    if (data.length === 0) break;

    problems.push(...data);
    // Advance by what actually came back, in case the server caps page size below pageSize
    from += data.length;
    onProgress(problems.length);
  }

  return { problems, complete: true };
};
