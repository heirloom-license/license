#!/usr/bin/env python3
"""Generate ADOPTERS.md and site/adopters.json from adopters.yml."""
import json, datetime, pathlib, re, sys
try:
    import yaml
except ImportError:
    sys.exit("pyyaml required: pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://heirloomlicense.org/adopters"

def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or "").lower()).strip('-')

data = yaml.safe_load((ROOT / "adopters.yml").read_text()) or {}
adopters = data.get("adopters") or []
adopters.sort(key=lambda a: (0 if a.get("status") == "live" else 1, a.get("name", "").lower()))
for a in adopters:
    a["slug"] = slugify(a.get("name", ""))
    a["permalink"] = f"{SITE}#{a['slug']}"

# JSON consumed by the website directory
(ROOT / "site" / "adopters.json").write_text(json.dumps(
    {"updated": datetime.date.today().isoformat(), "count": len(adopters), "adopters": adopters},
    indent=2) + "\n")

# Human-readable markdown table
SUBMIT = "https://github.com/heirloom-license/license/issues/new?template=adopter-submission.yml"
lines = [
    "# Adopters", "",
    "Software released under the Heirloom License. **Want to be listed?** "
    f"[Submit your app]({SUBMIT}) — fill the form, our bot verifies your badge and opens a PR.", "",
    "Live directory: **https://heirloomlicense.org/adopters**", "",
    "| Product | Variant | Status | Verified | Website | Directory link |",
    "|---|---|---|---|---|---|",
]
for a in adopters:
    url = a.get("product_url") or a.get("repo") or ""
    webmd = f"[{re.sub(r'^https?://(www[.])?', '', url).rstrip('/')}]({url})" if url else "—"
    lines.append(
        f"| **{a.get('name','')}** | `{a.get('variant','')}` | "
        f"{(a.get('status','') or '').capitalize() or '—'} | "
        f"{'✅' if a.get('verified') else '—'} | {webmd} | [#{a['slug']}]({a['permalink']}) |")
lines += ["", "*Generated from [`adopters.yml`](adopters.yml) — do not edit by hand.*", ""]
(ROOT / "ADOPTERS.md").write_text("\n".join(lines))
print(f"Generated ADOPTERS.md and site/adopters.json ({len(adopters)} adopters)")
