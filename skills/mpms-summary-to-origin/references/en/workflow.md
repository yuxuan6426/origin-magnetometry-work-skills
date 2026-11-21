# Work workflow and CLI

Python 3.10+ is required. `inspect` needs only its standard library. `convert` additionally needs openpyxl 3.1+ (<4) and Matplotlib 3.8+ (<4). The tested dependency versions are recorded in [verification](../verification.md). From the plugin root, install with `python -m pip install -r requirements.txt` if package installation is available. In Work, discover the execution environment and skill directory rather than assuming local Windows paths or a fixed `/mnt` location.

## Inspect before conversion

Run the actual bundled script against the uploaded file:

```sh
python skills/mpms-summary-to-origin/scripts/mpms.py inspect /path/to/upload.dat --output /path/to/inspection.json
```

Inspection reports actual headers and parsed units, 1-based indices, finite-value counts/ranges, candidate roles and ambiguity. The exact direction-change record is the record completing a change in the sign of successive nonzero X differences; equal X does not change direction, and missing X resets the diagnostic. This is a descriptive signal, not a segment boundary or experiment identity.

`--encoding NAME` overrides UTF-8-with-BOM then cp1252 decoding. A cp1252 fallback is recorded as a warning. `--delimiter comma|tab` overrides separator discovery. Files with missing or repeated `[Data]` markers fail explicitly. A selected output JSON path must not exist.

## Choose columns, units and mass

Use the user's intended magnetic moment header exactly as reported, or its numeric index. Multiple usable moment results require a user choice; the program does not rank VSM, DC free-center or DC fixed-center results. Error/uncertainty columns are separate candidates and cannot be selected as the magnetic moment.

Choose `--x temperature` or `--x field` only when inspection shows a unique usable axis candidate. Use `--x-column` for an exact header or 1-based index when necessary. X values keep the source unit; field is not silently changed from Oe to tesla. Missing X units are explicit in the metadata.

For normalization, supply the sample mass **in mg** that the user provided. The CLI requires one of `--mass-mg` or `--raw`; it has no default mass or normalization mode. Mass must be positive and finite. Normalized output is emu/g, using `M = moment_emu / (mass_mg / 1000)`. Source emu and A m² are supported for normalization; 1 A m² = 1000 emu. A verified `--moment-unit emu` or `--moment-unit 'A*m^2'` overrides the source unit and is recorded. Unknown units block normalization; raw mode preserves values and reports the source unit or “unspecified.”

## Segments

The default is one segment spanning every nonblank data record. To override it, copy `segment_template` from the inspection JSON into a temporary JSON file. Its structure is an object with a `segments` array; every item has integer `start`, integer `end`, and optional string `label`. Split ranges using the user's confirmed protocol and retain full coverage of records 1 through N. Ranges are inclusive, contiguous, nonoverlapping and in source order. A range may include invalid measurement records; these remain mapped. Empty ranges, skipped records and reordered ranges fail.

Labels are user text. ZFC/FC and sweep identity are not derived from temperature ordering, nominal fields, filename tokens or curve shape. No tolerance-based clustering or fit-quality rejection is applied.

## Convert

Replace each placeholder with the inspected selection and the user's mass:

```sh
python skills/mpms-summary-to-origin/scripts/mpms.py convert /path/to/upload.dat --output /path/to/new-output --moment-column 'ACTUAL HEADER' --x temperature --mass-mg USER_MASS_MG --segments /path/to/confirmed-segments.json
```

For a subset, replace `--segments ...` with `--target-range START END`, using inclusive source record numbers. Repeat it for ordered, non-overlapping ranges. Every curve artifact contains the selected ranges and both source tables preserve all records. Each target curve needs at least one finite X/Y pair and retains its missing measurements.

For raw moment values, replace `--mass-mg USER_MASS_MG` with `--raw`. Omit both range options for a single whole-file curve. For an explicit horizontal column, replace `--x temperature` with `--x-column 'ACTUAL X HEADER'`. The output directory must be new. Exit status is 0 for success and 2 for expected input/configuration errors. The script never overwrites an existing bundle.

Outputs:

| File | Content |
| --- | --- |
| `magnetometry.xlsx` | Metadata, literal source fields, curve index, one sheet per curve and `XY_Wide` with each curve's own X/Y pair |
| `curve_*.csv` | X, Y, original moment, source record and physical line range; rows remain in acquisition order |
| `source_rows.csv` | Every nonblank source record, curve row/CSV row, validity and original token array as JSON |
| `manifest.json` | Source SHA-256, discovered columns, chosen settings, exact ranges, scaling, runtime and artifact hashes |
| `preview.png` | Headless Matplotlib overview; invalid pairs create gaps |
| `import_origin.ogs` | Local Origin CSV import and a line graph per curve |
| `READ_ME.txt` | Bundle handoff notes |

Open the PNG and check manifest counts, selected units and an independently calculated normalization value. Attach the XLSX and a ZIP of the **entire** output directory using the Work host's attachment mechanism. A ZIP can be built using Python's standard library; keep generated data outside the skill repository.

## Origin handoff

Download and extract the whole bundle to a Windows directory. In Origin's Script Window, execute the generated OGS section, substituting the real paths:

```text
run.section("C:\data\import_origin.ogs", Main, "C:\data\");
```

The one argument is the extracted directory **including its trailing backslash**. The script creates a workbook and line graph for each curve with Origin's CSV Data Connector. It reads columns 1 and 2 for X/Y; later CSV columns provide provenance. Check headers, numeric import, missing-value line behavior and axes against the manifest and preview in the recipient's Origin version. Save the Origin project manually if desired. There is no live desktop automation or `.opju` generation here.

See the [verification record](../verification.md) for Work receiver and native Origin results.
