"""Censored phone-scanning entry point for Aliens Eye."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from aliens_eye.phone_scanner import scan_numbers


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan text or files for phone numbers.")
    parser.add_argument("source", nargs="*", help="Text or file paths to scan.")
    parser.add_argument(
        "--formats",
        default="json",
        help="Output formats: json,csv,txt,all",
    )
    parser.add_argument("--output", default=None, help="Output directory.")
    parser.add_argument("--region", default="CN", help="Default region code.")
    parser.add_argument("--valid-only", action="store_true", help="Return valid numbers only.")
    parser.add_argument("--label", default="", help="Optional label for outputs.")
    return parser.parse_args(argv)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def iter_inputs(text: str, sources: Iterable[str]) -> Iterable[str]:
    if sources:
        for source in sources:
            path = Path(source)
            if path.exists() and path.is_file():
                yield from read_text(path).splitlines()
            else:
                yield source
    else:
        if sys.stdin.isatty():
            print("Enter text, then Ctrl-D:")
        yield from sys.stdin.read().splitlines()


def fmt_results(results, summary, fmt, label):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"phone_scan_{stamp}"
    if label:
        base = f"{base}_{label}"

    lines = []
    for item in results:
        lines.append(
            f"[{item.get('region','')}] {item.get('e164','')} | {item.get('type','')} | valid={item.get('valid',0)} | carrier={item.get('carrier','')}"
        )
    text = "\n".join(lines)
    payload = {
        "results": results,
        "summary": summary,
        "label": label,
        "generated_at": datetime.now().isoformat(),
    }
    out = Path("." if fmt == "txt" else (fmt or "."))
    if fmt in {"json", "all"}:
        Path(base + ".json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if fmt in {"csv", "all"}:
        with Path(base + ".csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()) if results else [])
            writer.writeheader()
            writer.writerows(results)
    if fmt in {"txt", "all"}:
        Path(base + ".txt").write_text(text, encoding="utf-8")
    return base, payload


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    sources = list(args.source)
    candidates = [line for line in iter_inputs("", sources) if line.strip()]
    if not candidates:
        return 0
    formats = [item.strip().lower() for item in args.formats.split(",") if item.strip()]
    if not formats:
        formats = ["json"]
    if "all" in formats:
        formats = ["json", "csv", "txt"]
    results, summary = scan_numbers(candidates, args.region, dedupe=True, only_valid=args.valid_only)
    for fmt in formats:
        base, payload = fmt_results(results, summary, fmt, args.label)
        print(f"[{fmt}] wrote {base}")
    print("summary=", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
