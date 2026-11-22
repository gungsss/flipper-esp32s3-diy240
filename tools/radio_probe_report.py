#!/usr/bin/env python3
"""Convert M4145 physical radio probe logs into an auditable CSV report.

Usage: python3 tools/radio_probe_report.py serial.log -o radio_report.csv
Accepts ESP-IDF/Flipper log lines and ignores unrelated or malformed records.
No simulated radio measurements are generated.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

PROBE = re.compile(
    r"nRF24 (?P<phase>initial|manual) SPI probe:\s*(?P<state>detected|missing)",
    re.IGNORECASE,
)
CC1101 = re.compile(
    r"CC1101[^\r\n]{0,120}?(?P<state>detected|connected|missing|not detected|disconnected)",
    re.IGNORECASE,
)
TIMESTAMP = re.compile(r"^\s*(?:\[(?P<bracket>\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)\]|(?P<idf>\d{1,12})\s*\))")

def parse(lines):
    for line_number, line in enumerate(lines, 1):
        match = PROBE.search(line)
        if match:
            module, phase, state = "nRF24L01+", match["phase"].lower(), match["state"].lower()
        else:
            match = CC1101.search(line)
            if not match:
                continue
            module, phase = "CC1101", "status"
            state = "detected" if match["state"].lower() in ("detected", "connected") else "missing"
        timestamp = TIMESTAMP.search(line)
        yield {
            "line": line_number,
            "timestamp": (timestamp["bracket"] or timestamp["idf"]) if timestamp else "",
            "module": module,
            "phase": phase,
            "state": state,
            "source": line.rstrip("\r\n"),
        }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Captured serial or firmware log")
    parser.add_argument("-o", "--output", type=Path, required=True, help="CSV report path")
    args = parser.parse_args(argv)
    with args.log.open(encoding="utf-8", errors="replace") as source:
        rows = list(parse(source))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=("line", "timestamp", "module", "phase", "state", "source"))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported {len(rows)} physical probe records to {args.output}", file=sys.stderr)

if __name__ == "__main__":
    main()
