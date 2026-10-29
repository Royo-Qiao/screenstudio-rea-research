# Evidence ledger and limits

This is a manually curated, de-identified account of a local experiment on
2026-10-29. The public repository does not contain the private media, source app,
full logs or raw REA ledger. Historical claims are therefore reported observations,
not independently replayable artifacts. [observations.json](../evidence/observations.json)
contains the same bounded facts in machine-readable form.

A fresh static REA inspection is preserved as a curated
[Electron fuse excerpt](../evidence/rea-fuses-summary.json), retaining its actual
Evidence ID and artifact hash. The excerpt is not the complete canonical ledger.
The [Mach-O excerpt](../evidence/rea-macho-summary.json) also preserves its actual
REA Evidence ID. Its executable hash identifies the locally repackaged/ad-hoc
signed copy, not the vendor distribution. The operation established arm64/macOS
12.0 declarations and two load dependencies; it did not decompile functions.

## Static observations

- Target: Screen Studio 3.7.3-4540, main executable arm64.
- Application and main executable declared macOS 12.0. The experimental bundled
  Node runtime declared macOS 13.5. Neither establishes an actual supported range.
- Expanded main JS SHA-256:
  `ec196d54e0217cbeb2d19504457975cbe57540481052bf60ed5e60a61de2b1b2`.
- The package used Electron, ASAR resources, a WASM demuxer and native helpers.
- REA `inspect_electron_fuses` found a version-1 eight-fuse wire in the arm64
  Electron Framework. `NodeCliInspect` was enabled; `EmbeddedAsarIntegrity` and
  `OnlyLoadAppFromAsar` were disabled. Those static settings do not prove that an
  inspector was reachable or that authorization, capture or export succeeded.
- A local static-reading aid decoded string references without bootstrapping the
  application. This was not a recovered original source tree.

## Runtime observations

| Test | Observation | Limitation |
|---|---|---|
| Earlier imported desktop recording | 35 s / 2,100 frames, export and offline application restart passed | This did not test Screen Studio's own recorder |
| Native recording | Saved project, reopened after application restart, edited, exported | Automated input produced only 9 positions, 0 clicks and 0 keys; duplicate cursor observed |
| Native export | H.264, 1104×720, 60 fps, 3,337 frames, 55.616667 s, 1,386,307 bytes; complete decode exit 0 | File validity does not establish effect equivalence |
| Manual zoom | A 2× zoom range was added in the editor | It was not evidence of automatic zoom generation |
| Timeline trim attempt | Stored range changed, but export remained 55.616667 s | The attempted trim did not take effect |
| Online authorization | Stored experimental response was rejected and cleared; export returned to activation UI | Networked export failed; no permanent activation |
| Final local package | Archive integrity, signature, launch and restoration checked | Full native capture was not repeated after final signing |

Native export SHA-256:
`fbf1708df2788dc784febbfe4afa8b9247067ca263f7ec637e5b3ab6f787871b`.
The video itself is private and is not linked or distributed here.

The original application JS and native recording helpers were not rewritten.
Startup path settings and process restrictions belonged to a separate experiment
harness. The final packaged main bundle used a local ad-hoc signature, which is
not equivalent to vendor signing or notarization. No such package is published.

## Human acceptance

A subsequent human recording contained 938 mouse positions, 15 clicks, 10
keystrokes and one zoom range. The user reported normal functionality. That zoom
had `isSystem=false`; its presence alone cannot establish that the app generated
it automatically. This feedback is distinct from an objective visual-equivalence
test and from the earlier automated native sample.

## Inferences and unanswered questions

- Automation input delivery or pointer overlays may explain the earlier sparse
  event data and duplicate cursor. The cause was not established.
- REA was part of the investigation toolchain and informs the reproduction path.
  A fuse-inspection Evidence ID is retained in the curated excerpt; no Screen
  Studio Ghidra function dossier is published. Complete native decompilation is
  not claimed. A separate native
  sample used to validate the toolchain is not evidence about this product.
- Only Apple Silicon/macOS 26.5.2 was exercised. Intel, other macOS versions,
  Windows, Linux, macOS cold boot, future app updates and online authorization
  stability remain unverified.
- The historical configuration restoration covered a selected snapshot, not a
  full account or whole-machine backup.
- The repository tools were written after the experiment. Their fixture tests
  validate their behavior; they do not retroactively rerun the historical UI test.

## Bounded JavaScript analysis did not complete

A fresh REA 6.8.0 check selected only `dist-electron/index.js` (7,483,205 bytes)
from the expanded local copy. The first attempt reached a 60,000 ms per-source
provider deadline. One recovery raised that budget to 180,000 ms and lowered the
semantic node/unknown limits from 5,000 to 1,000; it also timed out. Both produced
partial observations, with 3,694 inventoried files explicitly outside the selected
source scope. No complete JavaScript application graph or absence claim is based
on these attempts. See [the curated failure record](../evidence/rea-javascript-limits.json).
The successful Mach-O and fuse observations remain separate static evidence.

## Fresh validation-tool recheck

The repository's actual CLI tools were run against the pre-existing local app,
human project and native export on the publication date. Signature verification
passed for the local ad-hoc signed copy; the project yielded the documented
aggregate event counts; the 55.616667-second saved export fully decoded with no
errors. [Aggregate output](../evidence/tool-recheck.json) is public; the app,
project, video and private paths are not. This did not repeat native capture,
restart the app, validate networked licensing or test another system.
