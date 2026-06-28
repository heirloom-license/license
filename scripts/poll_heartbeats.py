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
STALE_AFTER_DAYS = 14        # signed switch emits weekly; ~2 missed runs ⇒ can't vouch
STALE_AFTER_DAYS_LOG = 45    # a public log's liveness cadence is ~monthly (cron), so allow more
LOW_RUNWAY_DAYS = 90        # mirrors the §4 good-faith support window

# Map a variant id (HL-1.0-MPL2.0-12mo) to its license params, for log-sourced
# adopters whose public log carries signals but not dormancy/change-license.
_CL_MAP = {"MPL2.0": "MPL-2.0", "GPL3.0": "GPL-3.0-or-later", "AGPL3.0": "AGPL-3.0-or-later"}

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

def fetch(url, max_bytes=MAX_BYTES):
    """Fetch bytes with SSRF guards (https-only, no redirects, no private IPs) and a
    size cap. Reused by the intake bot for the badge page (with a larger cap)."""
    _check_url(url)
    u = urllib.parse.urlparse(url)
    if u.scheme == "file":
        with open(urllib.request.url2pathname(u.path), "rb") as f:
            data = f.read(max_bytes + 1)
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "heirloom-heartbeat-poller"})
        with _OPENER.open(req, timeout=TIMEOUT) as r:
            data = r.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"response exceeds {max_bytes} bytes")
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


def variant_params(variant):
    """(dormancy_days, change_license) from a variant id like HL-1.0-MPL2.0-12mo."""
    m = re.match(r'HL-1\.0-([A-Za-z0-9.]+)-([1-9]\d*)mo$', (variant or "").strip())
    if not m:
        return None, None
    return round(int(m.group(2)) * 365 / 12), _CL_MAP.get(m.group(1), m.group(1))

def _base_report():
    return {"source": None, "sig_ok": None, "last_signal": None, "emitted_at": None,
            "dormancy_days": None, "change_license": None, "sunset": None, "error": None}

def _future(times, now):
    horizon = now + datetime.timedelta(days=FUTURE_TOLERANCE_DAYS)
    return any(t > horizon for t in times)

def poll_one(a, now):
    """Fetch one adopter's heartbeat and return a facts report (never raises). A
    registered pubkey ⇒ the hardened signed-JSON source; otherwise a public
    maintenance log (simplest, provenance-trusted). See HEARTBEAT.md."""
    rep = _base_report()
    url = a.get("heartbeat_url")
    if not url:
        rep["error"] = "no heartbeat_url registered"; return rep
    return _poll_signed(a, url, now, rep) if a.get("pubkey") else _poll_log(a, url, now, rep)

def _poll_signed(a, url, now, rep):
    """Hardened source: a detached-SSHSIG-signed heartbeat.json verified against pubkey."""
    rep["source"] = "signed"; rep["sig_ok"] = False
    slug = a.get("slug") or slugify(a.get("name", ""))
    if not valid_pubkey(a.get("pubkey")):
        rep["error"] = "registered pubkey is malformed"; return rep
    try:
        payload = fetch(url); sig = fetch(url + ".sig")
    except Exception as e:
        rep["error"] = f"fetch failed: {e}"; return rep
    ok, msg = verify_sig(slug, a["pubkey"], payload, sig)
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
    if hb.get("app") != slug:
        rep["error"] = f"app mismatch: heartbeat app={hb.get('app')!r}, entry slug={slug!r}"; return rep
    try:
        last = parse_ts(hb["last_signal"]); emitted = parse_ts(hb["emitted_at"])
        dormancy = int(hb["dormancy_days"])
    except Exception as e:
        rep["error"] = f"bad/missing required field: {e}"; return rep
    if _future([last, emitted], now):
        rep["error"] = "timestamp is in the future (clock skew)"; return rep
    sunset_obj = None
    if hb.get("state") == "sunset":   # only a declared Sunset, with an https repo url, becomes a link
        so = hb.get("sunset")
        surl = so.get("public_repo_url") if isinstance(so, dict) else None
        if not (isinstance(surl, str) and surl.startswith("https://")):
            rep["error"] = "state=sunset but sunset.public_repo_url is missing or not https"; return rep
        sunset_obj = {"date": (str(so["date"]) if so.get("date") is not None else None), "public_repo_url": surl}
    cl = hb.get("change_license")
    rep.update(last_signal=iso_z(last), emitted_at=iso_z(emitted), dormancy_days=dormancy,
               change_license=(str(cl) if cl is not None else None), sunset=sunset_obj)
    return rep

def _poll_log(a, url, now, rep):
    """Simple source: a public JSONL maintenance log (e.g. memophant-public/heartbeat.log).
    Trust is provenance-based — the log lives in the adopter's own public repo (no SSHSIG).
    last_signal = latest commit/release entry (real work); emitted_at = latest entry of any
    kind (mechanism liveness); dormancy/change-license come from the registered variant."""
    rep["source"] = "log"
    try:
        raw = fetch(url, max_bytes=1_000_000).decode("utf-8", "ignore")
    except Exception as e:
        rep["error"] = f"fetch failed: {e}"; return rep
    horizon = now + datetime.timedelta(days=FUTURE_TOLERANCE_DAYS)
    work, latest_any, sunset_obj = [], None, None
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            ent = json.loads(line)
            t = parse_ts(ent.get("ts"))
        except Exception:
            continue   # skip non-JSON / undated lines rather than aborting the whole log
        if t > horizon:
            continue   # skip a single clock-skewed/future line rather than failing the report
        latest_any = t if latest_any is None or t > latest_any else latest_any
        if ent.get("kind") in ("commit", "release"):
            work.append(t)
        elif ent.get("kind") == "sunset" and isinstance(ent.get("public_repo_url"), str) \
                and ent["public_repo_url"].startswith("https://"):
            sunset_obj = {"date": (str(ent["date"]) if ent.get("date") is not None else None),
                          "public_repo_url": ent["public_repo_url"]}
    if latest_any is None:
        rep["error"] = "heartbeat log has no usable entries"; return rep
    dormancy, cl = variant_params(a.get("variant"))
    if dormancy is None:
        rep["error"] = f"cannot derive dormancy window from variant {a.get('variant')!r}"; return rep
    # Liveness pings alone (monthly/manual) are NOT a maintenance signal — without a
    # commit/release (or a terminal sunset) we can't vouch that the app is armed.
    if not work and not sunset_obj:
        rep["error"] = "no commit/release maintenance signal in log"; return rep
    rep.update(last_signal=iso_z(max(work) if work else latest_any), emitted_at=iso_z(latest_any),
               dormancy_days=dormancy, change_license=cl, sunset=sunset_obj)
    return rep


def derive_state(rep, now):
    """Display state from a facts report. MIRRORED in adopters.html — keep in sync."""
    if not rep or rep.get("error"):
        return "unknown"
    if rep.get("source") == "signed" and not rep.get("sig_ok"):
        return "unknown"
    if isinstance(rep.get("sunset"), dict):
        return "sunset"                                 # terminal — outranks staleness
    try:
        last = parse_ts(rep["last_signal"]); emitted = parse_ts(rep["emitted_at"])
        dormancy = int(rep["dormancy_days"])
    except Exception:
        return "unknown"
    if _future([last, emitted], now):
        return "unknown"   # clock skew
    stale_after = STALE_AFTER_DAYS_LOG if rep.get("source") == "log" else STALE_AFTER_DAYS
    if (now - emitted).total_seconds() / 86400.0 > stale_after:
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
            rep = _base_report(); rep["error"] = f"internal error: {e}"
        if a.get("report") != rep:
            a["report"] = rep; changed += 1
        state = derive_state(rep, now)
        ok = not rep.get("error")
        detail = (f"runway≈{rep['dormancy_days'] - int((now - parse_ts(rep['last_signal'])).total_seconds()//86400)}d"
                  if (ok and rep.get("last_signal")) else f"({rep['error']})")
        print(f"  {'✓' if ok else '✗'} {str(a.get('name','?')):<18} [{rep.get('source') or '-'}] {state:<10} {detail}")
    data["adopters"] = adopters
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    print(f"Polled {reporting} reporting adopter(s); "
          f"{changed} entr{'y' if changed == 1 else 'ies'} changed.")

if __name__ == "__main__":
    main()
