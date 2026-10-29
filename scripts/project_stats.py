#!/usr/bin/env python3
"""Count native project input/zoom events without printing event contents."""
import argparse
import json
import re
import sys
from pathlib import Path

EVENT_FILE = re.compile(r"(mousemoves|mouseclicks|keystrokes)-\d+\.json$")
MAX_JSON_BYTES = 64 * 1024 * 1024


def read_json(path):
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("JSON file exceeds the bounded parser limit")
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def project_stats(project):
    root = Path(project).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Supply a native project directory, not an archive")
    project_file = root / "project.json"
    if project_file.is_symlink():
        raise ValueError("Symlinked project metadata is not accepted")
    metadata = read_json(project_file)
    data = metadata.get("json", metadata) if isinstance(metadata, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        raise ValueError("Unrecognized project scene schema")
    counts = {"mousemoves": 0, "mouseclicks": 0, "keystrokes": 0}
    files = {key: 0 for key in counts}
    # Path.rglob does not descend into directory symlinks on supported Python.
    # Resolve each selected file as well to reject any external target.
    for path in root.rglob("*.json"):
        match = EVENT_FILE.fullmatch(path.name)
        if not match:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("Symlinked event data is not accepted")
        values = read_json(path)
        if not isinstance(values, list):
            raise ValueError("Unrecognized event schema; counts would be unreliable")
        key = match.group(1)
        counts[key] += len(values)
        files[key] += 1
    zoom_count = 0
    system_count = 0
    non_system_count = 0
    unknown_count = 0
    for scene in data["scenes"]:
        if not isinstance(scene, dict) or not isinstance(scene.get("zoomRanges", []), list):
            raise ValueError("Unrecognized zoom schema")
        for zoom in scene.get("zoomRanges", []):
            if not isinstance(zoom, dict):
                raise ValueError("Unrecognized zoom item")
            zoom_count += 1
            if zoom.get("isSystem") is True:
                system_count += 1
            elif zoom.get("isSystem") is False:
                non_system_count += 1
            else:
                unknown_count += 1
    return {"event_counts": {key: counts[key] if files[key] else None for key in counts}, "event_file_counts": files,
            "missing_event_kinds": [key for key in files if not files[key]],
            "zoom_ranges": zoom_count, "zoom_is_system_true": system_count,
            "zoom_is_system_false": non_system_count, "zoom_origin_unknown": unknown_count,
            "automatic_zoom_proven": False,
            "privacy": "Counts only; no names, titles, event values, keys or timestamps emitted"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="A local .screenstudio directory containing project.json")
    args = parser.parse_args()
    try:
        result = project_stats(args.project)
    except (OSError, ValueError, UnicodeError, RecursionError):
        print(json.dumps({"ok": False, "error": "Project statistics failed; unsupported schema, oversized JSON or unreadable input"}))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
