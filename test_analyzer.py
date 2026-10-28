import csv
import json
import os
import tempfile
import unittest
from pathlib import Path

import usb_forensics_analyzer as ufa


def make_tree(root):
    root = Path(root)
    (root / "sub").mkdir()
    (root / "a.txt").write_text("alpha")
    (root / "b.txt").write_text("beta")
    (root / "b_copy.txt").write_text("beta")
    (root / "sub" / "c.bin").write_bytes(b"\x00\x01\x02")


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "usb"
        self.root.mkdir()
        make_tree(self.root)
        self.out = Path(self._tmp.name) / "out"

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *extra):
        return ufa.main([str(self.root), "--out", str(self.out), *extra])

    def test_valid_scan_writes_reports(self):  # TC-01
        self.assertEqual(self.run_cli(), 0)
        self.assertTrue((self.out / "forensic_report.csv").exists())
        self.assertTrue((self.out / "manifest.json").exists())

    def test_metadata_fields_populated(self):  # TC-02
        records = ufa.scan_directory(self.root)
        self.assertEqual(len(records), 4)
        for r in records:
            self.assertTrue(r["size_bytes"] != "" and r["modified_time"] and len(r["sha256"]) == 64)
        self.assertIn("sub/c.bin", {r["relative_path"] for r in records})

    def test_duplicates_flagged(self):  # TC-03
        records = ufa.scan_directory(self.root)
        self.assertEqual(ufa.mark_duplicates(records), 2)
        dup = {r["relative_path"]: r for r in records if r["duplicate"] == "yes"}
        self.assertEqual(set(dup), {"b.txt", "b_copy.txt"})
        self.assertEqual(dup["b.txt"]["duplicate_group"], dup["b_copy.txt"]["duplicate_group"])

    def test_baseline_statuses(self):  # TC-04 to TC-07
        self.run_cli()
        (self.root / "a.txt").write_text("alpha changed")
        (self.root / "new.txt").write_text("new")
        (self.root / "b_copy.txt").unlink()
        second = Path(self._tmp.name) / "second"
        ufa.main([str(self.root), "--out", str(second), "--baseline", str(self.out / "manifest.json")])
        with open(second / "integrity_comparison.csv", newline="") as fh:
            status = {r["relative_path"]: r["status"] for r in csv.DictReader(fh)}
        self.assertEqual(status["a.txt"], "MODIFIED")
        self.assertEqual(status["new.txt"], "ADDED")
        self.assertEqual(status["b_copy.txt"], "REMOVED")
        self.assertEqual(status["b.txt"], "UNCHANGED")

    def test_invalid_input(self):  # TC-08
        self.assertEqual(ufa.main([str(self.root / "nope"), "--out", str(self.out)]), 2)
        self.assertEqual(ufa.main([str(self.root / "a.txt"), "--out", str(self.out)]), 2)

    def test_read_error_is_recorded(self):  # TC-09
        real = ufa.sha256_file

        def flaky(path):
            if path.endswith("a.txt"):
                raise PermissionError(13, "Permission denied")
            return real(path)

        ufa.sha256_file = flaky
        try:
            records = ufa.scan_directory(self.root)
        finally:
            ufa.sha256_file = real
        bad = [r for r in records if r["error"]]
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["sha256"], "")
        self.assertEqual(len(records), 4)

    def test_scanned_files_not_modified(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.run_cli()
        after = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
