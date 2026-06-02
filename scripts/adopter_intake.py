#!/usr/bin/env python3
"""Parse an adopter-submission issue, verify the badge on the product URL,
and open a PR adding the entry to adopters.yml. Run by the intake workflow."""
import os, re, sys, subprocess, datetime, urllib.request
import yaml

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
def get(*keys):
    for want in keys:
        for k, v in f.items():
            if want in k:
                return "" if v.strip() in ("_No response_", "") else v.strip()
    return ""

name        = get("product name")
product_url = get("product url")
repo        = get("repository")
desc        = get("short description")
variant     = get("license variant")
logo        = get("logo url", "logo")

def comment(msg):
    subprocess.run(["gh", "issue", "comment", num, "--body", msg], check=False)

if not (name and product_url and variant):
    comment("⚠️ I couldn't read all required fields (product name, URL, variant). "
            "Please edit the issue using the form fields and I'll re-check.")
    sys.exit(0)

# --- verify the badge link on the public product page ---
try:
    req = urllib.request.Request(product_url, headers={"User-Agent": "heirloom-adopters-bot"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
except Exception as e:
    comment(f"⚠️ Couldn't fetch `{product_url}` to verify the badge ({e}). "
            "Make sure it's public, then edit the issue to re-run.")
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

adopters.append({
    "name": name, "product_url": product_url, "repo": repo, "description": desc,
    "variant": variant, "logo": logo, "added": datetime.date.today().isoformat(),
    "status": "live", "verified": True,
})
data["adopters"] = adopters
yaml.safe_dump(data, open("adopters.yml", "w"), sort_keys=False, allow_unicode=True)

slug = re.sub(r'[^a-z0-9-]+', '-', name.lower()).strip('-')
branch = f"adopter/{slug}-{num}"
subprocess.run(["git", "config", "user.name", "heirloom-bot"], check=True)
subprocess.run(["git", "config", "user.email", "bot@heirloomlicense.org"], check=True)
subprocess.run(["git", "checkout", "-b", branch], check=True)
subprocess.run(["git", "add", "adopters.yml"], check=True)
subprocess.run(["git", "commit", "-m", f"Add adopter: {name} (closes #{num})"], check=True)
subprocess.run(["git", "push", "origin", branch], check=True)
subprocess.run(["gh", "pr", "create",
                "--title", f"Add adopter: {name}",
                "--body", f"Automated from #{num}. Badge verified on {product_url}.\n\nCloses #{num}.",
                "--head", branch], check=False)
comment(f"✅ Badge verified on `{product_url}` — opened a PR to add **{name}** to the directory. "
        "A maintainer will merge it shortly. Welcome aboard!")
print("done")
