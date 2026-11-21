"""Reviewable artifacts for cloud execution; no Origin desktop connection."""
from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from mpms_core import Column, DataError, Dataset, VERSION, column_dict, source_info


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def literal_row(ws, values):
    """Preserve uploaded strings as literal cells, including '=' and error tokens."""
    from openpyxl.cell import WriteOnlyCell
    cells = []
    for value in values:
        if isinstance(value, str):
            if len(value) > 32767:
                raise DataError("A text cell exceeds Excel's 32,767-character limit; inspect/export source separately.")
            if any(ord(c) < 32 and c not in "\t\n\r" for c in value):
                raise DataError("A text cell contains an XML-incompatible control character.")
            cell = WriteOnlyCell(ws, value=value)
            cell.data_type = "s"
            cells.append(cell)
        else:
            cells.append(value)
    ws.append(cells)


def write_xlsx(path: Path, data: Dataset, curves, xcol: Column, moment: Column, yunit: str, scaling):
    from openpyxl import Workbook
    if len(data.records) + 1 > 1048576 or len(data.columns) + 4 > 16384 or len(curves) * 2 > 16384:
        raise DataError("Workbook would exceed Excel row/column limits. Convert smaller source files or fewer segments.")
    wb = Workbook(write_only=True)
    info = wb.create_sheet("Metadata")
    literal_row(info, ["key", "value"])
    for key, value in {
        "tool_version": VERSION, "source_filename": data.path.name, "source_sha256": data.sha256,
        "x_header": xcol.header, "moment_header": moment.header,
        "x_unit": xcol.unit or "unspecified", "y_unit": yunit,
        "scaling": json.dumps(scaling, ensure_ascii=False, allow_nan=False),
        "order": "Acquisition order retained. Each curve has its own X column.",
        "labels": "Curve labels are user supplied; no ZFC/FC or branch assignment is inferred.",
    }.items():
        literal_row(info, [key, value])
    raw = wb.create_sheet("Source_Rows")
    raw.freeze_panes = "E2"
    literal_row(raw, ["source_record", "source_line_start", "source_line_end", "original_field_count"] +
                [c.header for c in data.columns])
    for record in data.records:
        literal_row(raw, [record.number, record.line_start, record.line_end, record.width] + record.cells)
    index = wb.create_sheet("Curves")
    literal_row(index, ["id", "user_label", "start_record", "end_record", "valid_pairs", "invalid_pairs"])
    for curve in curves:
        literal_row(index, [curve["id"], curve["label"], curve["start"], curve["end"],
                            curve["valid_pairs"], curve["invalid_pairs"]])
        ws = wb.create_sheet(curve["id"])
        ws.freeze_panes = "A2"
        literal_row(ws, [f"X: {xcol.header}", f"Y ({yunit})", f"Raw: {moment.header}",
                         "source_record", "source_line_start", "source_line_end", "status"])
        for p in curve["points"]:
            r = p["record"]
            literal_row(ws, [p["x"], p["y"], p["moment"], r.number, r.line_start, r.line_end, p["status"]])
    wide = wb.create_sheet("XY_Wide")
    wide.freeze_panes = "A2"
    literal_row(wide, [item for curve in curves for item in
                       (f"{curve['id']}_X ({xcol.unit or 'unspecified'})", f"{curve['id']}_Y ({yunit})")])
    for i in range(max(len(c["points"]) for c in curves)):
        values = []
        for curve in curves:
            p = curve["points"][i] if i < len(curve["points"]) else None
            values.extend([p["x"], p["y"]] if p else [None, None])
        literal_row(wide, values)
    wb.save(path)


def write_csvs(directory: Path, data: Dataset, curves):
    for curve in curves:
        with (directory / (curve["id"] + ".csv")).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["X", "Y", "Moment", "source_record", "source_line_start", "source_line_end"])
            for p in curve["points"]:
                r = p["record"]
                writer.writerow([p["x"], p["y"], p["moment"], r.number, r.line_start, r.line_end])
    with (directory / "source_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_record", "source_line_start", "source_line_end", "original_field_count",
                         "curve_id", "curve_row", "curve_csv_row", "status", "raw_cells_json"])
        selected = iter((p["record"].number, curve["id"], i, p["status"])
                        for curve in curves for i, p in enumerate(curve["points"], 1))
        point = next(selected, None)
        for r in data.records:
            if point and point[0] == r.number:
                _, curve_id, i, status = point
                location = [curve_id, i, i + 1, status]
                point = next(selected, None)
            else:
                location = [None, None, None, "outside_target_ranges"]
            # JSON arrays begin with '['; uploaded cells are never interpolated as CSV formulas.
            writer.writerow([r.number, r.line_start, r.line_end, r.width, *location,
                             json.dumps(r.cells[:r.width], ensure_ascii=False)])


def axis_caption(col: Column) -> str:
    return col.name + (f" ({col.unit})" if col.unit else " (unit unspecified)")


def write_preview(path: Path, curves, xcol: Column, yunit: str):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    # Uploaded text is not interpreted as math expressions.
    with matplotlib.rc_context({"text.usetex": False, "text.parse_math": False}):
        fig = Figure(figsize=(9, 5.5), dpi=150, layout="constrained")
        ax = fig.subplots()
        for curve in curves:
            # Keep invalid pairs as gaps. Never sort or merge equal X coordinates.
            xs = [p["x"] if p["status"] == "valid" else math.nan for p in curve["points"]]
            ys = [p["y"] if p["status"] == "valid" else math.nan for p in curve["points"]]
            ax.plot(xs, ys, ".-", linewidth=1, markersize=3, label=curve["id"])
        ax.set(xlabel=axis_caption(xcol), ylabel=f"Magnetic moment ({yunit})",
               title="MPMS summary | acquisition order")
        ax.grid(alpha=0.2)
        if len(curves) <= 16:
            ax.legend(fontsize=8, frameon=False)
        fig.savefig(path, format="png", metadata={"Software": f"mpms-summary-to-origin {VERSION}"})
        fig.clear()


def write_ogs(path: Path, curves, xcol: Column, yunit: str):
    # Only controlled identifiers enter executable text. Uploaded headers/labels remain in manifest/XLSX.
    xlabel = {"temperature": "Temperature", "field": "Magnetic Field"}.get(xcol.role, "X - see manifest for unit")
    safe_units = {"K", "Oe", "T", "mT", "G", "kOe", "degC"}
    if xcol.unit in safe_units:
        xlabel += f" ({xcol.unit})"
    ylabel = "Magnetic moment (emu/g)" if yunit == "emu/g" else "Raw moment - see manifest for unit"
    lines = ["// Generated portable handoff; Origin execution status: pending.",
             "// Download/extract the entire bundle before running in Origin.",
             '// run.section("C:\\data\\import_origin.ogs", Main, "C:\\data\\");',
             "// Pass exactly one Windows directory argument, including the final backslash.",
             "// Uses Origin CSV Data Connector. Verify import and plot against preview.png.",
             "// Each curve has its own workbook/graph. Source labels are in manifest.json.",
             "[Main]", "if (macro.narg != 1)", "{",
             '    type "Pass the extracted bundle directory, with final backslash, as one argument.";',
             "    return;", "}", 'string mpmsroot$ = "%1";']
    for curve in curves:
        lines.extend(["", f"// {curve['id']}: records {curve['start']}..{curve['end']}",
                      "newbook;", 'wbook.dc.add("CSV");',
                      f'wks.dc.source$ = mpmsroot$ + "{curve["id"]}.csv";',
                      "wks.dc.import();", "plotxy iy:=(1,2) plot:=200;",
                      f'label -xb "{xlabel}";', f'label -yl "{ylabel}";'])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_bundle(destination: Path, data: Dataset, curves, xcol: Column, moment: Column,
                  yunit: str, scaling, invocation: dict) -> dict:
    if destination.exists():
        raise DataError(f"Output already exists; choose a new output directory: {destination}")
    try:
        versions = {name: importlib.metadata.version(name) for name in ("openpyxl", "matplotlib")}
    except importlib.metadata.PackageNotFoundError as exc:
        raise DataError("Conversion needs openpyxl and matplotlib; install requirements.txt in the execution environment.") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    # The final directory appears only after every artifact succeeds. Never overwrite existing outputs.
    with tempfile.TemporaryDirectory(prefix="mpms-export-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "bundle"
        staging.mkdir()
        write_csvs(staging, data, curves)
        write_xlsx(staging / "magnetometry.xlsx", data, curves, xcol, moment, yunit, scaling)
        try:
            write_preview(staging / "preview.png", curves, xcol, yunit)
        except (ValueError, OverflowError) as exc:
            raise DataError(f"Cannot render the selected numeric range as a preview: {exc}") from exc
        write_ogs(staging / "import_origin.ogs", curves, xcol, yunit)
        notes = (
            "MPMS SUMMARY EXPORT / MPMS 汇总数据导出\n\n"
            "Read manifest.json for source hash, exact column selection, units, scaling, and segments.\n"
            "源文件哈希、实际表头、单位、归一化及段界见 manifest.json。\n"
            "All curves retain their own X and acquisition order. Blank numeric cells denote unavailable values.\n"
            "每条曲线独立保留 X 与采集顺序；空数值单元格表示缺失或非有限值。\n"
            "source_rows.csv lists all nonblank records. Rows outside target ranges have no curve assignment.\n"
            "source_rows.csv 保留全部非空源记录。目标范围外的记录仅保留来源追溯。\n"
            "No experimental labels, fits, background subtraction or quality filtering were inferred.\n"
            "实验标签由用户给出；本程序仅整理数据。\n"
            "Origin: download/extract all files, then run the Main section with the local directory argument.\n"
            "Origin: 下载并解压全部文件，按 OGS 顶部说明将本地目录作为参数运行 Main。\n"
            "CSV Data Connector and line graph behavior must be checked in the user's Origin version.\n"
            "Origin execution: pending. ChatGPT Work receiver execution: pending.\n"
        )
        (staging / "READ_ME.txt").write_text(notes, encoding="utf-8")
        files = [{"path": p.name, "size_bytes": p.stat().st_size,
                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(staging.iterdir()) if p.is_file()]
        curve_record_count = sum(len(c["points"]) for c in curves)
        manifest = {
            "schema_version": "1.0", "tool": "mpms-summary-to-origin", "tool_version": VERSION,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source": source_info(data), "record_count": len(data.records),
            "curve_record_count": curve_record_count,
            "outside_target_record_count": len(data.records) - curve_record_count,
            "columns": [column_dict(c, data.records) for c in data.columns],
            "selection": {"x": column_dict(xcol, data.records), "moment": column_dict(moment, data.records)},
            "scaling": scaling, "invocation": invocation,
            "segments": [{k: v for k, v in c.items() if k != "points"} for c in curves],
            "warnings": data.warnings + [
                "Experiment labels and curve boundaries are not inferred from direction changes.",
                "This export does not assess fit quality, remove outliers, or subtract backgrounds.",
            ],
            "mapping": {"record_numbering": "1-based nonblank CSV records after the column header",
                        "line_numbering": "1-based physical lines in original decoded source",
                        "csv_curve_header_lines": 1, "invalid_records": "retained with blank unavailable numeric cells",
                        "outside_target_ranges": "retained in source_rows.csv and Source_Rows with no curve assignment",
                        "blank_source_lines": "excluded from record numbering; ranges recorded in source",
                        "raw_cells_json": "original decoded tokens, before padding short rows",
                        "xlsx_text": "literal strings; formula interpretation disabled"},
            "runtime": {"python": platform.python_version(), **versions},
            "verification": {"chatgpt_work_receiver": "pending", "origin_execution": "pending",
                             "preview": "matplotlib headless rendering; not an Origin screenshot"},
            "artifacts": files,
        }
        (staging / "manifest.json").write_text(json_text(manifest), encoding="utf-8")
        staging.rename(destination)
    return manifest
