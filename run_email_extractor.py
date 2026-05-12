"""Run the email crawler against a user-supplied URL list.

Usage:
    python run_email_extractor.py path\to\urls.txt

The script runs the Scrapy spider and writes the results to:
    emailcrawler/extracted_emails.txt
    emailcrawler/report.txt
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python run_email_extractor.py path/to/urls.txt")
        return 1

    input_file = Path(sys.argv[1]).expanduser().resolve()
    if not input_file.exists():
        print(f"Input file not found: {input_file}")
        return 1

    repo_root = Path(__file__).resolve().parent
    project_root = repo_root / "emailcrawler"

    cmd = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "email_spider",
        "-a",
        f"input_file={input_file}",
    ]

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())