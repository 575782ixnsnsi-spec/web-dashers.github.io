
window._apiBase = (function () {
  // The Base44 sandbox preview serves this page with a same-origin /api
  // development stub and sets this flag, so accounts/cloud saves behave like
  // local dev instead of calling the hosted backend, which a preview origin
  // cannot reach (no CORS headers there).
  if (window.__previewLocalApi === true) return '';
  const h = location.hostname;
  if (h === 'localhost' || h === '127.0.0.1') return ''; 
  return 'https://webdasher-backend.itzar.dev'; 
}());
