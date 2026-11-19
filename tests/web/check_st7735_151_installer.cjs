const assert = require('node:assert/strict');
const {readFile} = require('node:fs/promises');
const {webcrypto} = require('node:crypto');
const vm = require('node:vm');
const path = require('node:path');

(async () => {
  const script = await readFile(path.join(__dirname, '../../web/public/flipper-st7735-151/installer.js'), 'utf8');
  const binary = new Uint8Array([0xe9, 0, 0, 0, 9]);
  const digest = Buffer.from(await webcrypto.subtle.digest('SHA-256', binary)).toString('hex');
  const good = {
    source_version: '1.5.1', source_commit: '9e810dc399e027e48ce07751df72168abbb19065',
    reported_flipper_version: '1.5.1-esp', board: 'DIY ESP32-S3 N16R8',
    lcd: 'ST7735S landscape 160x128', filename: 'esp32s3-st7735-151-merged.bin',
    size_bytes: binary.length, sha256: digest, hardware_validation: 'belum diuji',
  };
  const manifest = {version: '1.5.1-esp', builds: [{chipFamily: 'ESP32-S3', parts: [{path: good.filename, offset: 0}]}]};

  async function run(release, available = true, serial = true) {
    const elements = Object.fromEntries(['release-status','release-detail','confirm','install','download','browser-note'].map(id => [id, {
      hidden: true, disabled: true, checked: false, textContent: '', addEventListener(_, callback) {this.onchange = callback;},
    }]));
    const context = {
      document: {getElementById: id => elements[id]},
      window: {isSecureContext: true}, navigator: serial ? {serial: {}} : {},
      crypto: webcrypto, console: {error() {}},
      fetch: async url => ({ok: available,
        json: async () => url.endsWith('release.json') ? release : manifest,
        arrayBuffer: async () => binary.buffer,
      }),
    };
    vm.runInNewContext(script, context);
    await new Promise(resolve => setTimeout(resolve, 30));
    return elements;
  }

  for(const bad of [
    await run(good, false),
    await run({...good, reported_flipper_version: '1.4.3'}),
    await run({...good, sha256: '0'.repeat(64)}),
    await run({...good, board: 'wrong board'}),
  ]) {
    assert.equal(bad.confirm.disabled, true, 'invalid firmware must never enable the installer');
    assert.equal(bad.install.hidden, true);
    assert.match(bad['release-status'].textContent, /belum tersedia/);
  }
  const valid = await run(good);
  assert.equal(valid.confirm.disabled, false);
  assert.equal(valid.install.hidden, true, 'requires explicit confirmation');
  valid.confirm.checked = true;
  valid.confirm.onchange();
  assert.equal(valid.install.hidden, false);
  assert.equal(valid.download.hidden, false);
  const unsupported = await run(good, true, false);
  unsupported.confirm.checked = true;
  unsupported.confirm.onchange();
  assert.equal(unsupported.install.hidden, true, 'requires Web Serial');
  console.log('Installer rejects missing, mismatched and corrupt releases; a valid release needs confirmation and Web Serial.');
})().catch(error => {console.error(error); process.exitCode = 1;});
