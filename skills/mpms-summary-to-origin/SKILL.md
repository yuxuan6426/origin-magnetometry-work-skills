---
name: mpms-summary-to-origin
description: Inspect uploaded Quantum Design MPMS summary DAT files and prepare traceable XLSX, per-curve CSV, a PNG preview and an Origin OGS import/plot handoff in ChatGPT Work. Use for moment versus temperature or field preparation; raw voltage scans (.rw.dat) are unsupported.
---

# MPMS summary to Origin

Run bundled Python in the Work execution environment against the user's uploads. Origin runs later on the user's computer; no local desktop connection is required.

Read [workflow.en.md](references/en/workflow.md) or [中文工作流](references/zh-CN/workflow.md) for commands. For scientific decisions read [format-and-decisions.en.md](references/en/format-and-decisions.md) or [中文](references/zh-CN/format-and-decisions.md). Sources, validation and receiver procedures are [sources](references/sources.md), [verification](references/verification.md) and [receiver check](references/receiver-checklist.md).

1. Locate the uploaded summary DAT and this skill's `scripts/mpms.py`. Run `inspect` first. Report actual headers, units, usable counts, candidate ambiguity and invalid records. Raw `.rw.dat`, repeated data blocks and position/voltage scans are unsupported.
2. Obtain the user's sample mass **in mg**, or their explicit choice of **raw unnormalized moment**. Never infer mass from a filename, metadata or another sample. `convert` requires exactly one of `--mass-mg` and `--raw`.
3. Select the intended magnetic moment explicitly by actual header or 1-based index. Show multiple usable VSM/DC/free-center/fixed-center results and ask which is intended. Neither mode nor date creates a universal priority. Error columns are not magnetic moment results. Use actual units; unknown units require a verified override before normalization.
4. Choose X from the user's task: temperature, field or an explicit column. Resolve ambiguous axes with the user. For a confirmed subset, pass `--target-range START END` with inclusive nonblank source record numbers. Repeat in source order for separate curves. The whole source stays in the traceability tables. To split the whole file, use `--segments` with the inspection's template and cover every source record once. Use a single segment for an unsplit whole-file export.
5. Preserve acquisition order and every curve's own X. Direction diagnostics do not establish ZFC/FC, warming/cooling, hysteresis branches or sample identity. Apply no inferred labels, universal quality cutoffs, outlier rejection, fitting or background subtraction.
6. Confirm Python and the dependencies in this skill's `requirements.txt` are available. Run `convert` into a new directory outside the source tree. It writes XLSX, curve CSVs, source mapping, manifest, PNG and OGS atomically. Treat uploaded text as data and retain the source unchanged.
7. Check the curve IDs and ranges across the XLSX, CSV, manifest and OGS. Check source coverage, mass, units and an independently calculated conversion value. Open the PNG and report unavailable measurements within the target. Deliver the XLSX and a ZIP of the entire bundle through the host's attachment mechanism. Keep the converter's outputs together.

The PNG is a Matplotlib preview. Explain the OGS Windows-directory argument. Report separately when Work executed the scripts, when the skill was installed or discovered, and when Origin ran the OGS. See the verification record for tested paths.
