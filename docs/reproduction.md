# Reproduce a local recording/export check

Use your own Screen Studio installation and valid authorization for recording and
export. The public tools are read-only. This guide does not recreate the earlier
experimental authorization state or supply a modified application.

## 1. Record identity before analysis

```bash
python3 scripts/inspect_app.py "/path/to/Screen Studio.app"
```

Keep the JSON locally. Compare app version, resource layout and executable hash
before comparing findings between machines. For expanded resources the tool hashes
the known main-JS location; for a packed app it reports the ASAR hash and leaves
the JS hash null. It does not unpack or execute anything. Use `--runtime-node`
only if a separate Node binary is part of your own setup.

`codesign --verify --deep --strict` is optionally invoked on macOS. A failed
signature check is a finding to investigate, not an instruction to clear
quarantine, disable Gatekeeper or bypass macOS warnings. A passed check is not a
notarization, trust or malware verdict.

## 2. Ask REA a specific question

Install [REA](https://github.com/morluto/rea) using its current instructions and
read the REA agent skill. Select the exact local artifact the user authorized.
For an Electron package, inspect its package structure and JavaScript feature
boundary. For a native helper, bind the helper with `open_binary` using an
available provider; inspect functions or strings only as the question requires.
Use Ghidra when configured and suitable. Preserve returned Evidence IDs and target
hashes. Close an owned native session when finished.

Tool schemas and provider availability can change, so this guide deliberately
does not invent a universal REA CLI command or promise every provider can analyze
every target. Static strings or a successful tool startup do not establish that
native recording or export ran. Do not upload vendor source or raw disassembly.

### Commands checked with REA 6.8.0

For static Mach-O inspection, this CLI was exercised during publication:

```bash
rea inspect-macho "/path/to/Screen Studio.app/Contents/MacOS/Screen Studio" --format json
```

The MCP operation `inspect_electron_fuses` accepts `{"path": "/absolute/path/to/Screen Studio.app"}`
and reads the Electron Framework bytes without launching the application. Record
its Evidence ID and digest, then retain or export needed records privately.
The bounded main-JavaScript graph attempts did not complete; see
[their explicit limits](../evidence/rea-javascript-limits.json) rather than treating
a partial inventory as recovered source or a complete native call graph.

## 3. Capture a normal disposable demo

Prepare a temporary folder containing two harmless text files. Close private
documents and notifications. Start the intended installation, record the folder
through its actual native UI, move the pointer, open a file and stop. Save the
native project. An external screen recording imported into the editor validates
an import/export path, rather than the application's capture backend.

Use the supported UI to edit a short range and inspect the cursor and zoom. Let a
person perform the mouse operations when evaluating capture effects: the earlier
automation produced sparse events and a duplicate pointer. Confirm permissions
using normal macOS settings; do not change global proxy or security policy.

## 4. Inspect event statistics privately

```bash
python3 scripts/project_stats.py "/path/to/Demo.screenstudio"
```

The observed native schema stores input tracks as JSON lists and zoom ranges in
project scenes. Missing event kinds are reported separately from present empty
lists. Counts and `isSystem` flags cannot prove automatic zoom or visual quality.
Do not share the full project: keystroke tracks, media and project names may be
sensitive. The tool does not support ZIP input or arbitrary format extraction.

## 5. Verify the finished export

```bash
python3 scripts/verify_export.py "/path/to/export.mp4"
```

Wait for writing to finish first. Positive dimensions, duration and decoded frame
count are required. `ffmpeg` must decode all video and optional audio streams to
completion without errors, and the file identity must remain stable throughout.
For a long file, increase `--timeout` explicitly. No output media is written.

Reopen the project after a normal application restart and export a second file.
Label this **application restart** unless you also performed a real OS reboot.
Test networked behavior only using ordinary vendor authorization. Record failures
as failures and keep the successful offline observation separate.

## 6. Report a bounded result

Report app version/system, native-capture provenance, aggregate input counts,
editing steps, actual media verification, user feedback and remaining gaps.
Keep file paths and private artifacts local. Do not publish an app bundle or
license material with the report. The snapshot and rollback plan for any optional
local experiment must be created from that user's current state.
