# Screen Studio reverse engineering with REA

[![Offline tool checks](https://github.com/Royo-Qiao/screenstudio-rea-research/actions/workflows/checks.yml/badge.svg)](https://github.com/Royo-Qiao/screenstudio-rea-research/actions/workflows/checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Read-only tools and an evidence-led case study of Screen Studio **3.7.3-4540** on
Apple Silicon macOS. Inspect an Electron app bundle, count native recording events
without exposing keystrokes, and verify that an exported video fully decodes.

This repository is for developers and agent operators investigating the boundary
between an Electron editor and native recording/export helpers. It contains
original research tools and documentation, rather than the Screen Studio app or
its source. [中文说明](README.zh-CN.md) · [Evidence and limits](docs/evidence.md)

## What was actually verified?

| Observation | Result and scope |
|---|---|
| Native recording → saved project → reopen → edit → export | Passed in the local isolated-copy experiment |
| Exported native recording | H.264, 1104 × 720, 60 fps, 3,337 frames, 55.616667 s; complete decode passed |
| Human mouse-operation recording | 938 mouse positions, 15 clicks, 10 keystrokes, 1 zoom range; user reported normal functionality |
| Application restart | Offline reopen/export passed; a full macOS reboot was not tested |
| Networked authorization | **Failed** in the experiment; offline export is not evidence of permanent activation |
| Packaged copy | Launch and restoration checked; complete native capture was not repeated after final signing |
| Tested system | Apple Silicon, macOS 26.5.2; other systems were not tested |

These are historical observations from 2026-10-29, summarized in
[machine-readable observations](evidence/observations.json). A later
[read-only tool recheck](evidence/tool-recheck.json) independently checks the
existing app declarations, aggregate project events and saved export file. Private recordings and
raw machine logs are excluded, so readers cannot independently replay those
historical artifacts from this repository. The tools below let you collect new
evidence from your own files.

## Quickstart

Python 3.10+; no Python packages to install. The first two tools use the standard
library. Export validation also needs `ffprobe` and `ffmpeg` on `PATH`.

```bash
git clone https://github.com/Royo-Qiao/screenstudio-rea-research.git
cd screenstudio-rea-research

# Reads declarations and hashes; does not launch or modify the app.
python3 scripts/inspect_app.py "/path/to/Screen Studio.app"

# Prints counts only; does not emit recorded keys, window titles or coordinates.
python3 scripts/project_stats.py "/path/to/Demo.screenstudio"

# Checks metadata, decodes every video/audio stream, and hashes the stable file.
python3 scripts/verify_export.py "/path/to/export.mp4"
```

Each command emits JSON and exits nonzero on an inspection or validation error.
Paths above are placeholders for files you own. Do not paste private project data
into a public issue. A successful file decode proves media validity; it does not
prove that Screen Studio captured it or that its effects match another recording.

Example fields from an export result:

```json
{
  "ok": true,
  "video_codec": "h264",
  "width": 1104,
  "height": 720,
  "decoded_primary_video_frames": 3337,
  "full_decode_exit_code": 0,
  "native_recording_proven": false
}
```

The field names are the CLI schema; numbers illustrate the historical native test.
The project and UI recording provenance must be checked separately.

## Research path

1. [Architecture](docs/architecture.md): Electron resources, native recorder,
   event tracks, editor and export validation.
2. [Reproduction](docs/reproduction.md): inspect your licensed local app, use
   [REA](https://github.com/morluto/rea) for focused analysis, record a disposable
   demo through the actual UI, and validate the final media.
3. [Evidence](docs/evidence.md): distinguish static findings, runtime observations,
   human acceptance and untested behavior.
4. [Agent instructions](SKILL.md): a bounded, privacy-conscious workflow suitable
   for a coding agent.
5. [Discoverability review](docs/discoverability/README.md): query-to-document
   evidence and an unpublished experience-based article draft.

The public evidence includes curated REA
[Electron fuse](evidence/rea-fuses-summary.json) and
[Mach-O](evidence/rea-macho-summary.json) excerpts with their real Evidence IDs;
they are static inspections rather than native function decompilation.

## Why the checks matter

The experiment exposed several misleading success signals: a token being present
did not mean it was accepted; an export-complete log did not guarantee a final
video existed; and an imported desktop capture did not verify the application's
own native recorder. Unpacked executable modes, custom WASM asset loading and a
native recorder's atomic temporary writes also affected the workflow. The
[case study](docs/evidence.md) keeps each finding attached to its evidence level.

## Compatibility

The inspected application declared macOS 12.0 and had an arm64 main executable.
The experimental local package bundled an arm64 Node runtime declaring macOS 13.5.
These are binary declarations, **not** a tested support range. Only macOS 26.5.2
on Apple Silicon was exercised. This repository's static parsers and offline tests
can run elsewhere, but that does not make the macOS app compatible with Intel,
Windows or Linux.

## Development

```bash
python3 -m unittest discover -s tests -v
```

Tests use synthetic fixtures and mocked media subprocesses; they never launch
Screen Studio, make network requests, or need a license token. CI runs the same
suite on Python 3.10 and 3.13.

## Scope and ownership

Original tools and documentation are MIT licensed. Screen Studio remains its
vendor's product; no vendor binaries, extracted source, installers, license
responses or personal recordings are distributed. The historical isolated-copy
experiment is not an independently rewritten application or a permanent licensing
solution. Use your own installation with authorization for recording and export.
See [third-party notices](THIRD_PARTY.md) and [contributing](CONTRIBUTING.md).
