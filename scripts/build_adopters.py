#!/usr/bin/env python3
"""Generate ADOPTERS.md and site/adopters.json from adopters.yml.

The site computes each adopter's live status in the browser from the signed
`report` facts (see HEARTBEAT.md); this script also bakes a build-time snapshot
of that status into the static ADOPTERS.md table via the shared derive_state().

Usage: build_adopters.py [adopters.yml] [out_dir]   (defaults: repo root)
"""
import json, datetime, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try:
    import yaml
except ImportError:
    sys.exit("pyyaml required: pip install pyyaml")
from poll_heartbeats import derive_state, now_utc

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://heirloomlicense.org/adopters"
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (ROOT / "adopters.yml")
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT

# Build-time snapshot label for the static markdown table. The live site renders
# its own (always-current) version of these from the same facts.
STATE_LABEL = {
    "active": "🟢 Armed", "low_runway": "🟡 Low runway", "dormant": "🔴 Dormant",
    "stale": "🟠 Stale", "sunset": "⚫ Sunset", "unknown": "⚪ Unavailable", "none": "—",
}

def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or "").lower()).strip('-')

def status_of(a, now):
    return "none" if not a.get("report") else derive_state(a["report"], now)

data = yaml.safe_load(SRC.read_text()) or {}
adopters = data.get("adopters") or []
adopters.sort(key=lambda a: (0 if a.get("status") == "live" else 1, a.get("name", "").lower()))
now = now_utc()
for a in adopters:
    a["slug"] = slugify(a.get("name", ""))
    a["permalink"] = f"{SITE}#{a['slug']}"

# JSON consumed by the website directory (carries the signed `report` facts so
# the browser — and any third party — can derive and re-verify status).
(OUT / "site").mkdir(parents=True, exist_ok=True)
(OUT / "site" / "adopters.json").write_text(json.dumps(
    {"updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "count": len(adopters), "adopters": adopters},
    indent=2) + "\n")

# Human-readable markdown table
SUBMIT = "https://github.com/heirloom-license/license/issues/new?template=adopter-submission.yml"
lines = [
    "# Adopters", "",
    "Software released under the Heirloom License. **Want to be listed?** "
    f"[Submit your app]({SUBMIT}) — fill the form, our bot verifies your badge and opens a PR.", "",
    "Live directory (with real-time switch status): **https://heirloomlicense.org/adopters**", "",
    "Status is **self-reported and cryptographically signed** by each app's own "
    "dead-man's switch, then verified here (see [`HEARTBEAT.md`](HEARTBEAT.md)). "
    "The column below is a snapshot from the last build; the live site is current.", "",
    "| Product | Variant | Status | Verified | Website | Directory link |",
    "|---|---|---|---|---|---|",
]
for a in adopters:
    url = a.get("product_url") or a.get("repo") or ""
    webmd = f"[{re.sub(r'^https?://(www[.])?', '', url).rstrip('/')}]({url})" if url else "—"
    lines.append(
        f"| **{a.get('name','')}** | `{a.get('variant','')}` | "
        f"{STATE_LABEL.get(status_of(a, now), '—')} | "
        f"{'✅' if a.get('verified') else '—'} | {webmd} | [#{a['slug']}]({a['permalink']}) |")
lines += ["", "*Generated from [`adopters.yml`](adopters.yml) — do not edit by hand.*", ""]
(OUT / "ADOPTERS.md").write_text("\n".join(lines))
print(f"Generated ADOPTERS.md and site/adopters.json ({len(adopters)} adopters)")
