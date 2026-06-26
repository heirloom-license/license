# Setting up the Heirloom dead-man's switch

This guide walks you through arming the dead-man's switch: the automation that
makes good on the Heirloom License promise by publishing your repository under
your Change License if you ever go dormant.

It takes about 10 minutes. You only do it once per app.

> **Mental model.** The *license* (`LICENSE.md`) is the binding legal promise. The
> *switch* (this workflow) is the good-faith machine that performs it. Set up both.

---

## Before you start

- Your source repository should be **private** while you maintain it. The switch
  flips it public on Sunset.
- You need **admin** on the repository (to add a secret and let Actions change
  visibility).
- Decide your three parameters (defaults in brackets):
  - **Change License** — what the code becomes on Sunset. [`MPL-2.0`]
  - **Dormancy Window** — how long of silence triggers Sunset. [`365` days]
  - **Source Repository** — where the code publishes. [this repo]

---

## Step 1 — Add the license

Copy [`LICENSE.md`](LICENSE.md) into your repository root and fill in the
Parameters table at the top. For the common defaults you can start from
[`templates/HL-1.0-MPL2.0-12mo.md`](templates/HL-1.0-MPL2.0-12mo.md).

Optionally add a short `LICENSING.md` explaining the promise to buyers, and show
the badge in your README and in-app About box:

```markdown
[![License: Heirloom 1.0](https://heirloomlicense.org/badge.svg)](https://heirloomlicense.org)
```

## Step 2 — Add the workflow

Copy [`reference/.github/workflows/dead-mans-switch.yml`](reference/.github/workflows/dead-mans-switch.yml)
into your repo at `.github/workflows/heirloom-dead-mans-switch.yml`.

Open it and set the values near the top:

```yaml
env:
  DORMANCY_DAYS: "365"                 # your Dormancy Window in days (12 months = 365)
  CHANGE_LICENSE_SPDX: "MPL-2.0"       # your Change License
  CHANGE_LICENSE_URL: "https://www.mozilla.org/media/MPL/2.0/index.txt"
  APP_SLUG: "your-app-slug"            # your slug in adopters.yml — lowercase your
                                       # product name, non-alphanumerics → hyphens
                                       # (e.g. "Vellum Notes" → "vellum-notes")
  VARIANT: "HL-1.0-MPL2.0-12mo"        # your license variant id (must imply DORMANCY_DAYS)
  HEARTBEAT_REPO: ""                   # blank ⇒ <your-account>/heirloom-heartbeat
```

`APP_SLUG` must match the slug your directory entry gets (the directory derives it
from your product name the same way). `DORMANCY_DAYS` must match `VARIANT`'s window.

> Pushing workflow files needs a token with the **`workflow`** scope. If you're
> adding it through the API or a script and get a `404`, that missing scope is why.

## Step 3 — Create the `HEIRLOOM_PAT` secret

The default `GITHUB_TOKEN` **cannot change repository visibility**, so the switch
needs its own token.

1. Create a **fine-grained Personal Access Token** (GitHub ▸ Settings ▸ Developer
   settings ▸ Personal access tokens ▸ Fine-grained tokens).
2. Scope it to **two repositories** — this (private) source repo and the (public)
   `heirloom-heartbeat` repo from Step 4 — with these permissions:
   - Source repo → **Administration:** R/W *(flip visibility on Sunset)*,
     **Contents:** R/W *(swap the LICENSE, write the heartbeat clock)*,
     **Issues:** R/W *(post the Sunset announcement)*
   - Heartbeat repo → **Contents:** R/W *(push the public status file)*
3. In the source repo: **Settings ▸ Secrets and variables ▸ Actions ▸ New
   repository secret**. Name it exactly `HEIRLOOM_PAT` and paste the token.

Set an expiry you'll actually renew, or "no expiration" if you accept the
trade-off. An expired token silently disables the switch — see Hardening.

## Step 4 — Turn on public status reporting

This publishes a signed, public heartbeat so the
[adopters directory](https://heirloomlicense.org/adopters) can show that your
switch is armed — and implements the license's public **Heartbeat Record** (§4).
See [`HEARTBEAT.md`](HEARTBEAT.md) for the full protocol.

Do these **in order** — the directory bot verifies your live heartbeat at submission
time, so you must publish one *before* you list your app, or you'll be listed
badge-only until you retry.

1. **Create a public heartbeat repo.** Make a new **public** repo named
   `heirloom-heartbeat` in your account, initialized with a commit (a README is
   fine). Make sure its **default branch is `main`** (the Heartbeat URL below points
   at `main`; substitute your default branch if it differs). It holds only
   `heartbeat.json` — it reveals nothing about your source.
2. **Generate a signing key:**
   ```sh
   ssh-keygen -t ed25519 -N "" -C "heirloom-heartbeat" -f hb_key
   ```
   - Paste the contents of **`hb_key`** (the private key — keep the BEGIN/END lines
     and all newlines) into a source-repo secret named `HEIRLOOM_HEARTBEAT_KEY`.
   - Keep the line in **`hb_key.pub`** for step 4, then delete both files.
3. **Publish the first heartbeat.** With Steps 2–3 (the switch + `HEIRLOOM_PAT`) and
   the steps above done, run the switch by hand: **Actions ▸ Heirloom Dead-Man's
   Switch ▸ Run workflow**. Confirm `heartbeat.json` and `heartbeat.json.sig` now
   exist in your `heirloom-heartbeat` repo.
4. **List your app.** [Submit the adopter form](https://github.com/heirloom-license/license/issues/new?template=adopter-submission.yml)
   with your **Heartbeat URL**
   (`https://raw.githubusercontent.com/<you>/heirloom-heartbeat/main/heartbeat.json`)
   and the **public key** from `hb_key.pub`. The bot verifies the signature and
   opens a PR; the directory then polls and shows your live status.

## Step 5 — Keep it alive

The clock resets on any maintenance signal. You have two ways to send one:

- **Just commit.** Any push to the default branch counts. Normal development keeps
  the switch perpetually reset — you'll never think about it.
- **Manual heartbeat.** If you go quiet but are still around (a stable app you're
  not actively changing), run the workflow by hand: **Actions ▸ Heirloom Dead-Man's
  Switch ▸ Run workflow**. That resets the window and publishes a fresh public
  heartbeat (so the directory keeps showing you armed).

Set a calendar reminder for ~10 months if your app might go quiet for long stretches.

---

## Testing it safely

**Never test Sunset on your real private repo — it will make it public.** Test on
a throwaway:

1. Create a scratch **private** repo with a dummy file.
2. Add the workflow and a `HEIRLOOM_PAT` secret scoped to that scratch repo.
3. Set `DORMANCY_DAYS: "0"` so any age counts as dormant.
4. Temporarily let the Sunset job run on demand: change the Sunset step's guard
   from the schedule-only path to also run on `workflow_dispatch`, or just wait for
   the Monday cron. Run it.
5. Confirm the repo flipped public, `LICENSE` was replaced with your Change
   License, and the announcement issue was filed.
6. Delete the scratch repo.

This proves the full path end-to-end before you trust it on a real product.

## What happens on Sunset

When a scheduled run finds the repo has been dormant for the full window, the
workflow:

1. Fetches your Change License text and replaces `LICENSE`, appending a dated
   Sunset notice.
2. Commits that change.
3. Makes the repository **public**.
4. Opens an issue announcing the project is now open source.

This is irrevocable by design — that permanence is the whole promise.

## Hardening (and honest limits)

The switch is good-faith automation, not an unbreakable guarantee. Be honest with
your users about this. Known failure modes and mitigations:

- **Token expiry.** An expired `HEIRLOOM_PAT` disables the Sunset step. Use a long
  expiry and a renewal reminder, or accept "no expiration."
- **Account/repo deletion.** If the account is deleted, GitHub Actions can't run.
  For stronger assurance, add a second job that mirrors the repo to an independent
  host, or hand a copy to a trusted third party (classic source escrow).
- **Actions disabled.** If a maintainer disables Actions before disappearing, the
  switch won't fire. The **license text** still legally obligates publication
  (Section 6) — the automation just performs it.

The license and the switch reinforce each other: the contract is the promise, the
switch is the delivery. State this plainly to your buyers; the transparency is the
point.

## Troubleshooting

- **`404` when adding the workflow via API/script** → token missing the `workflow`
  scope.
- **Org allows only local actions (`local_only`)** → fine: the reference switch
  uses no third-party actions, so it runs under restrictive org policies.
- **Sunset step errors on visibility change** → `HEIRLOOM_PAT` missing, expired, or
  lacking **Administration: Read and write**.
- **Switch fired unexpectedly** → `DORMANCY_DAYS` too low, or no commit/heartbeat
  within the window. Restore from history; note that a completed Sunset grant is
  irrevocable under the license.
- **Want to confirm it's counting correctly** → check the scheduled run's logs; the
  "Measure dormancy" step prints days since the last maintenance signal.
