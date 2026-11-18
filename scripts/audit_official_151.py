#!/usr/bin/env python3
"""Inventory source provenance against the real Flipper 1.5.1 commit.

This is an inventory, not a claim of API, functional, or hardware parity.
Files marked different or absent need individual review; matching source alone
does not prove that the selected firmware compiles or behaves identically.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

OFFICIAL_COMMIT = '9e810dc399e027e48ce07751df72168abbb19065'
ROOTS = ('applications/main', 'applications/services', 'furi', 'lib')
EXTENSIONS = ('.c', '.h', '.fam')
WITHHELD = {'applications/main/nfc/plugins/supported_cards/hotels.c'}

def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True)

def candidates(path):
    found = []
    if path.startswith('applications/services/'):
        service = path.split('/')[2]
        # The board build explicitly selects these application-side services.
        if service in {'desktop', 'desktop_settings', 'storage'}:
            found.append(path)
        found.append('components/' + path.removeprefix('applications/services/'))
    if path.startswith('furi/'):
        found.append('components/' + path)
    if path.startswith('lib/'):
        found.append('components/' + path.removeprefix('lib/'))
    found.append(path)
    return list(dict.fromkeys(found))

def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def audit_sdk(official, port):
    raw = git(official, 'show', f'{OFFICIAL_COMMIT}:targets/f7/api_symbols.csv')
    table = (port / 'components/flipper_application/flipper_application/firmware_api.c').read_text()
    exported = set(re.findall(
        r'\.hash = 0x[0-9a-fA-F]+,\s*\.address = \(uint32_t\).*?/\* (.*?) \*/', table))
    groups = {'Function': set(), 'Variable': set()}
    for row in csv.DictReader(io.StringIO(raw)):
        if row['status'] == '+' and row['entry'] in groups:
            groups[row['entry']].add(row['name'])
    result = {}
    for kind, official_names in groups.items():
        missing = sorted(official_names - exported)
        result[kind.lower()] = {
            'official_names': len(official_names),
            'name_matches': len(official_names) - len(missing),
            'missing_names': missing,
        }
    return result

def audit(official, port):
    actual = git(official, 'rev-parse', '1.5.1^{commit}').strip()
    if actual != OFFICIAL_COMMIT:
        raise ValueError(f'official tag mismatch: {actual}')
    tree = git(official, 'ls-tree', '-r', OFFICIAL_COMMIT, '--', *ROOTS)
    files = []
    for line in tree.splitlines():
        meta, source = line.split('\t', 1)
        _, kind, official_sha = meta.split()
        if kind != 'blob' or not source.endswith(EXTENSIONS):
            continue
        if source in WITHHELD:
            files.append({'official_path': source, 'status': 'withheld'})
            continue
        target = next((name for name in candidates(source) if (port / name).is_file()), None)
        if target is None:
            files.append({'official_path': source, 'status': 'missing'})
            continue
        target_sha = blob_sha((port / target).read_bytes())
        files.append({
            'official_path': source,
            'port_path': target,
            'status': 'identical' if target_sha == official_sha else 'different',
            'official_blob_sha1': official_sha,
            'port_blob_sha1': target_sha,
        })
    return {
        'official_commit': actual,
        'scope': 'C, header, and FAM files under official application, service, core, and library trees',
        'warning': 'Text identity is not proof of runtime, ABI, hardware, or full firmware parity.',
        'counts': dict(sorted(Counter(row['status'] for row in files).items())),
        'sdk': audit_sdk(official, port),
        'files': files,
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('official', type=Path)
    parser.add_argument('port', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = audit(args.official, args.port)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    summary = {k: v for k, v in report.items() if k not in ('files', 'sdk')}
    summary['sdk_name_counts'] = {
        kind: {'official_names': details['official_names'],
               'name_matches': details['name_matches'],
               'missing_names': len(details['missing_names'])}
        for kind, details in report['sdk'].items()
    }
    print(json.dumps(summary, indent=2))
