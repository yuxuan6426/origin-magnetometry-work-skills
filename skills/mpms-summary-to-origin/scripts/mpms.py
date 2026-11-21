#!/usr/bin/env python3
"""Inspect/convert MPMS summary DAT. Run --help for the portable CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mpms_core import (DataError, VERSION, build_curves, inspect_dataset, load_dat,
                       segments_from_config, select_column, target_segments)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--version", action="version", version=VERSION)
    commands = root.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Report actual columns, units, candidate ambiguity and source rows")
    convert = commands.add_parser("convert", help="Write XLSX, curve CSVs, source mapping, manifest, PNG and Origin OGS")
    for command in (inspect, convert):
        command.add_argument("input", type=Path, help="Quantum Design summary DAT; .rw.dat unsupported")
        command.add_argument("--encoding", help="Explicit Python encoding name; default UTF-8 BOM, then cp1252")
        command.add_argument("--delimiter", choices=("comma", "tab"), help="Override comma/tab detection")
    inspect.add_argument("--output", type=Path, help="New inspection JSON path (default stdout)")
    convert.add_argument("--output", required=True, type=Path, help="New output directory; never overwritten")
    convert.add_argument("--moment-column", required=True, help="Exact actual header or 1-based column index")
    axis = convert.add_mutually_exclusive_group(required=True)
    axis.add_argument("--x", choices=("temperature", "field"), help="Resolve a unique numeric axis candidate")
    axis.add_argument("--x-column", help="Exact actual X header or 1-based column index")
    mass = convert.add_mutually_exclusive_group(required=True)
    mass.add_argument("--mass-mg", type=float, help="Positive sample mass in mg explicitly supplied by the user")
    mass.add_argument("--raw", action="store_true", help="Keep unnormalized moment values and source moment unit")
    convert.add_argument("--moment-unit", choices=("emu", "A*m^2"), help="Explicit verified source unit override")
    ranges = convert.add_mutually_exclusive_group()
    ranges.add_argument("--segments", type=Path, help="JSON record ranges covering all records once; default one segment")
    ranges.add_argument("--target-range", type=int, nargs=2, metavar=("START", "END"), action="append",
                        help="Export an inclusive source-record range; repeat in source order for other curves")
    return root


def run(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        separator = {"comma": ",", "tab": "\t"}.get(args.delimiter)
        data = load_dat(args.input, args.encoding, separator)
        if args.command == "inspect":
            report = json.dumps(inspect_dataset(data), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            if args.output:
                with args.output.open("x", encoding="utf-8") as handle:
                    handle.write(report)
                print(f"Inspection written: {args.output}")
            else:
                print(report, end="")
            return 0
        moment = select_column(data, args.moment_column)
        if moment.role == "moment_error":
            raise DataError("Selected column is an uncertainty/error column; select the magnetic moment itself.")
        xcol = select_column(data, args.x_column, args.x)
        if xcol.index == moment.index:
            raise DataError("X and moment must be different columns.")
        if args.target_range:
            segments = target_segments(args.target_range, len(data.records))
            segment_mode = "explicit target ranges"
        else:
            config = json.loads(args.segments.read_text(encoding="utf-8-sig")) if args.segments else None
            segments = segments_from_config(config, len(data.records))
            segment_mode = "explicit JSON ranges" if args.segments else "default single segment"
        curves, yunit, scaling = build_curves(data, xcol, moment, segments, args.mass_mg, args.moment_unit)
        from mpms_export import export_bundle
        invocation = {"moment_column": args.moment_column, "x": args.x, "x_column": args.x_column,
                      "mass_mg": args.mass_mg, "raw": args.raw, "moment_unit": args.moment_unit,
                      "segments": segment_mode}
        if args.target_range:
            invocation["target_ranges"] = args.target_range
        result = export_bundle(args.output, data, curves, xcol, moment, yunit, scaling, invocation)
        print(json.dumps({"output": str(args.output), "curves": len(curves),
                          "records": len(data.records), "curve_records": result["curve_record_count"], "unit": yunit,
                          "work_receiver": result["verification"]["chatgpt_work_receiver"],
                          "origin_execution": result["verification"]["origin_execution"]}, ensure_ascii=False))
        return 0
    except (DataError, OSError, UnicodeError, json.JSONDecodeError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
