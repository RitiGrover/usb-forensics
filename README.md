# USB Forensics and File Integrity Analysis

A small Python tool, plus a drag-and-drop demo website, for examining the files on a USB drive (or any folder). It answers three questions:

- What files are here, and what are their sizes and timestamps?
- Which files have identical contents, even under different names?
- What changed since the last time this folder was examined?

It is an educational logical file-analysis tool, not a full forensic acquisition suite (see [Limitations](#limitations)).

## What it does

1. Walks a directory recursively and records each file's relative path, name, extension, size and timestamps.
2. Computes a SHA-256 hash of every file, reading in 1 MB chunks.
3. Groups files with matching hashes as duplicate-content groups.
4. Writes `forensic_report.csv` (one row per file) and `manifest.json` (a reusable snapshot of the scan).
5. Compares a scan against an earlier `manifest.json` and labels each path `ADDED`, `REMOVED`, `MODIFIED` or `UNCHANGED`.

Files that cannot be read are recorded with an error and the scan carries on. Symbolic links are skipped. The scanned folder is opened read-only.

## Requirements

Python 3. There are no third-party packages.

## Command-line usage

```bash
python usb_forensics_analyzer.py <directory> [--out <folder>] [--baseline <manifest.json>]
```

- `--out` sets the output folder (default `forensic_output`).
- `--baseline` compares against a `manifest.json` from an earlier scan and also writes `integrity_comparison.csv`.

Example: scan, change something, scan again and compare.

```bash
python usb_forensics_analyzer.py ./test_usb --out first_scan
# change, add or delete a file in ./test_usb
python usb_forensics_analyzer.py ./test_usb --out second_scan --baseline first_scan/manifest.json
```

### Demo folder

```bash
python make_demo_folder.py            # builds usb_forensics_demo (4 files, one duplicate pair)
python usb_forensics_analyzer.py usb_forensics_demo --out first_scan
python make_demo_folder.py --change   # edits notes.txt and adds new_file.txt
python usb_forensics_analyzer.py usb_forensics_demo --out second_scan --baseline first_scan/manifest.json
```

The second scan reports 1 added, 1 modified and 3 unchanged.

A larger sample with nested folders and two duplicate pairs can be generated with:

```bash
python make_sample_usb.py             # builds sample_usb_drive
```

## Demo website

The website scans a folder you drop onto it. Everything runs in the browser; no files are uploaded.

```bash
python serve.py                       # serves website/ at http://localhost:5173
```

- Drag a folder onto the frame, or use **Choose folder**.
- **Run sample** and **Simulate edits** reproduce the demo folder scan without needing a folder.
- A `manifest.json` from the website or the command line can be dropped in as the baseline.
- The report can be downloaded as `forensic_report.csv` or `manifest.json`.

The browser only exposes the last-modified time, so the website's report leaves the OS-dependent metadata time blank. Files larger than 256 MB are not hashed in the browser.

## Output files

| File | Contents |
| --- | --- |
| `forensic_report.csv` | One row per file: path, filename, extension, size, modified time, OS-dependent metadata time, SHA-256, duplicate flag and group, error |
| `manifest.json` | Scan metadata and every file record, used as a baseline for later comparisons |
| `integrity_comparison.csv` | Per path: status (`ADDED`, `REMOVED`, `MODIFIED`, `UNCHANGED`), baseline hash and current hash |

## Tests

```bash
python -m unittest -v
```

The tests cover scanning, metadata fields, duplicate detection, each baseline status, invalid input, read errors and that scanned files are left unmodified.

## Limitations

- **Not a forensic image.** It reads files the operating system shows. It does not read raw sectors, unallocated space or deleted files.
- **No write blocking.** Opening files can still update access times on some systems. Use a hardware or validated write blocker for real evidence.
- **Timestamps are not proof.** They can be changed and mean different things on different filesystems.
- **A hash is not authorship.** Matching hashes mean matching bytes. A changed hash means different bytes, not wrongdoing.
- **Path-based comparison.** A renamed file shows as one removed path and one added path.
- **Not a chain of custody.** A CSV or manifest alone is not an evidence record.

Only scan media you own or are authorised to examine. Reports contain file names and paths, which can themselves be sensitive.
