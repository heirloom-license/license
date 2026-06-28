# Deploying the site & directory

The public site (**heirloomlicense.org**) is a static site served by a **Cloudflare
Worker** (Workers Static Assets); the adopters directory is driven by GitHub Actions in
this repo. They are two independent "deploys."

## 1. The website (Cloudflare Worker)

Static files live in [`site/`](site/), served by the `heirloom-license` Worker
(config in [`wrangler.jsonc`](wrangler.jsonc) — `assets.directory = ./site`).

```sh
npx wrangler deploy          # needs CLOUDFLARE_API_TOKEN in your environment
```

Run this after changing anything in `site/` (`index.html`, `adopters.html`, `badge.svg`).
Deploys are **manual** — no git auto-build is connected. Canonical domain is
heirloomlicense.org (apex + `www`); `.com` 301-redirects to it.

## 2. The adopters directory (GitHub Actions, on `main`)

[`adopters.yml`](adopters.yml) is the source of truth. Three self-contained workflows
keep the rendered artifacts (`site/adopters.json`, `ADOPTERS.md`) and the live status in
sync — all run from `main`:

| Workflow | Trigger | Does |
|---|---|---|
| `adopters-intake.yml` | adopter-submission issue | verify badge (+ heartbeat), open a PR |
| `adopters-build.yml` | push touching `adopters.yml` | regenerate `adopters.json` + `ADOPTERS.md` |
| `adopters-poll.yml` | cron (every 6h) + manual | poll each adopter's heartbeat, refresh its `report` |

`site/adopters.html` fetches `adopters.json` from
**raw.githubusercontent.com/heirloom-license/license/main**, so merging to `main` makes
directory *data* live without a Worker deploy — but the page's HTML/JS only updates when
you `wrangler deploy`. The status pipeline (poll → verify → derive → render) is specified
in [`HEARTBEAT.md`](HEARTBEAT.md); `scripts/` holds the build/intake/poll code.

## Full go-live checklist

1. Merge changes to `main`.
2. `git push origin main` — activates the poll cron and makes `adopters.json` live via raw.
3. `npx wrangler deploy` — ships `site/` (new HTML/JS) to the Worker.
4. Verify: [heirloomlicense.org/adopters](https://heirloomlicense.org/adopters) renders the
   live status, and the latest **adopters-poll** Actions run is green.
