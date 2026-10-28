#!/usr/bin/env python3
"""Create ./sample_usb_drive, a synthetic folder to drag onto the demo website."""

import struct
import zlib
from pathlib import Path

ROOT = Path("sample_usb_drive")


def tiny_png(color):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    row = b"\x00" + bytes(color) * 16
    raw = row * 16
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def tiny_pdf(text):
    stream = f"BT /F1 18 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def build():
    (ROOT / "Documents").mkdir(parents=True, exist_ok=True)
    (ROOT / "Photos").mkdir(exist_ok=True)
    (ROOT / "Backup").mkdir(exist_ok=True)

    report = tiny_pdf("Project report - confidential draft")
    (ROOT / "Documents" / "project_report.pdf").write_bytes(report)
    (ROOT / "Backup" / "project_report_copy.pdf").write_bytes(report)

    (ROOT / "Documents" / "employee_data.csv").write_text(
        "id,name,department\n1,A. Rao,Finance\n2,B. Iyer,Engineering\n3,C. Nair,HR\n")
    (ROOT / "notes.txt").write_text("Remember to hand over the drive on Friday.\n")
    (ROOT / "Photos" / "photo1.png").write_bytes(tiny_png((200, 90, 60)))
    (ROOT / "Photos" / "photo2.png").write_bytes(tiny_png((60, 120, 200)))
    (ROOT / "Photos" / "IMG_0042.png").write_bytes(tiny_png((200, 90, 60)))  # same as photo1
    (ROOT / "Backup" / "archive.bin").write_bytes(bytes(range(256)) * 8)


if __name__ == "__main__":
    build()
    print(f"sample folder ready: {ROOT.resolve()}")
