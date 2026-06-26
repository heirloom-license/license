#!/usr/bin/env python3
"""Poll each adopter's public heartbeat, verify its detached SSHSIG against the
registered public key, and write a `report` of the SIGNED FACTS back into
adopters.yml. The live display state and runway countdown are derived from these
facts at render time (browser + build) so they stay accurate between polls.
Run by the adopters-poll workflow. See HEARTBEAT.md.

Trust posture: authenticated self-report. We prove a heartbeat was signed by the
holder of the registered key and is untampered; we do not inspect private source.

Usage: poll_heartbeats.py [path/to/adopters.yml]   (default: repo adopters.yml)
"""
import datetime, ipaddress, json, os, pathlib, re, socket, subprocess, sys, tempfile
import urllib.parse, urllib.request
try:
    import yaml
except ImportError:
    sys.exit("pyyaml required: pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
NS = "heirloom-heartbeat"                # SSHSIG namespace — must match the switch
SCHEMA_MAJOR = "heirloom-heartbeat/v1"   # supported payload schema major
MAX_BYTES = 64 * 1024                    # a heartbeat is a few hundred bytes
TIMEOUT = 20
FUTURE_TOLERANCE_DAYS = 2                # reject timestamps further in the future (clock skew)
ALLOW_FILE = os.environ.get("HEIRLOOM_ALLOW_FILE") == "1"   # file:// — tests only

# Thresholds for the derived state. Mirrored in adopters.html (JS) and used by
# build_adopters.py for the static ADOPTERS.md snapshot. Keep all three in sync.
STALE_AFTER_DAYS = 14    # switch emits weekly; ~2 missed runs ⇒ can't vouch
LOW_RUNWAY_DAYS = 90    # mirrors the §4 good-faith support window

_PUBKEY_RE = re.compile(
    r'^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521))'
    r'\s+[A-Za-z0-9+/]+=*(?:\s+\S[^\r\n]*)?$')

def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or "").lower()).strip('-')

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)

def iso_z(dt):
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def parse_ts(s):
    """Parse an ISO-8601 stamp, accepting a trailing Z; always return aware UTC."""
    dt = datetime.datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def valid_pubkey(pk):
    pk = (pk or "").strip()
    return bool(pk) and "\n" not in pk and "\r" not in pk and bool(_PUBKEY_RE.match(pk))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None   # never follow redirects (a 30x to an internal host would be SSRF)

_OPENER = urllib.request.build_opener(_NoRedirect)

def _check_url(url):
    u = urllib.parse.urlparse(url)
    if u.scheme == "file":
        if not ALLOW_FILE:
            raise ValueError("file:// not allowed")
        return
    if u.scheme != "https":
        raise ValueError(f"scheme must be https (got {u.scheme!r})")
    host = u.hostname or ""
    try:
        addrs = {ai[4][0] for ai in socket.getaddrinfo(host, u.port or 443,
                                                        proto=socket.IPPROTO_TCP)}
    except Exception as e:
        raise ValueError(f"cannot resolve host: {e}")
    for a in addrs:
        ip = ipaddress.ip_address(a)
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise ValueError(f"host resolves to disallowed address {a}")

def fetch(url):
    _check_url(url)
    u = urllib.parse.urlparse(url)
    if u.scheme == "file":
        with open(urllib.request.url2pathname(u.path), "rb") as f:
            data = f.read(MAX_BYTES + 1)
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "heirloom-heartbeat-poller"})
        with _OPENER.open(req, timeout=TIMEOUT) as r:
            data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"response exceeds {MAX_BYTES} bytes")
    return data

def verify_sig(slug, pubkey, payload_bytes, sig_bytes):
    """Return (ok, message). Verifies the detached SSHSIG over the EXACT bytes."""
    with tempfile.TemporaryDirectory() as d:
        allowed = os.path.join(d, "allowed_signers")
        sigf = os.path.join(d, "heartbeat.sig")
        with open(allowed, "w") as f:
            f.write(f"{slug} {pubkey.strip()}\n")
        with open(sigf, "wb") as f:
            f.write(sig_bytes)
        p = subprocess.run(
            ["ssh-keygen", "-Y", "verify", "-f", allowed, "-I", slug, "-n", NS, "-s", sigf],
            input=payload_bytes, capture_output=True)
        return p.returncode == 0, p.stderr.decode("utf-8", "ignore").strip()


def poll_one(a, now):
    """Fetch + verify one adopter's heartbeat; return a facts report (never raises)."""
    slug = a.get("slug") or slugify(a.get("name", ""))
    rep = {"sig_ok": False, "last_signal": None, "emitted_at": None,
           "dormancy_days": None, "change_license": None, "sunset": None, "error": None}
    url = a.get("heartbeat_url")
    pubkey = a.get("pubkey")
    if not url or not pubkey:
        rep["error"] = "no heartbeat_url/pubkey registered"; return rep
    if not valid_pubkey(pubkey):
        rep["error"] = "registered pubkey is malformed"; return rep
    try:
        payload = fetch(url)
        sig = fetch(url + ".sig")
    except Exception as e:
        rep["error"] = f"fetch failed: {e}"; return rep
    ok, msg = verify_sig(slug, pubkey, payload, sig)
    rep["sig_ok"] = ok
    if not ok:
        rep["error"] = f"signature verification failed: {msg or 'mismatch'}"; return rep
    try:
        hb = json.loads(payload)
    except Exception as e:
        rep["error"] = f"payload is not valid JSON: {e}"; return rep
    schema = str(hb.get("schema") or "")
    if schema != SCHEMA_MAJOR and not schema.startswith(SCHEMA_MAJOR + "."):
        rep["error"] = f"unsupported schema: {hb.get('schema')!r}"; return rep
    if hb.get("app") != slug:    # app is mandatory and binds the heartbeat to this entry
        rep["error"] = f"app mismatch: heartbeat app={hb.get('app')!r}, entry slug={slug!r}"; return rep
    try:
        last = parse_ts(hb["last_signal"])
        emitted = parse_ts(hb["emitted_at"])
        dormancy = int(hb["dormancy_days"])
    except Exception as e:
        rep["error"] = f"bad/missing required field: {e}"; return rep
    horizon = now + datetime.timedelta(days=FUTURE_TOLERANCE_DAYS)
    if last > horizon or emitted > horizon:
        rep["error"] = "timestamp is in the future (clock skew)"; return rep
    # Sunset is recorded ONLY when state==sunset AND the payload (adopter-signed,
    # so attacker-influenceable) carries an https public_repo_url — this is what
    # the directory turns into a clickable link, so the scheme is enforced here.
    sunset_obj = None
    if hb.get("state") == "sunset":
        so = hb.get("sunset")
        url = so.get("public_repo_url") if isinstance(so, dict) else None
        if not (isinstance(url, str) and url.startswith("https://")):
            rep["error"] = "state=sunset but sunset.public_repo_url is missing or not https"
            return rep
        sunset_obj = {"date": (str(so["date"]) if so.get("date") is not None else None),
                      "public_repo_url": url}
    cl = hb.get("change_license")
    rep.update(last_signal=iso_z(last), emitted_at=iso_z(emitted), dormancy_days=dormancy,
               change_license=(str(cl) if cl is not None else None), sunset=sunset_obj)
    return rep


def derive_state(rep, now):
    """Display state from a verified facts report. MIRRORED in adopters.html — keep in sync."""
    if not rep or rep.get("error") or not rep.get("sig_ok"):
        return "unknown"
    if isinstance(rep.get("sunset"), dict):
        return "sunset"                                 # terminal — outranks staleness
    try:
        last = parse_ts(rep["last_signal"]); emitted = parse_ts(rep["emitted_at"])
        dormancy = int(rep["dormancy_days"])
    except Exception:
        return "unknown"
    if (emitted - now).total_seconds() / 86400.0 > FUTURE_TOLERANCE_DAYS \
            or (last - now).total_seconds() / 86400.0 > FUTURE_TOLERANCE_DAYS:
        return "unknown"   # clock skew — mirror poll_one()
    if (now - emitted).total_seconds() / 86400.0 > STALE_AFTER_DAYS:
        return "stale"
    runway = dormancy - int((now - last).total_seconds() // 86400)
    if runway <= 0:
        return "dormant"
    if runway <= LOW_RUNWAY_DAYS:
        return "low_runway"
    return "active"


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (ROOT / "adopters.yml")
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        sys.exit(f"cannot read {path}: {e}")
    adopters = data.get("adopters") or []
    now = now_utc()
    changed = reporting = 0
    for a in adopters:
        if not isinstance(a, dict):
            continue
        if not a.get("heartbeat_url"):
            if "report" in a:
                del a["report"]; changed += 1
            continue
        reporting += 1
        try:
            rep = poll_one(a, now)
        except Exception as e:   # defense in depth: one bad entry must not abort the run
            rep = {"sig_ok": False, "last_signal": None, "emitted_at": None,
                   "dormancy_days": None, "change_license": None, "sunset": None,
                   "error": f"internal error: {e}"}
        if a.get("report") != rep:
            a["report"] = rep; changed += 1
        state = derive_state(rep, now)
        detail = f"runway≈{rep['dormancy_days'] - int((now - parse_ts(rep['last_signal'])).total_seconds()//86400)}d" \
            if (rep["sig_ok"] and rep["last_signal"]) else f"({rep['error']})"
        print(f"  {'✓' if rep['sig_ok'] else '✗'} {str(a.get('name','?')):<20} {state:<10} {detail}")
    data["adopters"] = adopters
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    print(f"Polled {reporting} reporting adopter(s); "
          f"{changed} entr{'y' if changed == 1 else 'ies'} changed.")

if __name__ == "__main__":
    main()
