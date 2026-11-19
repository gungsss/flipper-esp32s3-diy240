#!/usr/bin/env python3
"""Check 1.5.1 source and legacy ESP CLI VCP entry points."""
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
source = (root / 'applications/services/cli/cli_vcp.c').read_text()
header = (root / 'applications/services/cli/cli_vcp.h').read_text()
api = (root / 'components/flipper_application/flipper_application/firmware_api.c').read_text()
adapter = (root / 'components/compat/cli_vcp_151.h').read_text()
assert 'void cli_vcp_disable(CliVcp* cli_vcp);' in header
assert '#define cli_vcp_disable cli_vcp_disable_151' in adapter
assert '.address = (uint32_t)cli_vcp_disable_and_get_previous }, /* cli_vcp_disable */' in api
assert '.address = (uint32_t)cli_vcp_disable_151 }, /* cli_vcp_disable_151 */' in api
assert '.address = (uint32_t)cli_vcp_disable_and_get_previous }, /* cli_vcp_disable_and_get_previous */' in api


def function(prefix):
    start = source.index(prefix)
    brace = source.index('{', start)
    depth = 0
    for end in range(brace, len(source)):
        if source[end] == '{':
            depth += 1
        elif source[end] == '}':
            depth -= 1
            if depth == 0:
                return source[start:end + 1]
    raise AssertionError('unclosed function')


test = r'''
#include <assert.h>
#include <stdbool.h>
#define FuriWaitForever 0
#define furi_check(x) assert(x)
typedef struct { int message_queue; } CliVcp;
typedef struct { int type; int api_lock; bool* enabled; } CliVcpMessage;
enum { CliVcpMessageTypeDisable = 1 };
static bool state;
static int requests;
static int api_lock_alloc_locked(void) { return 1; }
static void api_lock_wait_unlock_and_free(int lock) { assert(lock == 1); }
static void furi_message_queue_put(int queue, CliVcpMessage* message, int timeout) {
    (void)queue; (void)timeout; assert(message->type == CliVcpMessageTypeDisable);
    *message->enabled = state; state = false; requests++;
}
FUNCTIONS
int main(void) {
    CliVcp vcp = {0};
    state = true; assert(cli_vcp_disable_and_get_previous(&vcp)); assert(!state);
    assert(!cli_vcp_disable_and_get_previous(&vcp));
    state = true; cli_vcp_disable(&vcp); assert(!state);
    state = true; cli_vcp_disable_151(&vcp); assert(!state);
    assert(requests == 4); return 0;
}
'''
names = ('static void cli_vcp_synchronous_request(',
         'bool cli_vcp_disable_and_get_previous(',
         'void cli_vcp_disable(', 'void cli_vcp_disable_151(')
test = test.replace('FUNCTIONS', '\n'.join(function(n) for n in names))
with tempfile.TemporaryDirectory(prefix='esp-cli-vcp-') as directory:
    path = Path(directory)
    (path / 'test.c').write_text(test)
    subprocess.run(['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                    str(path / 'test.c'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
print('Legacy ESP and 1.5.1-adapted CLI VCP signatures preserve their own behavior.')
