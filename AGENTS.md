# Working on Web Dashers in this sandbox

## What this project is
A client-side static site: `index.html` plus `assets/` (Phaser 3 game, sprites, level
`.txt` files, music, sfx). There is **no build step, no bundler, and no package
dependencies** — `package.json` only carries a `start` script (`npx serve .`). Editing
any file under `assets/` or `index.html` is live on the next page load.

## Running it
`docker compose -f docker-compose.base44.yml up -d` serves the repo root on host port
3000 with Python's stdlib static file server (`python -m http.server`, threaded). Nothing
is installed at startup; the clone is bind-mounted and read from disk per request. Use
`reload_preview` after edits if the browser holds a stale page.

Verify: `curl -sI http://localhost:3000/` returns 200 `text/html`, and
`curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/assets/scripts/core/main.js`
returns 200. `docker compose ps` should show `web` as healthy.

## The one thing that is *not* in this repo
The account / cloud-save API (`/api/auth/*`, `/api/saves`) is a separate server whose
source is deliberately git-ignored here (see `/.gitignore`: `/server.js`, `*.env*`).
`db/schema.sql` in this repo documents that server's tables (`users`, `user_sessions`,
`cloud_saves`) but nothing here applies or serves it.

`assets/scripts/utils/api-config.js` picks the API base:
- host `localhost` / `127.0.0.1` → `''` (same-origin, expects the un-committed `server.js`)
- any other host → `https://webdasher-backend.itzar.dev`

So inside the sandbox preview the client's login / register / cloud-save calls go to that
external backend, **not** to the compose stack. Those features are external and are not
covered by the sandbox setup. The game itself (main levels, icon kit, settings, level
editor) is fully local and does not need the backend.

Other outbound traffic is public and unauthenticated: the GD proxy Cloudflare workers
listed in `index.html`, `boomlings.com` (GD's API, or the proxy), and `gdbrowser.com` for
online level metadata. No API keys or credentials are required to boot this project.

## Verifying the app actually works
First load pulls ~75 MB of assets and then flips a cache flag, so allow a few seconds:

```js
// in the preview browser
localStorage.getItem('webdash_assets_loaded') === 'true'  // loading finished
typeof window.scene                                       // 'object' => GameScene running (set in game-scene.js)
document.querySelector('canvas')                          // Phaser canvas, 16:9
```

The main menu opens with the "BETA (EXPECT BUGS)" update-log pop-up rendered over it;
that is the app's own boot behaviour (`game-scene.js` guard `window.updateLogShown`), not a
sandbox artifact. Any runtime error surfaces as an empty canvas plus console errors — check
`consoleLogs({ level: 'error' })` before reporting a blank preview.

## Gotchas
- `assets/scripts/core/loading-screen.js` begins with an `eval(atob(...))` anti-scam guard:
  it only rewrites the page when the document is framed **and** the referrer host matches a
  known clone domain (or `sessionStorage.lol_rekt` is `'1'`). It stays inert in the sandbox.
- Asset URLs carry cache-busting query strings (`main.js?latest`) — the static server strips
  the query, so nothing needs configuring for that.
- `db/schema.sql` assumes PostgreSQL; there is no database service in this compose file,
  because the only consumer of those tables (the un-committed backend) is not run here.
