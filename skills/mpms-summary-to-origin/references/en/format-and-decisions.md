# Supported format and scientific decisions

## Scope

This tool reads a **summary measurement table** with one `[Data]` marker, a delimited column header and data records. It discovers the uploaded file's headers instead of assuming a universal MPMS column order. A comma or tab separator is detected; explicit delimiter/encoding overrides are available. Raw voltage-scan `.rw.dat` is a different, block-oriented format and is unsupported, including renamed position/voltage scans. AC susceptibility reduction, raw-scan fitting and background subtraction are separate workflows.

The Quantum Design notes listed in [sources](../sources.md) explain SVSM summary columns, raw DC scan files and the complementary DC-Scan/SQUID-VSM measurements. Their purpose differs: a summary-column description is not a guarantee that every software generation produces an identical schema. The implementation therefore records actual headers, units and finite-value availability. No document establishes a universal preference for a newer DC result over other usable moments.

## Column discovery

Names are classified conservatively for inspection: `Temperature`/`Sample Temperature`, `Magnetic Field`/`Field`, names containing the word `Moment`, and moment uncertainty names. The full original header is retained. The trailing parenthesized/bracketed token is reported as a unit. Classification gives candidates, not a scientific selection. An exact header or column index can select a nonstandard name. Duplicate exact headers require numeric indices. The selected X and moment must differ.

Blank, nonnumeric, NaN and infinite values do not become zeros. Short records are padded with blanks while their original field count is recorded. Extra fields beyond the header block conversion until the mismatch is resolved. Blank source records are excluded from record numbering and their physical line ranges are recorded. Quoted delimiters and multiline CSV fields remain traceable. Numeric calculation uses finite Python floats; original string tokens are preserved in the mapping and XLSX source sheet.

## Units and sample mass

Only user-provided sample mass is used. Raw keeps the selected moment numerically unchanged, including a known or unspecified source unit. Normalization supports emu and A m²; a unit override is an explicit statement about the source numeric values, not a guessed conversion. Normalized results are emu/g. X remains in its source unit, even if magnetic field was recorded in Oe. No density, molar mass, diamagnetic correction or per-atom factor is inferred.

## Curves and ordering

In target-range mode, `record_count` counts all source records, `curve_record_count` counts selected records including missing measurements, and `outside_target_record_count` counts records outside the selection. Those rows have status `outside_target_ranges` and empty curve fields in `source_rows.csv`. All curve artifacts use the ranges found in manifest `segments`.

The default single segment is an organizational choice, not a claim of one physical experiment. Explicit inclusive record ranges may override it. Every nonblank source record appears once, even if X or magnetic moment is invalid. Per-curve CSVs and XLSX worksheets keep acquisition order; `XY_Wide` has a separate X/Y pair for each curve and pads shorter curves at their ends. Equal X values, reversals and repeated setpoints remain intact. No resampling, interpolation, sorting or merging is performed.

Records are numbered after the column header. `source_line_start` and `source_line_end` refer to 1-based physical lines in the original decoded file. For multiline quoted comments, one record spans several physical lines. `curve_row` is 1-based numeric-row numbering; `curve_csv_row` includes the CSV header. `raw_cells_json` stores original decoded tokens before padding. The source SHA-256 binds mappings to the exact uploaded bytes.

## Interpretation and quality

Protocol knowledge is required to identify ZFC/FC, warming/cooling, hysteresis branches or distinct samples. Exact direction changes have no built-in tolerance and cannot establish these labels. Fit errors, regression values and transport status remain in the source fields. There is no universal numeric cutoff or automatic rejection. The PNG shows the selected measurements; it is not an assessment of measurement validity. Check the relevant instrument protocol and the user's intended correction before undertaking additional analysis.

## Artifact and execution boundaries

Uploaded strings are literal XLSX strings, even when beginning with `=`. Executable OGS contains controlled curve identifiers and safe captions; uploaded comments, arbitrary labels and headers are not inserted as code. Provenance CSV stores raw fields inside JSON arrays. A new output directory is staged and moved into place only after all artifacts succeed.

The workbook is bounded by Excel's row/column/text limits; conversion fails rather than truncate data. Origin import uses a CSV Data Connector and plots columns 1/2 in separate workbooks/graphs. Origin version compatibility, missing-point line behavior and native project saving require receiver verification. The code does not call a local Origin MCP, COM server or desktop application.
