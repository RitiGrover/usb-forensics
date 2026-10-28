#!/usr/bin/env python3
"""Create the synthetic demo folder used in the report.

    python make_demo_folder.py            # builds ./usb_forensics_demo (4 files)
    python make_demo_folder.py --change   # modifies notes.txt and adds new_file.txt
"""

import argparse
from pathlib import Path

DEMO = Path("usb_forensics_demo")


def build():
    (DEMO / "docs").mkdir(parents=True, exist_ok=True)
    (DEMO / "notes.txt").write_text("Meeting notes: initial version.\n")
    (DEMO / "report.txt").write_text("Quarterly report contents.\n")
    (DEMO / "report_copy.txt").write_text("Quarterly report contents.\n")
    (DEMO / "docs" / "placeholder.bin").write_bytes(bytes(range(64)))


def change():
    (DEMO / "notes.txt").write_text("Meeting notes: edited after the baseline scan.\n")
    (DEMO / "new_file.txt").write_text("Added after the baseline scan.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--change", action="store_true")
    args = parser.parse_args()
    change() if args.change else build()
    print(f"demo folder ready: {DEMO.resolve()}")
