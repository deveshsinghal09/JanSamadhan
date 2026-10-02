export const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

// Retry only reads: replaying a submission could create a duplicate complaint.
export async function api(path, options = {}, dependencies = {}) {
 const request = dependencies.fetch || fetch;
 const delay = dependencies.wait || wait;
 const method = (options.method || 'GET').toUpperCase();
 const attempts = method === 'GET' && !options.signal ? 4 : 1;
 for (let attempt = 0; attempt < attempts; attempt++) {
  let response;
  try {
   response = await request('/api' + path, {
    ...options,
    signal: options.signal || AbortSignal.timeout(method === 'GET' ? 20000 : 90000),
    headers: options.body instanceof FormData ? options.headers : {'Content-Type': 'application/json', ...options.headers},
   });
  } catch (cause) {
   if (attempt + 1 < attempts) { await delay(2000 * 2 ** attempt); continue; }
   throw new Error('The server is taking longer to respond. Please try again shortly.', {cause});
  }
  if ([502, 503, 504].includes(response.status) && attempt + 1 < attempts) {
   await response.body?.cancel();
   await delay(2000 * 2 ** attempt);
   continue;
  }
  let data;
  try { data = await response.json(); }
  catch { throw new Error('The server is temporarily unavailable. Please try again shortly.'); }
  if (!response.ok) throw Object.assign(new Error(data.error || 'Request failed. Please try again.'), {status: response.status});
  return data;
 }
}
