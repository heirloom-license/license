#!/usr/bin/env python3
"""Parse an adopter-submission issue, verify the badge on the product URL,
and open a PR adding the entry to adopters.yml. Run by the intake workflow."""
import os, re, sys, subprocess, datetime
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poll_heartbeats import fetch, poll_one, derive_state, now_utc, slugify

body = os.environ.get("ISSUE_BODY", "") or ""
num  = os.environ["ISSUE_NUMBER"]

def parse_form(text):
    fields = {}
    for chunk in re.split(r'\n###\s+', "\n" + text):
        if not chunk.strip():
            continue
        head, _, rest = chunk.partition("\n")
        fields[head.strip().lower()] = rest.strip()
    return fields

f = parse_form(body)
def get(label, n=400, oneline=True):
    """Look up a field by EXACT (normalized) form label — substring matching let a
    crafted field value smuggle a phantom heading that shadowed the real field."""
    v = f.get(label, "")
    if v.strip() in ("_No response_", ""):
        return ""
    v = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', v)   # strip control chars
    if oneline:
        v = re.sub(r'\s+', ' ', v)
    return v.strip()[:n]

name        = get("product name", 80)
product_url = get("product url")
repo        = get("repository url")
desc        = get("short description", 400, oneline=False)
variant     = get("license variant", 60)
logo        = get("logo url")
heartbeat_url = get("heartbeat url")
pubkey        = get("heartbeat public key", 200)

def comment(msg):
    subprocess.run(["gh", "issue", "comment", num, "--body", msg], check=False)

if not (name and product_url and variant):
    comment("⚠️ I couldn't read all required fields (product name, URL, variant). "
            "Please edit the issue using the form fields and I'll re-check.")
    sys.exit(0)

# --- verify the badge link on the public product page (SSRF-guarded fetch) ---
try:
    html = fetch(product_url, max_bytes=2_000_000).decode("utf-8", "ignore")
except Exception as e:
    comment(f"⚠️ Couldn't fetch `{product_url}` to verify the badge ({e}). "
            "Make sure it's a public **https** page, then edit the issue to re-run.")
    sys.exit(0)

if "heirloomlicense.org" not in html:
    comment(f"⚠️ I fetched `{product_url}` but didn't find a link to **heirloomlicense.org**. "
            "Add the badge to that page, then edit this issue to re-check:\n\n"
            "```markdown\n[![License: Heirloom 1.0](https://heirloomlicense.org/badge.svg)]"
            "(https://heirloomlicense.org)\n```")
    subprocess.run(["gh", "issue", "edit", num, "--add-label", "needs-badge"], check=False)
    sys.exit(0)

# --- passed: append to adopters.yml on a branch and open a PR ---
data = yaml.safe_load(open("adopters.yml")) or {"adopters": []}
adopters = data.get("adopters") or []
if any(a.get("name", "").lower() == name.lower() for a in adopters):
    comment(f"ℹ️ **{name}** is already listed. Closing the loop — edit the YAML directly if details changed.")
    sys.exit(0)

# --- optionally verify the public heartbeat (live "switch armed" status) ---
hb_fields, hb_note = {}, ""
if heartbeat_url or pubkey:
    if not (heartbeat_url and pubkey):
        hb_note = ("\n\n⚠️ You provided a Heartbeat URL **or** a public key but not both — "
                   "listing by badge only for now. Add both and edit this issue to enable live status.")
    else:
        now = now_utc()
        rep = poll_one({"slug": slugify(name), "heartbeat_url": heartbeat_url, "pubkey": pubkey}, now)
        if rep.get("sig_ok") and not rep.get("error"):
            hb_fields = {"heartbeat_url": heartbeat_url, "pubkey": pubkey}
            hb_note = f"\n\n🫀 Heartbeat verified — signature checks out; live status: **{derive_state(rep, now)}**."
        else:
            hb_note = (f"\n\n⚠️ I couldn't verify your heartbeat ({rep.get('error')}). Listed by badge for now — "
                       "make sure `heartbeat.json`/`.sig` are public, the `app` field equals "
                       f"`{slugify(name)}`, and the public key matches, then edit this issue to retry.")

entry = {
    "name": name, "product_url": product_url, "repo": repo, "description": desc,
    "variant": variant, "logo": logo, "added": datetime.date.today().isoformat(),
    "status": "live", "verified": True,
}
entry.update(hb_fields)
adopters.append(entry)
data["adopters"] = adopters
yaml.safe_dump(data, open("adopters.yml", "w"), sort_keys=False, allow_unicode=True)

branch = f"adopter/{slugify(name)}-{num}"
try:
    subprocess.run(["git", "config", "user.name", "heirloom-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "bot@heirloomlicense.org"], check=True)
    subprocess.run(["git", "checkout", "-B", branch], check=True)   # -B: idempotent on issue edits
    subprocess.run(["git", "add", "adopters.yml"], check=True)
    subprocess.run(["git", "commit", "-m", f"Add adopter: {name} (closes #{num})"], check=True)
    subprocess.run(["git", "push", "-f", "origin", branch], check=True)   # refresh branch on re-edit
    pr = subprocess.run(["gh", "pr", "create", "--base", "main",
                         "--title", f"Add adopter: {name}",
                         "--body", f"Automated from #{num}. Badge verified on {product_url}.\n\nCloses #{num}.",
                         "--head", branch], capture_output=True, text=True)
    if pr.returncode != 0 and "already exists" not in (pr.stderr or ""):
        raise RuntimeError((pr.stderr or "gh pr create failed").strip())
except Exception as e:
    comment(f"⚠️ I verified **{name}** but hit an error opening the PR: `{e}`. "
            f"A maintainer can complete it from #{num}.")
    sys.exit(0)
comment(f"✅ Badge verified on `{product_url}` — opened a PR to add **{name}** to the directory. "
        f"A maintainer will merge it shortly. Welcome aboard!{hb_note}")
print("done")
