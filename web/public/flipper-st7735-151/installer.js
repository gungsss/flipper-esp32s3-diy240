const COMMIT_151 = '9e810dc399e027e48ce07751df72168abbb19065';
const EXPECTED_FILE = 'esp32s3-st7735-151-merged.bin';
const status = document.getElementById('release-status');
const detail = document.getElementById('release-detail');
const confirmation = document.getElementById('confirm');
const installer = document.getElementById('install');
const download = document.getElementById('download');
const browserNote = document.getElementById('browser-note');
let verified = false;

function setInstallerVisibility() {
  installer.hidden = !(verified && confirmation.checked && window.isSecureContext && 'serial' in navigator);
}
confirmation.addEventListener('change', setInstallerVisibility);

async function getResponse(path) {
  const response = await fetch(path, {cache: 'no-store'});
  if(!response.ok) throw new Error('Firmware belum tersedia');
  return response;
}

async function prepare() {
  const [releaseResponse, manifestResponse] = await Promise.all([
    getResponse('./release.json'), getResponse('./manifest.json'),
  ]);
  const [release, manifest] = await Promise.all([releaseResponse.json(), manifestResponse.json()]);
  const build = manifest.builds?.[0];
  const part = build?.parts?.[0];
  const version = release.reported_flipper_version;
  if(release.source_version !== '1.5.1' || release.source_commit !== COMMIT_151 ||
     (version !== '1.5.1' && !version?.startsWith('1.5.1-')) || manifest.version !== version ||
     release.board !== 'DIY ESP32-S3 N16R8' || !release.lcd?.includes('ST7735S landscape 160x128') ||
     release.filename !== EXPECTED_FILE || manifest.builds?.length !== 1 ||
     build.chipFamily !== 'ESP32-S3' || build.parts?.length !== 1 ||
     part.path !== EXPECTED_FILE || part.offset !== 0 ||
     !/^[0-9a-f]{64}$/.test(release.sha256)) throw new Error('Identitas firmware tidak cocok');
  const binary = await (await getResponse('./' + EXPECTED_FILE)).arrayBuffer();
  if(binary.byteLength !== release.size_bytes || binary.byteLength > 16 * 1024 * 1024) {
    throw new Error('Ukuran firmware tidak cocok');
  }
  const digest = await crypto.subtle.digest('SHA-256', binary);
  const checksum = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
  if(checksum !== release.sha256) throw new Error('Pemeriksaan file firmware gagal');

  verified = true;
  confirmation.disabled = false;
  status.textContent = `Firmware ${version} siap dipasang.`;
  const disabled = Array.isArray(release.disabled_features) ? release.disabled_features.join(', ') : '';
  detail.textContent = `Pengujian perangkat: ${release.hardware_validation || 'belum disebutkan'}.${disabled ? ' Fitur dinonaktifkan: ' + disabled + '.' : ''}`;
  detail.hidden = false;
  download.href = './' + EXPECTED_FILE;
  download.hidden = false;
  browserNote.hidden = window.isSecureContext && 'serial' in navigator;
  setInstallerVisibility();
}

prepare().catch(error => {
  console.error('Firmware belum dapat dipasang:', error);
  status.textContent = 'Firmware 1.5.1 belum tersedia atau belum lolos pemeriksaan. Tombol flash masih dinonaktifkan.';
  confirmation.checked = false;
  confirmation.disabled = true;
  verified = false;
  setInstallerVisibility();
});
