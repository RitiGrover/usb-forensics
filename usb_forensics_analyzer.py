#!/usr/bin/env python3
"""USB Forensics and File Integrity Analysis System.

Scans a directory (a mounted USB drive or a prepared test folder), records file
metadata, computes SHA-256 hashes, groups files with identical content, writes
a CSV report and a JSON manifest, and optionally compares the scan against an
earlier manifest.

Only the Python standard library is used. Files are opened read-only.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CHUNK_SIZE = 1024 * 1024  # 1 MB

REPORT_FIELDS = [
    "relative_path",
    "filename",
    "extension",
    "size_bytes",
    "modified_time",
    "metadata_time_os_dependent",
    "sha256",
    "duplicate",
    "duplicate_group",
    "error",
]


def sha256_file(path):
    """Return the SHA-256 hex digest of a file, read in 1 MB chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _iso(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(timespec="seconds")


def scan_directory(root):
    """Walk root and return one record per regular file.

    Symlinks are skipped. A file that cannot be read gets an empty digest and
    an error message, and the scan continues.
    """
    root = Path(root)
    if not root.exists():
        raise ValueError(f"path does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"path is not a directory: {root}")

    records = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not os.path.islink(os.path.join(dirpath, d)))
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            record = {
                "relative_path": Path(full).relative_to(root).as_posix(),
                "filename": name,
                "extension": Path(name).suffix.lower().lstrip("."),
                "size_bytes": "",
                "modified_time": "",
                "metadata_time_os_dependent": "",
                "sha256": "",
                "duplicate": "no",
                "duplicate_group": "",
                "error": "",
            }
            try:
                stat = os.stat(full)
                record["size_bytes"] = stat.st_size
                record["modified_time"] = _iso(stat.st_mtime)
                record["metadata_time_os_dependent"] = _iso(stat.st_ctime)
                record["sha256"] = sha256_file(full)
            except OSError as exc:
                record["error"] = f"{type(exc).__name__}: {exc.strerror or exc}"
            records.append(record)
    return records


def mark_duplicates(records):
    """Flag records that share a non-empty digest; return the number flagged."""
    groups = defaultdict(list)
    for record in records:
        if record["sha256"]:
            groups[record["sha256"]].append(record["relative_path"])
    flagged = 0
    for record in records:
        members = groups.get(record["sha256"], [])
        if record["sha256"] and len(members) > 1:
            record["duplicate"] = "yes"
            record["duplicate_group"] = "; ".join(members)
            flagged += 1
    return flagged


def write_csv(records, path):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(records)


def write_manifest(records, root, path):
    manifest = {
        "tool": "usb_forensics_analyzer",
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(Path(root).resolve()),
        "file_count": len(records),
        "files": records,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)


def compare_manifests(baseline, records):
    """Compare a baseline manifest dict with current records, path by path."""
    old = {f["relative_path"]: f.get("sha256", "") for f in baseline.get("files", [])}
    new = {r["relative_path"]: r["sha256"] for r in records}
    rows = []
    for path in sorted(set(old) | set(new)):
        if path not in old:
            status = "ADDED"
        elif path not in new:
            status = "REMOVED"
        elif old[path] != new[path]:
            status = "MODIFIED"
        else:
            status = "UNCHANGED"
        rows.append(
            {
                "relative_path": path,
                "status": status,
                "baseline_sha256": old.get(path, ""),
                "current_sha256": new.get(path, ""),
            }
        )
    return rows


def write_comparison(rows, path):
    fields = ["relative_path", "status", "baseline_sha256", "current_sha256"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_parser():
    parser = argparse.ArgumentParser(
        description="USB forensics and file integrity analysis (logical, read-only)."
    )
    parser.add_argument("directory", help="directory to examine (USB drive or test folder)")
    parser.add_argument("--out", default="forensic_output", help="output folder (default: forensic_output)")
    parser.add_argument("--baseline", help="manifest.json from an earlier scan to compare against")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    baseline = None
    if args.baseline:
        try:
            with open(args.baseline, encoding="utf-8") as handle:
                baseline = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read baseline manifest: {exc}", file=sys.stderr)
            return 2

    try:
        records = scan_directory(args.directory)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    duplicates = mark_duplicates(records)
    errors = sum(1 for r in records if r["error"])

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "forensic_report.csv"
    manifest_path = out_dir / "manifest.json"
    write_csv(records, csv_path)
    write_manifest(records, args.directory, manifest_path)

    print("USB FORENSICS AND FILE INTEGRITY ANALYSIS")
    print(f"Input directory : {args.directory}")
    print(f"Files recorded  : {len(records)}")
    print(f"Scan errors     : {errors}")
    print(f"Duplicate files : {duplicates}")
    print(f"CSV report      : {csv_path}")
    print(f"JSON manifest   : {manifest_path}")

    if baseline is not None:
        rows = compare_manifests(baseline, records)
        comparison_path = out_dir / "integrity_comparison.csv"
        write_comparison(rows, comparison_path)
        counts = defaultdict(int)
        for row in rows:
            counts[row["status"]] += 1
        print("Baseline comparison:")
        print(f"  ADDED    : {counts['ADDED']}")
        print(f"  REMOVED  : {counts['REMOVED']}")
        print(f"  MODIFIED : {counts['MODIFIED']}")
        print(f"  UNCHANGED: {counts['UNCHANGED']}")
        print(f"Comparison CSV  : {comparison_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
