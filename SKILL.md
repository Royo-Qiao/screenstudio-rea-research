---
name: screenstudio-rea-research
description: Read-only Screen Studio app inspection, private project event statistics, and complete video export validation. Use for REA-assisted Electron/native workflow research; does not install, activate, patch, or launch the target app.
license: MIT
---

# Screen Studio research and export validation

Read [the evidence limits](docs/evidence.md) before interpreting results. Resolve
this skill's absolute directory from the loaded SKILL.md; scripts live there.

1. Identify the user's app, native project or finished export. Inspect only the
   requested target; do not search recordings or read captured keystroke values.
2. Run `python3 <skill-dir>/scripts/inspect_app.py <app>` for bundle declarations,
   main executable Mach-O slices and hashes. It never launches the app. Optional
   `--runtime-node <binary>` inspects a separate runtime. Missing packed-main JS
   hashes stay null: the script does not extract ASAR or invent a hash.
3. Use REA only for a concrete unresolved question. Read its current skill and
   tool availability. Bind the user-selected local artifact; retain exact target
   hashes and returned Evidence IDs. Do not claim a native function was decompiled
   from a strings search or this repository's static parser.
4. Run `project_stats.py <native-project-directory>` for aggregate input and zoom
   counts. Missing event files are unknown, distinct from a present empty list.
   The `isSystem` field and zoom count do not alone prove automatic zoom behavior.
5. Run `verify_export.py <finished-local-media>` to require positive media
   metadata, decoded frames, a complete video/audio decode and a stable file hash.
   A nonzero exit or `ok:false` fails validation. Do not treat an app's export log
   as final-file evidence. Do not publish the video or full project without a
   separate user request to share those materials.
6. If the user requests runtime validation, follow [reproduction](docs/reproduction.md)
   using their installation and valid recording/export authorization. A human UI
   recording is needed for mouse/zoom acceptance. Do not alter authorization logic,
   inject license responses, disable global security, modify hosts/proxy, or use
   this repository as authorization to run someone else's experiment.
7. Report static observations, actual runtime results, user feedback and unknowns
   separately. State tested system, app version and each important limitation.

The historical case passed native recording/editing/offline export, but networked
authorization failed and no full OS reboot was tested. This repository is a
research record with new validation tools, not an app replacement or activation
solution. Do not stop or overwrite a user's currently running app to inspect files.
