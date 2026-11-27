"""event_parse.py - threshold-event extraction from GEV tool text (2026-11-27).

GEV tools answer with a human summary line PLUS a JSON blob carrying the real
rows and a share view.url. Parse the blob when present; fall back to the
summary lines only for what the blob does not cover."""
import json
import re


def _blobs(text):
    out = []
    for line in str(text or "").splitlines():
        s = line.strip()
        if s.startswith("{"):
            try:
                d = json.loads(s)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                pass
    return out


def _rows(blobs, key="rows"):
    for b in blobs:
        r = b.get(key)
        if isinstance(r, list):
            return r
    return []


def _share_url(blobs):
    for b in blobs:
        u = (b.get("view") or {}).get("url")
        if isinstance(u, str) and u.startswith("http"):
            return u
    return None


def events_from(snap):
    """Threshold events from one snapshot dict: quake M>5, active cyclones, crewed launches."""
    out = []
    for name in ("quakes", "cyclones", "launches"):
        text = snap.get(name) or ""
        blobs = _blobs(text)
        url = _share_url(blobs)
        if name == "quakes":
            for r in _rows(blobs):
                try:
                    mag = float(r.get("magnitude"))
                except Exception:
                    continue
                if mag > 5.0:
                    out.append({"id": "quake-%s" % str(r.get("id") or r.get("place"))[:48],
                                "kind": "quake", "mag": mag,
                                "desc": "M%.1f %s at %s" % (mag, r.get("place", "?"), r.get("time", ""))[:180],
                                "lat": r.get("lat"), "lon": r.get("lon"), "share_url": url})
        elif name == "cyclones":
            storms = _rows(blobs, "storms") or _rows(blobs)
            if not storms:
                continue
            for s in storms[:8]:
                nm = str(s.get("name") or s.get("title") or "unnamed").strip()
                out.append({"id": "cyc-" + re.sub(r"[^a-z0-9]", "-", nm.lower())[:40],
                            "kind": "cyclone", "name": nm,
                            "desc": ("active tropical cyclone: %s (%s)" % (nm, s.get("basin") or s.get("region") or ""))[:180],
                            "lat": s.get("lat"), "lon": s.get("lon"), "share_url": url})
        else:
            for r in _rows(blobs):
                blob = "%s %s" % (r.get("name", ""), r.get("mission", ""))
                if re.search(r"(?i)\bcrew\b|dragon|soyuz|starliner", blob):
                    out.append({"id": "launch-" + str(r.get("id") or r.get("name"))[:48],
                                "kind": "launch",
                                "desc": ("%s | %s | %s" % (r.get("time", ""), r.get("provider", ""), r.get("name", "")))[:180],
                                "share_url": url})
    return out
