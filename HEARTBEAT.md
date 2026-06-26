# Heirloom Heartbeat — status reporting protocol (v1)

This document is the canonical contract for how an adopter's dead-man's switch
**reports its status** so the [adopters directory](https://heirloomlicense.org/adopters)
can show live proof that the switch is armed and the promise is alive.

It implements the **Heartbeat Record** that the license already requires:

> §4. *"A valid update is any timestamped, publicly verifiable signal of continued
> maintenance — including a new release, a commit to the Source Repository, or a
> **signed heartbeat entry** — recorded at the Heartbeat Record location."*

The switch publishes a small, **signed, public** file on every run. Heirloom polls
it, verifies the signature, and renders the status. Nothing is pushed to a Heirloom
server; there is no central service holding secrets.

---

## Trust posture — authenticated self-report

The heartbeat is **self-reported but cryptographically attributable.** Heirloom
verifies that a heartbeat was produced by the holder of the adopter's registered
key and has not been tampered with, but **cannot inspect a private source repo** and
does not pretend to. Concretely:

- **Verifiable by anyone:** the file and its signature are public; the public key is
  published in [`adopters.yml`](adopters.yml). Verification is not privileged to
  Heirloom — any third party can run the same check.
- **What we assert:** "this app's own switch signed this status at this time."
- **What we do *not* assert:** independent confirmation of private commit history.
  A **Sunset** becomes independently verifiable once the repo is public.

The directory labels every reported status `self-reported · signed` to keep this honest.

---

## Published artifacts

The switch publishes two files at a stable, public HTTPS location the adopter owns
(a public `heirloom-heartbeat` repo, a gist, or a path on the product domain):

| File | Contents |
|---|---|
| `heartbeat.json` | The payload (UTF-8 JSON). Signed **as exact bytes.** |
| `heartbeat.json.sig` | Detached SSHSIG over the exact bytes of `heartbeat.json`. |

The directory stores the URL of `heartbeat.json` as `heartbeat_url`; the signature
is always fetched from the sibling URL `heartbeat_url + ".sig"`.

> **Canonicalization rule:** the signature covers the *exact bytes* of
> `heartbeat.json` as published. The poller verifies the signature against the bytes
> it fetched **before** parsing them. Never re-serialize before verifying.

---

## Payload schema — `heirloom-heartbeat/v1`

```json
{
  "schema": "heirloom-heartbeat/v1",
  "app": "memophant",
  "repo": "awizemann/Memophant",
  "variant": "HL-1.0-MPL2.0-12mo",
  "dormancy_days": 365,
  "change_license": "MPL-2.0",
  "last_signal": "2026-06-22T14:03:00Z",
  "emitted_at": "2026-06-26T09:00:11Z",
  "state": "active",
  "sunset": null
}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema` | const `"heirloom-heartbeat/v1"` | yes | Format version. Poller rejects unknown majors. |
| `app` | string (slug) | yes | Must equal the adopter's directory slug. Binds heartbeat → entry. |
| `repo` | `owner/name` | no | Informational only; may be private. |
| `variant` | string | yes | License variant id, e.g. `HL-1.0-MPL2.0-12mo`. |
| `dormancy_days` | integer > 0 | yes | The Dormancy Window in days. |
| `change_license` | SPDX string | yes | What the work becomes on Sunset. |
| `last_signal` | ISO-8601 UTC | yes | Timestamp of the most recent maintenance signal (last commit or manual heartbeat). **Resets the dormancy clock.** |
| `emitted_at` | ISO-8601 UTC | yes | When *this* heartbeat was produced. Written on **every** run — it is the liveness of the switch itself. |
| `state` | `active` \| `dormant` \| `sunset` | yes | The switch's own view of its state. |
| `sunset` | object \| null | iff `state==sunset` | `{ "date": "YYYY-MM-DD", "public_repo_url": "https://…" }` |

Timestamps are UTC, `YYYY-MM-DDTHH:MM:SSZ`. Unknown extra fields are ignored
(forward-compatible). A breaking change ships as `heirloom-heartbeat/v2`.

---

## Signing (switch side)

The adopter generates one Ed25519 keypair. The **private** key is stored as the repo
secret `HEIRLOOM_HEARTBEAT_KEY`; the **public** key line is registered in
`adopters.yml` as `pubkey`.

```sh
# one time — generate the keypair
ssh-keygen -t ed25519 -N "" -C "heirloom-heartbeat" -f hb_key
#   hb_key       -> repo secret HEIRLOOM_HEARTBEAT_KEY
#   hb_key.pub   -> adopters.yml: pubkey

# every run — sign the payload (fixed namespace, detached signature)
ssh-keygen -Y sign -f hb_key -n heirloom-heartbeat heartbeat.json
#   -> heartbeat.json.sig
```

**Namespace** is the constant `heirloom-heartbeat` (domain-separates these signatures
from any other use of the key). Requires OpenSSH ≥ 8.0 (present on GitHub runners).

---

## Verification (poller side)

The poller reconstructs an `allowed_signers` file from the registered `pubkey`, using
the **app slug as the principal**, and verifies the detached signature over the fetched
bytes:

```sh
printf '%s %s\n' "$SLUG" "$PUBKEY" > allowed_signers
ssh-keygen -Y verify -f allowed_signers -I "$SLUG" -n heirloom-heartbeat \
  -s heartbeat.json.sig < heartbeat.json
```

A non-zero exit (tampered payload, wrong key, malformed signature) marks the entry
`sig_ok: false` and the status is **not** trusted.

---

## Directory fields (`adopters.yml`)

Two fields are **registered once** by the adopter (via the intake form or a maintainer):

| Field | Set by | Meaning |
|---|---|---|
| `heartbeat_url` | adopter | Public URL of `heartbeat.json`. Enables status reporting. |
| `pubkey` | adopter | The `ssh-ed25519 AAAA… ` public key line that signs the heartbeat. |

One block is **written by the poller** (never hand-edited) and consumed by the site:

```yaml
report:
  state: active            # display state — see below
  sig_ok: true             # signature verified against pubkey
  last_signal: '2026-06-22T14:03:00Z'
  emitted_at: '2026-06-26T09:00:11Z'
  days_since_signal: 4
  runway_days: 361         # dormancy_days - days_since_signal
  sunset: null             # or { date, public_repo_url }
  last_polled: '2026-06-26T12:00:05Z'
  error: null              # human-readable reason when state == unknown
```

---

## Derived display states & thresholds

The poller computes one **display state** from the verified payload. Constants:

| Constant | Value | Rationale |
|---|---|---|
| `STALE_AFTER_DAYS` | 14 | Switch emits weekly; ~2 missed runs ⇒ we can't vouch. |
| `LOW_RUNWAY_DAYS` | 90 | Mirrors the §4 good-faith support window. |
| poll cadence | 6h | How often the directory refreshes. |

State resolution (first match wins):

| Display state | Condition | Shown as |
|---|---|---|
| `unknown` | fetch failed, `sig_ok:false`, or schema mismatch | ⚪ status unavailable |
| `sunset` | `state==sunset` + `sunset` object present | ⚫ Sunset — open-sourced, links public repo |
| `stale` | `now − emitted_at > STALE_AFTER_DAYS` | 🟠 no signal from switch since `emitted_at` |
| `dormant` | `runway_days ≤ 0` | 🔴 dormant — past the window |
| `low_runway` | `runway_days ≤ LOW_RUNWAY_DAYS` | 🟡 armed — ~N days to Sunset |
| `active` | otherwise | 🟢 armed — last signal Nd ago, ~N days runway |

`stale` is the safety property that matters most: if the switch itself dies (account
deleted, Actions disabled, token expired — the honest limits in
[`SETUP.md`](SETUP.md)), `emitted_at` stops advancing and the directory stops
vouching, rather than showing a frozen-green lie.

---

## Versioning

This protocol is `v1`. Additive fields are non-breaking and ignored by older readers.
Any change to the meaning of an existing field, the namespace, or the signature
scheme ships as a new `schema` major and a new section here.
