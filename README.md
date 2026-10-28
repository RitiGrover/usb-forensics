# USB Forensics and File Integrity Analysis

**Live demo: https://usb-forensics-six.vercel.app/**

A Python tool and a drag-and-drop website for examining the files on a USB drive or any folder. It answers three questions:

- What files are here, and what are their sizes and timestamps?
- Which files have identical contents, even under different names?
- What changed since the last time this folder was examined?

It is an educational logical file-analysis tool, not a full forensic acquisition suite (see [Limitations](#limitations)).

## Try it

Open the [live demo](https://usb-forensics-six.vercel.app/), then drag a folder onto the frame or click **Run sample**. Everything runs in your browser and no files are uploaded. A `manifest.json` from an earlier scan can be dropped in as a baseline to see what changed.

## What it does

1. Walks a folder recursively and records each file's path, name, extension, size and timestamps.
2. Computes a SHA-256 hash of every file, reading in 1 MB chunks.
3. Groups files with matching hashes as duplicates.
4. Writes `forensic_report.csv` and a reusable `manifest.json`.
5. Compares a scan with an earlier manifest and labels each path `ADDED`, `REMOVED`, `MODIFIED` or `UNCHANGED`.

Unreadable files are recorded with an error and the scan continues. Symbolic links are skipped. The scanned folder is opened read-only.

## Command line

Python 3, no packages needed.

```bash
python usb_forensics_analyzer.py <directory> [--out <folder>] [--baseline <manifest.json>]
```

Scan, change something, then scan again and compare:

```bash
python usb_forensics_analyzer.py ./test_usb --out first_scan
python usb_forensics_analyzer.py ./test_usb --out second_scan --baseline first_scan/manifest.json
```

To try it without your own files, `python make_demo_folder.py` builds a small demo folder, and `python make_demo_folder.py --change` edits it afterwards. `python make_sample_usb.py` builds a larger sample with nested folders and duplicates. To run the website locally, use `python serve.py`.

## Output files

| File | Contents |
| --- | --- |
| `forensic_report.csv` | One row per file: path, name, extension, size, timestamps, SHA-256, duplicate flag and group, error |
| `manifest.json` | Scan metadata and all file records, used as a baseline later |
| `integrity_comparison.csv` | Per path: status, baseline hash and current hash |

## Tests

```bash
python -m unittest -v
```

## Limitations

- **Not a forensic image.** It reads files the OS shows, not raw sectors, unallocated space or deleted files.
- **No write blocking.** Use a hardware or validated write blocker for real evidence.
- **Timestamps are not proof.** They can be changed and vary by filesystem. The website can only read the last-modified time.
- **A hash is not authorship.** Matching hashes mean matching bytes. A changed hash means different bytes, not wrongdoing.
- **Path-based comparison.** A renamed file shows as one removed and one added path.
- **Not a chain of custody.** A CSV or manifest alone is not an evidence record.
- **Browser limit.** The website does not hash files over 256 MB.

Only scan media you own or are authorised to examine. Reports contain file names and paths, which can themselves be sensitive.
