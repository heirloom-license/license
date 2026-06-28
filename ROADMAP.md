# Roadmap — from license text to movement

The license is the artifact. The *trend* needs a website, a credible home, a way
for people to back it, and a visible first adopter. Here's the sequence.

## Phase 1 — Ship the canonical repo (now)

- [ ] Create GitHub org `heirloom-license` (org, not personal repo — signals it's
      a standard, not one person's project).
- [ ] Push this scaffold as the `heirloom-license/license` repo.
- [ ] Tag `v1.0-draft`. Use GitHub Releases for every version so the text is
      immutably archived per version (important for a license).
- [ ] Open issues for the `LEGAL-REVIEW.md` items so the review is public and
      builds trust.
- [ ] Add a `CODE_OF_CONDUCT.md` and a lightweight `GOVERNANCE.md` (see Phase 4).

## Phase 2 — Website (heirloomlicense.org)

The site's whole job is to make a buyer relax in 10 seconds and a developer adopt
in 10 minutes. Model: fsl.software (one page, opinionated, links to the repo).

- [ ] Register `heirloomlicense.org` (and `.dev` defensively).
- [ ] Host `site/index.html` (included) on GitHub Pages or Vercel — static, free.
- [ ] Serve the badge at a stable URL (`/badge.svg`) so adopters can hot-link it.
- [ ] Add a one-line "is my app dormant?" explainer and the variant picker.
- [ ] Pages to add later: FAQ, adopters wall, "for buyers" vs "for developers".

I can wire up the Vercel/Pages deploy and register the domain when you're ready —
there are connectors available for both.

## Phase 3 — Ways for people to support it

Pick based on how heavy you want to go:

- **Lightweight (recommended start):** GitHub Sponsors on the org, a "Backers"
  section on the site, and a Star/adopt call-to-action. Costs nothing, signals
  momentum.
- **Adopters wall:** every app using it gets listed (`ADOPTERS.md` → rendered on
  the site). Social proof is the real currency for a license standard.
- **Open Collective:** if money comes in (legal review, domain, a logo designer),
  a transparent fiscal host fits the trust theme better than a personal account.
- **Endorsements:** get 2–3 respected indie devs to adopt early and quote them.
  A standard with three users is a standard; with one it's a proposal.

The biggest "support" lever isn't money — it's **other developers shipping with the
badge.** Optimize for adoption friction, not donations.

## Phase 4 — Governance (so it's trusted as a standard)

A license nobody can unilaterally change is more trustworthy than one person's
repo. Even a thin structure helps:

- Versioned, immutable releases (never edit a published version — issue a new one).
- A short stewardship statement: who can publish a new version, how changes are
  proposed (issues/PRs), and a promise that existing versions are permanent.
- CC0 on the text + marks policy on the name/badge (already in place).

## Phase 5 — You as first adopter

This is the proof. **Memophant** is the live first adopter:

- [x] Variant chosen — `HL-1.0-MPL2.0-12mo`.
- [x] `LICENSE.md` in the (private) app repo.
- [x] Dead-man's switch installed (the secret is `HEIRLOOM_PAT`; `DORMANCY_DAYS=365`).
- [x] Listed in the directory **and reporting live status** — Memophant publishes a
      public maintenance log (`memophant-public/heartbeat.log`); the directory polls it
      and shows it 🟢 armed. See [`HEARTBEAT.md`](HEARTBEAT.md).
- [ ] Add the **heirloomlicense.org badge** to memophant.co (the site references the
      guarantee but doesn't yet carry the badge link, so the directory marks it
      `verified: false`).
- [ ] Write a short launch post: "Why my apps will open-source themselves if I
      ever quit." That post is the marketing for the whole license.

## Suggested order of operations

1. Legal review of v1.0 (parallel-track; don't block the repo on it, but block the
   *promotion* on it).
2. Publish repo as `v1.0-draft`.
3. Adopt it in one of your apps end-to-end — this shakes out the switch.
4. Stand up the website.
5. Announce, with your app as the live example.
6. Recruit 2–3 more adopters before calling it a standard.

## Open decisions for you

- Final name: **Heirloom License** (current) vs. alternatives (Sunset Source,
  Lifeline). Naming locks in the domain and badge, so decide before Phase 2.
- Per-app Change License: MPL-2.0 everywhere, or AGPL for anything server-side?
- Do you want a hard backstop Sunset date (e.g. 5 years) in addition to the
  dormancy trigger? (See `LEGAL-REVIEW.md`.)
