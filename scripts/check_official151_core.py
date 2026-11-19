#!/usr/bin/env python3
"""Record and verify byte-identical supported core files from Flipper 1.5.1.

The manifest is evidence for individual files only. It does not certify that
the adapted files, hardware interfaces, or application ABI are complete.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

OFFICIAL_COMMIT = '9e810dc399e027e48ce07751df72168abbb19065'
OFFICIAL_TREE = '520fb70571ea6882103542d60a6444215b12ce31'
BASE_COMMIT = 'e6ec11972a8e025d7ab686a6ef3016cf52360834'
GROUPS = {
    'gui': ('applications/services/gui', ('components/gui',)),
    'desktop': ('applications/services/desktop', ('applications/services/desktop',)),
    'storage': ('applications/services/storage', ('applications/services/storage',)),
    'loader': ('applications/services/loader', ('components/loader',)),
    'rpc': ('applications/services/rpc', ('components/rpc',)),
    'dolphin': ('applications/services/dolphin', ('applications/services/dolphin',)),
    'cli': ('applications/services/cli', ('applications/services/cli',)),
    'furi': ('furi/core', ('components/furi/core',)),
    'toolbox': ('lib/toolbox', ('components/toolbox', 'lib/toolbox')),
    'javascript': ('applications/system/js_app', ('applications/system/js_app',)),
    'bit': ('lib/bit_lib', ('components/bit_lib',)),
}
EXCLUDED = ('nfc', 'hotel', 'input_get_key_name', 'input_get_type_name')


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def official_tree(repository, paths):
    command = ['git', '-C', str(repository), 'ls-tree', '-r', OFFICIAL_COMMIT, '--', *paths]
    result = subprocess.check_output(command, text=True)
    entries = {}
    for line in result.splitlines():
        meta, name = line.split('\t', 1)
        mode, kind, oid = meta.split()
        if kind == 'blob' and mode in ('100644', '100755'):
            entries[name] = oid
    return entries


def selected_path(path):
    return path.endswith(('.c', '.h')) and not any(word in path.lower() for word in EXCLUDED)


def create_manifest(source, official):
    assert subprocess.check_output(['git', '-C', str(official), 'rev-parse', '1.5.1^{commit}'], text=True).strip() == OFFICIAL_COMMIT
    records = []
    for group, (prefix, targets) in GROUPS.items():
        for name, oid in sorted(official_tree(official, [prefix]).items()):
            if not selected_path(name):
                continue
            relative = PurePosixPath(name).relative_to(prefix)
            candidates = [PurePosixPath(target) / relative for target in targets]
            if group == 'furi' and str(relative) in ('string.c', 'string.h'):
                candidates.insert(0, PurePosixPath('components/furi/core') / ('furi_' + str(relative)))
            for candidate in candidates:
                path = source / str(candidate)
                if path.is_file() and git_blob(path.read_bytes()) == oid:
                    records.append({'group': group, 'official': name, 'source': str(candidate), 'blob': oid})
                    break
    assert len(records) >= 150, f'too few matching upstream source files: {len(records)}'
    return {'official_commit': OFFICIAL_COMMIT, 'esp_base_commit': BASE_COMMIT, 'files': records}


def verify_manifest(source, manifest, official=None, tree_json=None):
    data = json.loads(manifest.read_text())
    if data.get('official_commit') != OFFICIAL_COMMIT or data.get('esp_base_commit') != BASE_COMMIT:
        raise ValueError('source commit identity does not match')
    records = data['files']
    if len(records) < 150:
        raise ValueError('unexpectedly small official file set')
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != BASE_COMMIT:
        raise ValueError('ESP source is not the pinned base commit')
    source = source.resolve()
    seen = set()
    official_seen = set()
    for row in records:
        group = row['group']
        official_name, target, oid = row['official'], row['source'], row['blob']
        if group not in GROUPS or not selected_path(official_name) or not re.fullmatch(r'[0-9a-f]{40}', oid):
            raise ValueError('invalid source record')
        prefix, targets = GROUPS[group]
        if not official_name.startswith(prefix + '/') or not any(target.startswith(item + '/') for item in targets):
            raise ValueError('source record is outside its selected core group')
        rel = PurePosixPath(target)
        if rel.is_absolute() or '..' in rel.parts or target in seen or official_name in official_seen:
            raise ValueError('unsafe or duplicate source path')
        seen.add(target)
        official_seen.add(official_name)
        local = (source / str(rel)).resolve()
        if not local.is_relative_to(source) or git_blob(local.read_bytes()) != oid:
            raise ValueError(f'1.5.1 source differs: {target}')
    if official is not None:
        entries = official_tree(official, [row['official'] for row in records])
        for row in records:
            if entries.get(row['official']) != row['blob']:
                raise ValueError(f'official tree mismatch: {row["official"]}')
    if tree_json is not None:
        tree = json.loads(tree_json.read_text())
        if tree.get('sha') != OFFICIAL_TREE or tree.get('truncated') is not False:
            raise ValueError('official Git tree response is incomplete or incorrect')
        entries = {row['path']: row['sha'] for row in tree['tree'] if row.get('type') == 'blob'}
        for row in records:
            if entries.get(row['official']) != row['blob']:
                raise ValueError(f'official GitHub tree mismatch: {row["official"]}')
    print(f'Verified {len(records)} byte-identical supported core files against the 1.5.1 manifest.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--manifest', type=Path, default=Path('tests/basic151/official151_core_manifest.json'))
    parser.add_argument('--official-repo', type=Path)
    parser.add_argument('--tree-json', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        if args.official_repo is None:
            parser.error('--write requires --official-repo')
        args.manifest.write_text(json.dumps(create_manifest(args.source, args.official_repo), indent=2) + '\n')
    verify_manifest(args.source, args.manifest, args.official_repo, args.tree_json)


if __name__ == '__main__':
    main()
