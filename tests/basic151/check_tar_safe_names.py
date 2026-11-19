#!/usr/bin/env python3
"""Exercise the archive-entry validation used by real extraction code."""
import subprocess
import sys
import tempfile
from pathlib import Path

text = (Path(sys.argv[1]) / 'components/toolbox/tar/tar_archive.c').read_text()
start = text.index('static bool archive_entry_name_is_safe(')
end = text.index('\nstatic int archive_extract_foreach_cb(', start)
function = text[start:end]
assert 'archive_entry_name_is_safe(header->name)' in text[end:]
assert 'archive_entry_name_is_safe(furi_string_get_cstr(converted_fname))' in text[end:]
test = r'''
#include <assert.h>
#include <stdbool.h>
#include <ctype.h>
#include <string.h>
FUNCTION
int main(void) {
    const char* accepted[] = {"hello.txt", ".bt.keys", "dir/file.txt", "./dir/file", "dir/"};
    const char* rejected[] = {NULL, "", "/absolute", "../file", "dir/../file", "..",
        "dir/.. /file", "dir/..\t/file", "dir/.../file", " dir/file", "dir/file ", "dir\\file", "C:/file"};
    for(size_t i = 0; i < sizeof(accepted)/sizeof(accepted[0]); ++i)
        assert(archive_entry_name_is_safe(accepted[i]));
    for(size_t i = 0; i < sizeof(rejected)/sizeof(rejected[0]); ++i)
        assert(!archive_entry_name_is_safe(rejected[i]));
    return 0;
}
'''.replace('FUNCTION', function)
with tempfile.TemporaryDirectory(prefix='esp-tar-names-') as directory:
    root = Path(directory)
    (root / 'test.c').write_text(test)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(root / 'test.c'),
                    '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True)
print('Archive extraction rejects absolute paths, parent traversal and FAT path aliases.')
