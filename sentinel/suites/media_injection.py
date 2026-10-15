"""
Media-injection suite: generates benign-but-hostile media (SQL strings in
metadata/filename/pixels + malformed and content/extension-mismatch files),
uploads each through the target, and asserts the pipeline neutralises them.

Checks:
  MED1  malformed media is rejected (not stored, no 5xx)
  MED2  content/extension mismatch is rejected (e.g. a PNG renamed .mp4)
  MED3  metadata SQLi probes create NO injected DB row        [needs db_probe]
  MED4  valid hostile uploads don't 500 and don't reflect the probe string

MED3 is the strongest proof; without a db_probe hook it's SKIPPED and MED4 still
gives black-box coverage (no crash, no reflection).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from ..adapters.base import Capability
from ..config import Config
from .common import Attack
from ..media.generator import generate


def _token(t, user):
    return t.login(user["username"], user["password"]).body.get("access_token", "")


def build(cfg: Config) -> list[Attack]:
    user = cfg.users["user"]
    # generate the corpus once; the checks share it
    tmp = Path(tempfile.mkdtemp(prefix="sentinel-media-"))
    manifest = generate(tmp)
    samples = [(m, (tmp / m["file"]).read_bytes()) for m in manifest if (tmp / m["file"]).exists()]

    def _uploads(t, predicate):
        tok = _token(t, user)
        results = []
        for m, data in samples:
            if not predicate(m):
                continue
            r = t.upload_bytes(tok, m["file"], data, m["content_type"])
            results.append((m, r))
        return results

    A: list[Attack] = []

    def med1(t):
        rs = _uploads(t, lambda m: m["expect"] == "reject" and m["probe_id"] in ("MAL1", "MAL2"))
        return all((not r.ok) and r.status != 500 for _, r in rs)
    A.append(Attack("MED1", "media", "malformed media is rejected", med1, {Capability.MEDIA_UPLOAD}))

    def med2(t):
        rs = _uploads(t, lambda m: m["probe_id"] == "MAL3")
        return all(not r.ok for _, r in rs)
    A.append(Attack("MED2", "media", "content/extension mismatch rejected", med2, {Capability.MEDIA_UPLOAD}))

    def med3(t):
        # upload every valid hostile sample, then assert no injected row exists
        _uploads(t, lambda m: m["expect"] == "accept")
        markers = [m["marker"] for m, _ in samples if m.get("marker")]
        return not any(t.injected_row_exists(mk) for mk in markers)
    A.append(Attack("MED3", "media", "metadata SQLi creates no injected DB row", med3,
                    {Capability.MEDIA_UPLOAD, Capability.DB_PROBE}))

    def med4(t):
        rs = _uploads(t, lambda m: m["expect"] == "accept")
        for m, r in rs:
            if r.status == 500:
                return False
            if m.get("marker") and m["marker"] in str(r.body):   # reflected payload
                return False
        return True
    A.append(Attack("MED4", "media", "hostile uploads don't crash or reflect the payload", med4,
                    {Capability.MEDIA_UPLOAD}))

    return A
