#!/usr/bin/env python3
"""
Generate BENIGN media files that carry SQL-injection *strings* in every channel
a real upload could reach (filename, container/EXIF/PNG metadata, pixels). The
files execute nothing — they are data that looks like SQL, used to prove a
pipeline treats them inertly.

Requires: ffmpeg on PATH, Pillow.  Call generate(out_dir) -> manifest(list).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROBES = [
    ("P01", "'; DROP TABLE users; --"),
    ("P02", "1' OR '1'='1"),
    ("P03", "'); INSERT INTO audit(note) VALUES ('SQLiPROBE_P03'); --"),
    ("P04", '" OR ""="'),
    ("P05", "admin'--"),
    ("P06", "'; UPDATE users SET role='admin' WHERE id=1; --"),
    ("NC",  "x','x','video/mp4',0,0,0); INSERT INTO audit(note) VALUES ('SQLiPROBE_NC'); --"),
    ("P11", "%27%20OR%201=1--"),
    ("P14", "'/*c*/OR/**/1=1--"),
]


def _tag(pid, payload):
    return f"SQLiPROBE_{pid}::{payload}"


def _run(cmd):
    subprocess.run(cmd, capture_output=True, text=True)


def generate(out_dir) -> list:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = []

    # 1) MP4 — probe in container metadata atoms
    for pid, payload in PROBES:
        marker = _tag(pid, payload)
        arg = marker.replace("\x00", "\\x00")
        path = out / f"video_{pid}.mp4"
        _run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=320x240:d=1",
              "-metadata", f"title={arg}", "-metadata", f"comment={arg}",
              "-pix_fmt", "yuv420p", str(path)])
        if path.exists():
            manifest.append({"file": path.name, "type": "mp4", "probe_id": pid,
                             "marker": marker, "content_type": "video/mp4", "expect": "accept"})

    # 2) PNG + 3) JPEG — probe in text chunks / EXIF + pixels
    try:
        from PIL import Image, PngImagePlugin, ImageDraw
        for pid, payload in PROBES:
            marker = _tag(pid, payload)
            p = out / f"image_{pid}.png"
            img = Image.new("RGB", (480, 120), (20, 30, 50))
            ImageDraw.Draw(img).text((8, 50), marker[:60], fill=(230, 230, 230))
            meta = PngImagePlugin.PngInfo()
            meta.add_text("Comment", marker); meta.add_itxt("Title", marker)
            img.save(p, pnginfo=meta)
            manifest.append({"file": p.name, "type": "png", "probe_id": pid,
                             "marker": marker, "content_type": "image/png", "expect": "accept"})

            j = out / f"photo_{pid}.jpg"
            img2 = Image.new("RGB", (480, 120), (50, 20, 30))
            ImageDraw.Draw(img2).text((8, 50), marker[:60], fill=(240, 240, 240))
            exif = img2.getexif(); exif[0x010e] = marker; exif[0x9286] = marker
            img2.save(j, exif=exif)
            manifest.append({"file": j.name, "type": "jpg", "probe_id": pid,
                             "marker": marker, "content_type": "image/jpeg", "expect": "accept"})
    except ImportError:
        sys.stderr.write("[warn] Pillow missing; PNG/JPEG samples skipped\n")

    # 4) malformed + content/extension-mismatch — must be rejected
    good = out / "video_P01.mp4"
    if good.exists():
        (out / "malformed_truncated.mp4").write_bytes(good.read_bytes()[: good.stat().st_size // 3])
        manifest.append({"file": "malformed_truncated.mp4", "type": "mp4", "probe_id": "MAL1",
                         "marker": None, "content_type": "video/mp4", "expect": "reject"})
    pngsrc = out / "image_P02.png"
    if pngsrc.exists():
        # a real PNG truncated mid-stream: valid signature, structurally broken
        (out / "malformed_fakepng.png").write_bytes(pngsrc.read_bytes()[:40])
        manifest.append({"file": "malformed_fakepng.png", "type": "png", "probe_id": "MAL2",
                         "marker": None, "content_type": "image/png", "expect": "reject"})
        (out / "disguised_png_as.mp4").write_bytes(pngsrc.read_bytes())
        manifest.append({"file": "disguised_png_as.mp4", "type": "mp4", "probe_id": "MAL3",
                         "marker": None, "content_type": "video/mp4", "expect": "reject"})

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "samples"
    m = generate(d)
    print(f"generated {len(m)} entries in {d}/")
