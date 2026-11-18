#!/usr/bin/env python3
"""Exercise an ESP emulator pushbutton over its loopback control channel."""
import argparse
import socket
import time

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, required=True)
parser.add_argument('--button', default='button')
parser.add_argument('--ready-ms', type=int, default=4000)
parser.add_argument('--hold-ms', type=int, default=180)
parser.add_argument('--timeout', type=float, default=45)
args = parser.parse_args()
deadline = time.monotonic() + args.timeout
sock = None
while time.monotonic() < deadline:
    try:
        sock = socket.create_connection(('127.0.0.1', args.port), timeout=2)
        break
    except OSError:
        time.sleep(0.2)
if sock is None:
    raise RuntimeError('emulator control socket did not become available')

with sock:
    sock.settimeout(2)
    lines = sock.makefile('rwb', buffering=0)

    def command(text):
        lines.write((text + '\n').encode())
        response = lines.readline().decode().strip()
        if not response.startswith('ok'):
            raise RuntimeError(f'control command {text!r} failed: {response!r}')
        return response

    listing = command('part list')
    if args.button not in listing.split():
        raise RuntimeError(f'button not present in part list: {listing}')
    while time.monotonic() < deadline:
        clock = command('part clock').split()
        if len(clock) != 2:
            raise RuntimeError(f'unexpected emulator clock: {clock}')
        if int(clock[1]) >= args.ready_ms:
            break
        time.sleep(0.1)
    else:
        raise RuntimeError('emulator clock did not reach startup time')
    command(f'part {args.button} input press')
    command(f'part {args.button} input release after {args.hold_ms}')
    print(f'Pressed and released virtual GPIO button after clock {clock[1]} ms.')
