#!/usr/bin/env python3
"""Verify a stable local export using ffprobe and a complete ffmpeg decode."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path


def fingerprint(path):
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def verify_export(media, ffprobe="ffprobe", ffmpeg="ffmpeg", timeout=600):
    path = Path(media).expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Export must be a nonempty regular file")
    before = fingerprint(path)
    probe_tool, decode_tool = shutil.which(str(ffprobe)), shutil.which(str(ffmpeg))
    if not probe_tool or not decode_tool:
        raise ValueError("ffprobe and ffmpeg must be available")
    probed = subprocess.run([
        probe_tool, "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration",
        "-of", "json", str(path)], capture_output=True, text=True, timeout=timeout, check=False)
    if probed.returncode or probed.stderr.strip():
        raise ValueError("ffprobe reported a media error")
    metadata = json.loads(probed.stdout)
    streams = metadata.get("streams", [])
    if len(streams) != 1:
        raise ValueError("No primary video stream was decoded")
    stream = streams[0]
    duration = float(metadata.get("format", {}).get("duration", 0))
    width, height = int(stream.get("width", 0)), int(stream.get("height", 0))
    frames = int(stream.get("nb_read_frames", 0))
    if not math.isfinite(duration) or duration <= 0 or min(width, height, frames) <= 0:
        raise ValueError("Export has no positive duration, dimensions or decoded frames")
    decoded = subprocess.run([
        decode_tool, "-nostdin", "-v", "error", "-xerror", "-i", str(path),
        "-map", "0:v", "-map", "0:a?", "-f", "null", "-"],
        capture_output=True, text=True, timeout=timeout, check=False)
    if decoded.returncode or decoded.stderr.strip():
        raise ValueError("Full video/audio decode failed or reported errors")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    if fingerprint(path) != before:
        raise ValueError("Export changed during verification; wait for writing to finish")
    return {"bytes": before[2], "sha256": digest.hexdigest(), "duration_seconds": duration,
            "video_codec": stream.get("codec_name"), "width": width, "height": height,
            "average_frame_rate": stream.get("avg_frame_rate"), "decoded_primary_video_frames": frames,
            "full_decode_exit_code": decoded.returncode, "full_decode_errors": 0,
            "native_recording_proven": False,
            "scope": "File validity only; recording provenance and visual effects require separate evidence"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path, help="An already completed local video export")
    parser.add_argument("--ffprobe", default="ffprobe", help="ffprobe executable path or name")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable path or name")
    parser.add_argument("--timeout", type=int, default=600, help="Seconds per media subprocess (default: 600)")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        result = verify_export(args.media, args.ffprobe, args.ffmpeg, args.timeout)
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired):
        print(json.dumps({"ok": False, "error": "Export validation failed; check tools, file stability, metadata and full decode"}))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
