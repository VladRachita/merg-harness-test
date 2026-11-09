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

Every check first uploads a VALID file as its control: if a normal upload is
refused (bad token, wrong field name, rate limit) then "the hostile one was
refused too" would prove nothing.
"""
from __future__ import annotations

import functools
import shutil
import tempfile
from pathlib import Path

from ..adapters.base import Capability
from ..config import Config
from .common import Attack, Inconclusive, Leak, authed, body_contains, expect_ok, reached
from ..media.generator import generate


@functools.lru_cache(maxsize=1)
def corpus() -> tuple:
    """(manifest entry, bytes) pairs. Generated once per process, on first use —
    not at import/build time — and the temp files are removed straight away."""
    tmp = Path(tempfile.mkdtemp(prefix="sentinel-media-"))
    try:
        manifest = generate(tmp)
        return tuple((m, (tmp / m["file"]).read_bytes()) for m in manifest
                     if (tmp / m["file"]).exists())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def samples(predicate=lambda m: True) -> list:
    out = [(m, d) for m, d in corpus() if predicate(m)]
    if not out:
        raise Inconclusive("no media samples for this check could be generated — the corpus "
                           "needs ffmpeg (video) and Pillow (images) installed")
    return out


def valid_upload(t, tok):
    """Control: an ordinary, well-formed file is accepted."""
    good = samples(lambda m: m["expect"] == "control")
    m, data = next(((m, d) for m, d in good if m["type"] == "mp4"), good[0])
    return expect_ok(t.upload_bytes(tok, m["file"], data, m["content_type"]),
                     f"uploading a valid {m['type']} file")


def build(cfg: Config) -> list[Attack]:
    user = cfg.users["user"]
    A: list[Attack] = []

    def rejected(t, tok, which, what):
        for m, data in samples(which):
            r = reached(t.upload_bytes(tok, m["file"], data, m["content_type"]))
            if r.ok:
                raise Leak(f"{what} '{m['file']}' was accepted (HTTP {r.status})")
            if r.status >= 500:
                raise Leak(f"{what} '{m['file']}' crashed the upload pipeline (HTTP {r.status})")
        return True

    def med1(t):
        tok = authed(t, user); valid_upload(t, tok)
        return rejected(t, tok, lambda m: m["probe_id"] in ("MAL1", "MAL2"), "malformed file")
    A.append(Attack("MED1", "media", "malformed media is rejected", med1, {Capability.MEDIA_UPLOAD}))

    def med2(t):
        tok = authed(t, user); valid_upload(t, tok)
        return rejected(t, tok, lambda m: m["probe_id"] == "MAL3", "disguised file")
    A.append(Attack("MED2", "media", "content/extension mismatch rejected", med2,
                    {Capability.MEDIA_UPLOAD}))

    def med3(t):
        # upload the samples whose metadata carries a stacked INSERT, then ask the
        # DB whether the row that INSERT would write exists
        tok = authed(t, user)
        carriers = samples(lambda m: m.get("injected_value"))
        stored = 0
        for m, data in carriers:
            stored += reached(t.upload_bytes(tok, m["file"], data, m["content_type"])).ok
        if not stored:
            raise Inconclusive("none of the probe files was accepted — nothing reached storage")
        hit = next((m["injected_value"] for m, _ in carriers
                    if t.injected_row_exists(m["injected_value"])), None)
        if hit:
            raise Leak(f"an injected row '{hit}' exists — file metadata reached SQL unescaped")
        return True
    A.append(Attack("MED3", "media", "metadata SQLi creates no injected DB row", med3,
                    {Capability.MEDIA_UPLOAD, Capability.DB_PROBE}))

    def med4(t):
        tok = authed(t, user)
        accepted = 0
        for m, data in samples(lambda m: m["expect"] == "accept"):
            r = reached(t.upload_bytes(tok, m["file"], data, m["content_type"]))
            if r.status >= 500:
                raise Leak(f"'{m['file']}' crashed the upload pipeline (HTTP {r.status})")
            if m.get("marker") and body_contains(r.body, m["marker"]):
                raise Leak(f"the metadata payload of '{m['file']}' is echoed back unescaped")
            accepted += r.ok
        if not accepted:
            raise Inconclusive("every valid sample was refused — the pipeline was never exercised")
        return True
    A.append(Attack("MED4", "media", "hostile uploads don't crash or reflect the payload", med4,
                    {Capability.MEDIA_UPLOAD}))

    return A
