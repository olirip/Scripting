#!/usr/bin/env python3
"""Convert a PDF file to Markdown and save it in the same directory as this script."""

import sys
from pathlib import Path
import pymupdf4llm

def convert(pdf_path: str) -> None:
    src = Path(pdf_path).expanduser().resolve()
    if not src.exists():
        print(f"Error: file not found: {src}", file=sys.stderr)
        sys.exit(1)
    if src.suffix.lower() != ".pdf":
        print(f"Error: expected a .pdf file, got: {src.suffix}", file=sys.stderr)
        sys.exit(1)

    md_text = pymupdf4llm.to_markdown(str(src))

    # Strip image placeholder lines added by pymupdf4llm for omitted pictures
    import re
    md_text = re.sub(r"\*\*==> picture \[.*?\] intentionally omitted <==\*\*\n*", "", md_text)

    out_dir = Path(__file__).parent
    out_file = out_dir / (src.stem + ".md")
    out_file.write_text(md_text, encoding="utf-8")
    print(f"Saved: {out_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {Path(__file__).name} <path/to/file.pdf>", file=sys.stderr)
        sys.exit(1)
    convert(sys.argv[1])
