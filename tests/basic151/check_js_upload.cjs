#!/usr/bin/env node
// Exercise the actual SDK upload sequence with UTF-8 input and an async drain.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(path.join(process.argv[2],
  'applications/system/js_app/packages/fz-sdk/sdk.js'), 'utf8');
const start = source.indexOf('const appFileBuffer = Buffer.from(appFile, "utf8");');
assert.ok(start >= 0, 'missing UTF-8 encoding');
const endMarker = 'await waitFor(">: ", 1000);';
const end = source.indexOf(endMarker, start);
assert.ok(end >= 0, 'missing final response wait');
const snippet = source.slice(start, end + endMarker.length);
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const uploadChunk = new AsyncFunction('appFile', 'config', 'port', 'waitFor', snippet);

(async () => {
  const events = [];
  const appFile = 'print("Halo 🌴é");';
  const port = {
    write(value) { events.push(Buffer.isBuffer(value) ? Buffer.from(value) : value); },
    drain(callback) {
      events.push('drain-start');
      setTimeout(() => { events.push('drain-done'); callback(); }, 1);
    },
  };
  async function waitFor(text) { events.push('wait:' + text); }
  await uploadChunk(appFile, {output: '/ext/app.js'}, port, waitFor);
  assert.equal(events[0], `storage write_chunk /ext/app.js ${Buffer.byteLength(appFile, 'utf8')}\r`);
  assert.equal(events[1], 'wait:Ready');
  assert.equal(events[2].toString('utf8'), appFile);
  assert.deepEqual(events.slice(3), ['drain-start', 'drain-done', 'wait:>: ']);
  console.log('SDK upload uses UTF-8 byte length and waits for serial drain.');
})().catch(error => { console.error(error); process.exitCode = 1; });
