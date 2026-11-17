"""Parse Quantum Design summary DAT files without interpreting experiment labels.

No optional dependencies: inspection works with Python's standard library alone.
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VERSION = "0.1.0"


class DataError(ValueError):
    """An actionable input or configuration error."""


@dataclass
class Column:
    index: int
    header: str
    name: str
    unit: str | None
    role: str


@dataclass
class Record:
    number: int
    line_start: int
    line_end: int
    cells: list[str]
    width: int


@dataclass
class Dataset:
    path: Path
    sha256: str
    size_bytes: int
    encoding: str
    delimiter: str
    data_marker_line: int
    header_start: int
    header_end: int
    columns: list[Column]
    records: list[Record]
    blank_line_ranges: list[list[int]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def number(text: str) -> float | None:
    """Only finite numbers; retain original tokens elsewhere for traceability."""
    try:
        value = float(text.strip().replace("D", "E").replace("d", "e"))
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def split_header(header: str) -> tuple[str, str | None]:
    match = re.match(r"^(.*?)\s*[\[(]([^\[\]()]+)[\])]\s*$", header.strip())
    if match:
        return match[1].strip(), match[2].strip()
    return header.strip(), None


def role_of(name: str) -> str:
    name = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    words = set(name.split())
    if name in {"temperature", "sample temperature"}:
        return "temperature"
    if name in {"magnetic field", "field"}:
        return "field"
    if "moment" in words or name in {"m std err", "m standard error"}:
        if words & {"err", "error", "stderr", "std", "uncertainty"}:
            return "moment_error"
        return "moment"
    return "other"


def load_dat(path: str | Path, encoding: str | None = None,
             delimiter: str | None = None) -> Dataset:
    path = Path(path)
    if path.name.lower().endswith(".rw.dat"):
        raise DataError("Raw voltage scans (.rw.dat) are unsupported. Supply a summary DAT.")
    raw = path.read_bytes()
    chosen = encoding
    if chosen is None:
        for candidate in ("utf-8-sig", "cp1252"):
            try:
                text = raw.decode(candidate)
                chosen = candidate
                break
            except UnicodeDecodeError:
                continue
        else:
            raise DataError("Cannot decode input. Provide --encoding explicitly.")
    else:
        try:
            text = raw.decode(chosen)
        except (UnicodeDecodeError, LookupError) as exc:
            raise DataError(f"Cannot decode with {chosen}: {exc}") from exc
    if "\x00" in text:
        raise DataError("NUL bytes found; select the correct text encoding, e.g. utf-16.")
    lines = text.splitlines(keepends=True)
    markers = [i for i, line in enumerate(lines) if line.strip().lower() == "[data]"]
    if len(markers) != 1:
        raise DataError(f"Expected one [Data] section, found {len(markers)}; repeated/raw blocks unsupported.")
    marker = markers[0]
    first = next((i for i in range(marker + 1, len(lines)) if lines[i].strip()), None)
    if first is None:
        raise DataError("No column header after [Data].")
    if delimiter is None:
        counts = {sep: len(next(csv.reader([lines[first]], delimiter=sep))) for sep in (",", "\t")}
        best = max(counts.values())
        matches = [sep for sep, count in counts.items() if count == best]
        if best < 2 or len(matches) != 1:
            raise DataError("Cannot uniquely discover comma/tab separator; use --delimiter comma|tab.")
        delimiter = matches[0]
    reader = csv.reader(io.StringIO("".join(lines[first:]), newline=""), delimiter=delimiter, strict=True)
    try:
        headers = next(reader)
        header_end = first + reader.line_num
        columns = []
        for i, header in enumerate(headers, 1):
            name, unit = split_header(header)
            columns.append(Column(i, header, name, unit, role_of(name)))
        names = {re.sub(r"[^a-z]+", " ", c.name.lower()).strip() for c in columns}
        if any("voltage" in name for name in names) and any("position" in name for name in names):
            raise DataError("Position/voltage scan schema detected; raw scan data are unsupported.")
        records, blank_ranges = [], []
        previous = reader.line_num
        for cells in reader:
            start, end = first + previous + 1, first + reader.line_num
            previous = reader.line_num
            if not cells or all(not c.strip() for c in cells):
                blank_ranges.append([start, end])
                continue
            width = len(cells)
            records.append(Record(len(records) + 1, start, end,
                                  cells + [""] * max(0, len(headers) - width), width))
    except csv.Error as exc:
        raise DataError(f"Malformed CSV near physical line {first + reader.line_num}: {exc}") from exc
    if not records:
        raise DataError("The [Data] section has no nonblank records.")
    warnings = []
    if chosen == "cp1252":
        warnings.append("UTF-8 decoding failed; cp1252 was used. Check non-ASCII text or set --encoding.")
    if any(r.width != len(headers) for r in records):
        warnings.append("Some records have a different field count; inspect row_width_issues.")
    return Dataset(path, hashlib.sha256(raw).hexdigest(), len(raw), chosen,
                   delimiter, marker + 1, first + 1, header_end, columns,
                   records, blank_ranges, warnings)


def column_dict(col: Column, records: list[Record]) -> dict[str, Any]:
    values = [number(r.cells[col.index - 1]) for r in records]
    finite = [x for x in values if x is not None]
    return {"index": col.index, "header": col.header, "name": col.name,
            "unit": col.unit, "role": col.role, "finite_count": len(finite),
            "missing_or_nonfinite_count": len(values) - len(finite),
            "minimum": min(finite) if finite else None, "maximum": max(finite) if finite else None}


def inspect_dataset(data: Dataset) -> dict[str, Any]:
    cols = [column_dict(c, data.records) for c in data.columns]
    candidates = {role: [c["index"] for c in cols if c["role"] == role and c["finite_count"]]
                  for role in ("temperature", "field", "moment", "moment_error")}
    ambiguity = []
    for role in ("temperature", "field", "moment"):
        if len(candidates[role]) > 1:
            ambiguity.append(f"Multiple usable {role} columns: {candidates[role]}; select an exact header or index.")
    if not candidates["moment"]:
        ambiguity.append("No recognized finite magnetic moment column; review all headers and select explicitly.")
    # Direction changes are descriptive only. No tolerance, grouping or experimental label is inferred.
    directions = {}
    for col in data.columns:
        if col.role not in {"temperature", "field"}:
            continue
        previous = previous_sign = None
        changes, gaps = [], []
        for row in data.records:
            value = number(row.cells[col.index - 1])
            if value is None:
                gaps.append(row.number)
                previous = previous_sign = None
                continue
            if previous is not None:
                sign = (value > previous) - (value < previous)
                if sign and previous_sign and sign != previous_sign:
                    changes.append(row.number)
                if sign:
                    previous_sign = sign
            previous = value
        directions[str(col.index)] = {"exact_direction_change_records": changes, "gap_records": gaps}
    return {"schema_version": "1.0", "tool_version": VERSION,
            "source": source_info(data), "record_count": len(data.records),
            "columns": cols, "candidates": candidates, "ambiguities": ambiguity,
            "direction_diagnostics": directions,
            "row_width_issues": [{"record": r.number, "line_start": r.line_start,
                                   "expected": len(data.columns), "actual": r.width}
                                  for r in data.records if r.width != len(data.columns)],
            "warnings": data.warnings,
            "segmentation": "Single segment unless explicit ranges supplied; direction changes do not identify experiments.",
            "segment_template": {"segments": [{"start": 1, "end": len(data.records), "label": ""}]}}


def source_info(data: Dataset) -> dict[str, Any]:
    return {"filename": data.path.name, "sha256": data.sha256, "size_bytes": data.size_bytes,
            "encoding": data.encoding, "delimiter": "tab" if data.delimiter == "\t" else "comma",
            "data_marker_line": data.data_marker_line,
            "column_header_lines": [data.header_start, data.header_end],
            "blank_data_line_ranges": data.blank_line_ranges}


def select_column(data: Dataset, selector: str | None, role: str | None = None) -> Column:
    if selector is not None:
        if selector.isdecimal():
            selected = [c for c in data.columns if c.index == int(selector)]
        else:
            selected = [c for c in data.columns if c.header == selector]
        if len(selected) != 1:
            raise DataError(f"Column selector {selector!r} matches {len(selected)} columns; use a 1-based index.")
        return selected[0]
    selected = [c for c in data.columns if c.role == role and
                any(number(r.cells[c.index - 1]) is not None for r in data.records)]
    if len(selected) != 1:
        raise DataError(f"Expected one usable {role} column, found {len(selected)}; use --x-column.")
    return selected[0]


def segments_from_config(config: Any, count: int) -> list[dict[str, Any]]:
    if config is None:
        return [{"id": "curve_001", "start": 1, "end": count, "label": "", "origin": "default_single_segment"}]
    if not isinstance(config, dict) or set(config) != {"segments"} or not isinstance(config["segments"], list):
        raise DataError('Segment file must be an object with only a "segments" array.')
    segments, expected = [], 1
    for i, spec in enumerate(config["segments"], 1):
        if not isinstance(spec, dict) or not {"start", "end"} <= set(spec) or set(spec) - {"start", "end", "label"}:
            raise DataError("Each segment accepts only start, end, and optional label.")
        start, end, label = spec["start"], spec["end"], spec.get("label", "")
        if type(start) is not int or type(end) is not int or start != expected or end < start or end > count:
            raise DataError("Segments must cover records 1..N exactly once, contiguously, in acquisition order.")
        if not isinstance(label, str):
            raise DataError("Segment labels must be strings.")
        segments.append({"id": f"curve_{i:03d}", "start": start, "end": end,
                         "label": label, "origin": "explicit_user_ranges"})
        expected = end + 1
    if expected != count + 1:
        raise DataError("Segments must cover every nonblank data record (including invalid measurements).")
    return segments


def moment_emu_factor(unit: str | None) -> float:
    canonical = re.sub(r"[\s·*^]", "", (unit or "").lower().replace("²", "2"))
    if canonical == "emu":
        return 1.0
    if canonical in {"am2", "a.m2"}:
        return 1000.0
    raise DataError(f"Cannot mass-normalize moment unit {unit!r}. Use --moment-unit emu or A*m^2 after verifying the source.")


def build_curves(data: Dataset, xcol: Column, moment: Column,
                 segments: list[dict[str, Any]], mass_mg: float | None,
                 moment_unit: str | None = None) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    if any(r.width > len(data.columns) for r in data.records):
        raise DataError("Records have extra fields beyond the header. Resolve row_width_issues before conversion.")
    if mass_mg is not None and (not math.isfinite(mass_mg) or mass_mg <= 0):
        raise DataError("--mass-mg must be a positive finite number supplied by the user.")
    unit = moment_unit or moment.unit
    emu_factor = moment_emu_factor(unit) if mass_mg is not None else None
    mass_g = mass_mg / 1000.0 if mass_mg is not None else None
    if mass_g is not None and mass_g == 0:
        raise DataError("Mass is too small to represent in grams.")
    scale = emu_factor / mass_g if mass_g is not None else 1.0
    if not math.isfinite(scale):
        raise DataError("Mass is too small to represent the normalization factor.")
    yunit = "emu/g" if mass_mg is not None else (unit or "source unit unspecified")
    curves = []
    for segment in segments:
        points = []
        for record in data.records[segment["start"] - 1:segment["end"]]:
            x, raw = number(record.cells[xcol.index - 1]), number(record.cells[moment.index - 1])
            y = raw * scale if raw is not None else None
            reasons = []
            if x is None:
                reasons.append("missing_or_nonfinite_x")
            if raw is None:
                reasons.append("missing_or_nonfinite_moment")
            if y is not None and not math.isfinite(y):
                raise DataError(f"Normalization overflow at record {record.number}.")
            points.append({"record": record, "x": x, "moment": raw, "y": y,
                           "status": "valid" if not reasons else ";".join(reasons)})
        valid = sum(p["status"] == "valid" for p in points)
        if not valid:
            raise DataError(f"{segment['id']} has no finite X/moment pairs. Check columns and ranges.")
        curves.append({**segment, "points": points, "valid_pairs": valid,
                       "invalid_pairs": len(points) - valid})
    scaling = {"mode": "mass_normalized" if mass_mg is not None else "raw",
               "mass_mg": mass_mg, "mass_g": mass_g,
               "source_header_unit": moment.unit, "effective_moment_unit": unit,
               "unit_override": moment_unit, "moment_to_emu_factor": emu_factor,
               "output_multiplier": scale, "output_unit": yunit,
               "formula": "moment * moment_to_emu_factor / (mass_mg / 1000)" if mass_mg is not None else "moment unchanged"}
    return curves, yunit, scaling
