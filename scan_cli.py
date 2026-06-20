"""CLI runner for batch plagiarism scan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from checker.analyzer import analyze_document
from checker.export_docx import COPYRIGHT, export_report_docx
from checker.extractor import extract_paragraphs
from checker.fix_docx import generate_fixed_docx


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="IEEE Plagiarism Checker CLI")
    parser.add_argument("docx", nargs="?", default="HTTL-NEW.docx", help="Path to .docx file")
    parser.add_argument(
        "--mode",
        choices=["quick", "standard", "thorough"],
        default="standard",
        help="Scan depth",
    )
    parser.add_argument("--output", "-o", help="Save JSON report to file")
    parser.add_argument("--word", "-w", help="Save Word (.docx) report to file")
    parser.add_argument(
        "--fix",
        "-f",
        help="Auto-paraphrase flagged paragraphs and save fixed .docx (requires scan)",
    )
    args = parser.parse_args()

    path = Path(args.docx)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {path.name} ({args.mode} mode)...")
    paragraphs = extract_paragraphs(str(path))

    def progress(cur, total, preview):
        print(f"\r  [{cur}/{total}] {preview[:60]}...", end="", flush=True)

    report = analyze_document(paragraphs, path.name, scan_mode=args.mode, progress_callback=progress)
    print()

    print(f"\n{'='*50}")
    print(f"  Plagiarism:  {report.plagiarism_percent}%")
    print(f"  Originality: {report.originality_percent}%")
    print(f"  Analyzed:    {report.analyzed_paragraphs} paragraphs")
    print(f"  Duration:    {report.duration_seconds}s")
    print(f"{'='*50}\n")

    flagged = [p for p in report.paragraphs if p.similarity >= 38]
    flagged.sort(key=lambda p: -p.similarity)

    print("Flagged paragraphs:")
    for p in flagged[:15]:
        print(f"  #{p.index} [{p.risk.value}] {p.similarity}% - {p.section}")
        if p.suggestions:
            print(f"    > {p.suggestions[0][:100]}")

    if args.output:
        data = {
            "copyright": COPYRIGHT,
            "plagiarism_percent": report.plagiarism_percent,
            "originality_percent": report.originality_percent,
            "paragraphs": [
                {
                    "index": p.index,
                    "similarity": p.similarity,
                    "risk": p.risk.value,
                    "section": p.section,
                    "suggestions": p.suggestions,
                }
                for p in report.paragraphs
                if p.similarity > 0
            ],
        }
        Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON report saved to {args.output}")

    if args.word:
        Path(args.word).write_bytes(export_report_docx(report))
        print(f"Word report saved to {args.word}")

    if args.fix:
        fix_path = args.fix
        fixed_bytes, stats = generate_fixed_docx(str(path), report)
        Path(fix_path).write_bytes(fixed_bytes)
        print(f"Fixed document saved to {fix_path}")
        print(f"  Modified: {stats.paragraphs_modified} paragraphs")
        print(f"  Unchanged: {stats.paragraphs_unchanged} paragraphs")
        print(f"  Indices: {stats.modified_indices[:15]}{'...' if len(stats.modified_indices)>15 else ''}")


if __name__ == "__main__":
    main()
