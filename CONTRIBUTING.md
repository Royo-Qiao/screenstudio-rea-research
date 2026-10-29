# Contributing

Use synthetic fixtures for parser and subprocess tests. Run
`python3 -m unittest discover -s tests -v` before submitting a change.

An issue about another version should include the app version, platform,
de-identified tool JSON and the smallest reproducible schema example. Remove
recorded keys, coordinates, titles, personal paths and names. Do not attach the
vendor app, extracted source, personal projects, activation responses or raw logs.

Keep static declarations, runtime behavior, human feedback and unknowns separate.
Do not generalize one tested system into a supported range or call a valid media
file proof of the native recording path. New format support needs a representative
synthetic fixture and a test that rejects malformed data.
