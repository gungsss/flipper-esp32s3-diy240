const BASE = '/flipper-st7735-151/landscape/';
const EXPECTED_IMAGES = [
  { file: 'bootloader/bootloader.bin', offset: 0 },
  { file: 'partition_table/partition-table.bin', offset: 0x8000 },
  { file: 'furi_esp32.bin', offset: 0x10000 },
  { file: 'ota_data_initial.bin', offset: 0xbf0000 },
];
const EXPECTED_MODULES = ['CC1101 Sub-GHz', 'nRF24L01+'];
const EXPECTED_PINOUT_SHA256 = 'b154574a0d1acc7b915306f563a6cc8f0b4ca1e5fa492a5a584914182bd46c12';
const $ = (selector) => document.querySelector(selector);
const elements = {
  confirm: $('#hardware-confirm'), locked: $('#installer-locked'), wrapper: $('#installer-wrap'),
  browser: $('#browser-label'), browserDot: $('#browser-dot'), firmware: $('#firmware-label'),
  firmwareDot: $('#firmware-dot'), version: $('#release-version'),
  installer: $('#web-installer'),
};
let firmwareReady = false;
let browserSupported = false;
let buildInfo = null;

function browserInfo() {
  const ua = navigator.userAgent || '';
  const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const webSerialNative = Boolean(navigator.serial && typeof navigator.serial.requestPort === 'function');
  return { isIOS, webSerialNative };
}

function updateButton() {
  const agreed = elements.confirm.checked;
  const available = agreed && firmwareReady && browserSupported;
  elements.wrapper.hidden = !available;
  elements.locked.hidden = available;
  if (!agreed) elements.locked.textContent = 'Centang konfirmasi hardware untuk membuka installer.';
  else if (!firmwareReady) elements.locked.textContent = 'File firmware belum lengkap atau tidak cocok dengan metadata. Unduh paket build dan coba lagi.';
  else if (!browserSupported) elements.locked.textContent = 'Flash USB tidak didukung browser ini. Gunakan Chrome atau Edge desktop, atau flash manual dari paket build.';
}

function setStatus(dot, label, ok, text) {
  dot.textContent = ok ? '✓' : '!';
  dot.classList.toggle('good', ok);
  dot.classList.toggle('bad', !ok);
  label.textContent = text;
}

function updateBrowserStatus() {
  const info = browserInfo();
  const supported = elements.installer.hasAttribute('install-supported');
  const unsupported = elements.installer.hasAttribute('install-unsupported');
  browserSupported = !info.isIOS && window.isSecureContext && !unsupported && (info.webSerialNative || supported);
  if (info.isIOS) setStatus(elements.browserDot, elements.browser, false, 'iOS belum didukung');
  else if (!window.isSecureContext) setStatus(elements.browserDot, elements.browser, false, 'Perlu HTTPS');
  else if (unsupported) setStatus(elements.browserDot, elements.browser, false, 'Browser tidak didukung');
  else if (info.webSerialNative || supported) setStatus(elements.browserDot, elements.browser, true, 'USB tersedia');
  else setStatus(elements.browserDot, elements.browser, false, 'Memeriksa USB');
  updateButton();
}

if (window.customElements && elements.installer) {
  const observer = new MutationObserver(updateBrowserStatus);
  observer.observe(elements.installer, { attributes: true, attributeFilter: ['install-supported', 'install-unsupported', 'install-not-allowed'] });
  customElements.whenDefined('esp-web-install-button').then(updateBrowserStatus).catch(() => {});
}

function prettyBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return 'Tidak diketahui';
  return (bytes / 1024 / 1024).toFixed(2).replace('.', ',') + ' MB';
}

async function readJson(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) throw new Error('HTTP ' + response.status + ' saat membaca ' + url);
  return response.json();
}

function validateParts(manifest, info) {
  if (info.project_name !== 'M4145 Flipper ESP32-S3' || info.firmware_author !== 'm4145') throw new Error('Identitas build tidak sesuai.');
  if (info.build_profile !== 'm4145-unified' || info.board !== 'DIY ESP32-S3 N16R8') throw new Error('Profil board bukan firmware ST7735S untuk wiring saat ini.');
  if (!String(info.lcd || '').includes('ST7735S landscape 160x128')) throw new Error('Build bukan ST7735S landscape 160×128.');
  if (info.pinout_sha256 !== EXPECTED_PINOUT_SHA256) throw new Error('Pinout firmware bukan wiring radio yang sudah ditetapkan.');
  if (!Array.isArray(info.enabled_optional_modules) || EXPECTED_MODULES.length !== info.enabled_optional_modules.length || EXPECTED_MODULES.some((name) => !info.enabled_optional_modules.includes(name))) throw new Error('Daftar modul tidak cocok dengan profil uji radio saat ini.');
  if (!Array.isArray(manifest.builds) || manifest.builds.length !== 1 || manifest.builds[0].chipFamily !== 'ESP32-S3') throw new Error('Manifest bukan satu build ESP32-S3.');
  const parts = manifest.builds[0].parts;
  if (parts.length !== EXPECTED_IMAGES.length || info.images.length !== EXPECTED_IMAGES.length) throw new Error('Jumlah partisi tidak cocok.');
  for (let i = 0; i < EXPECTED_IMAGES.length; i++) {
    const expected = EXPECTED_IMAGES[i];
    const part = parts.find((item) => item.path === expected.file);
    const image = info.images.find((item) => item.file === expected.file);
    if (!part || !image || part.offset !== expected.offset || Number(image.offset) !== expected.offset) throw new Error('Offset tidak cocok untuk ' + expected.file);
    if (!/^[a-f0-9]{64}$/.test(image.sha256 || '') || !Number.isInteger(image.size_bytes) || image.size_bytes <= 0) throw new Error('Metadata file tidak valid: ' + expected.file);
  }
}

function renderPackageFiles(info) {
  const container = $('#package-files');
  const fragment = document.createDocumentFragment();
  for (const expected of EXPECTED_IMAGES) {
    const data = info.images.find((item) => item.file === expected.file);
    const row = document.createElement('div');
    row.className = 'package-file';
    const name = document.createElement('code');
    name.textContent = expected.file;
    const offset = document.createElement('span');
    offset.textContent = 'Offset ' + '0x' + expected.offset.toString(16);
    const size = document.createElement('small');
    size.textContent = prettyBytes(data.size_bytes);
    const link = document.createElement('a');
    link.href = BASE + expected.file;
    link.download = expected.file.split('/').pop();
    link.textContent = 'Unduh';
    link.setAttribute('aria-label', 'Unduh ' + expected.file);
    row.append(name, offset, size, link);
    fragment.append(row);
  }
  container.replaceChildren(fragment);
}

function setBuildInfo(info) {
  buildInfo = info;
  elements.version.textContent = info.reported_flipper_version;
  $('#panel-board').textContent = info.board.replace('DIY ', '');
  $('#panel-display').textContent = 'ST7735S · 160×128';
  $('#panel-build-profile').textContent = 'Uji radio';
  const appImage = info.images.find((item) => item.file === 'furi_esp32.bin');
  $('#panel-file-size').textContent = prettyBytes(appImage.size_bytes);
  $('#panel-sha').textContent = appImage.sha256.slice(0, 16) + '…';
  $('#panel-sha').title = appImage.sha256;
  renderPackageFiles(info);
}

async function checkFirmware() {
  elements.firmware.textContent = 'Memeriksa…';
  elements.version.textContent = 'Memeriksa firmware…';
  try {
    const [manifest, info] = await Promise.all([
      readJson(BASE + 'manifest.json'),
      readJson(BASE + 'BUILD_INFO.json'),
    ]);
    validateParts(manifest, info);
    const heads = await Promise.all(EXPECTED_IMAGES.map(async (item) => {
      const image = info.images.find((record) => record.file === item.file);
      const response = await fetch(BASE + item.file, { method: 'HEAD', cache: 'no-store' });
      if (!response.ok) throw new Error('File tidak tersedia: ' + item.file);
      const length = Number(response.headers.get('Content-Length'));
      if (length > 0 && length !== image.size_bytes) throw new Error('Ukuran file tidak cocok: ' + item.file);
      return true;
    }));
    if (!heads.every(Boolean)) throw new Error('Pemeriksaan file firmware gagal.');
    firmwareReady = true;
    setStatus(elements.firmwareDot, elements.firmware, true, 'Siap · 4 file cocok');
    setBuildInfo(info);
  } catch (error) {
    firmwareReady = false;
    buildInfo = null;
    elements.version.textContent = 'Firmware belum siap';
    setStatus(elements.firmwareDot, elements.firmware, false, 'Perlu diperiksa');
    $('#package-files').textContent = 'Daftar firmware belum dapat diperiksa. Buka workflow build pada GitHub.';
    console.warn('Firmware status check:', error.message);
  }
  updateButton();
}

function formatDate(value) {
  const date = new Date(value + 'T00:00:00');
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }).format(date);
}

function renderReleaseHistory(data) {
  const container = $('#updates-list');
  const releases = Array.isArray(data.releases) ? data.releases : [];
  const fragment = document.createDocumentFragment();
  if (!releases.length) throw new Error('Riwayat rilis belum tersedia.');
  for (let i = 0; i < releases.length; i++) {
    const release = releases[i];
    const article = document.createElement('article');
    article.className = 'panel release-card';
    const top = document.createElement('div');
    top.className = 'release-topline';
    const date = document.createElement('time');
    date.dateTime = release.date;
    date.textContent = formatDate(release.date);
    const badge = document.createElement('span');
    badge.className = 'release-badge' + (i === 0 ? ' current' : '');
    badge.textContent = i === 0 ? 'VERSI TERBARU' : 'RIWAYAT';
    top.append(date, badge);
    const title = document.createElement('h3');
    title.textContent = release.title;
    const version = document.createElement('p');
    version.className = 'release-version';
    version.textContent = release.version;
    const list = document.createElement('ul');
    for (const change of (Array.isArray(release.changes) ? release.changes : [])) {
      const item = document.createElement('li');
      item.textContent = change;
      list.append(item);
    }
    const footer = document.createElement('div');
    footer.className = 'release-footer';
    const scope = document.createElement('p');
    scope.textContent = release.scope || 'Build komunitas untuk ESP32-S3.';
    footer.append(scope);
    if (release.build_url) {
      const link = document.createElement('a');
      link.href = release.build_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'Build & paket ↗';
      footer.append(link);
    }
    article.append(top, title, version, list, footer);
    fragment.append(article);
  }
  container.replaceChildren(fragment);
  $('#update-current-label').textContent = releases.length + (releases.length === 1 ? ' rilis' : ' rilis') + ' tercatat';
}

async function loadReleaseHistory() {
  try {
    const data = await readJson('/updates.json');
    renderReleaseHistory(data);
  } catch (error) {
    $('#updates-list').textContent = 'Riwayat update belum dapat dimuat.';
    $('#updates-status').textContent = error.message;
  }
}

const platforms = {
  windows: {
    title: 'Windows 10 / 11',
    summary: 'Pilihan utama: Chrome atau Edge terbaru, kabel USB-C data, dan izin port USB dari browser. Esptool tersedia untuk flashing manual.',
    link: '/flipper-st7735-151/landscape/INSTALL_WINDOWS.md',
    command: 'py -3 -m esptool --chip esp32s3 --port COM5 --baud 460800 --before default_reset --after hard_reset write_flash 0x0 bootloader/bootloader.bin 0x8000 partition_table/partition-table.bin 0x10000 furi_esp32.bin 0xbf0000 ota_data_initial.bin',
    steps: ['Gunakan kabel USB data dan tutup Serial Monitor atau aplikasi lain yang memakai port.', 'Centang konfirmasi hardware, pilih Hubungkan & Flash, lalu pilih port ESP32-S3.', 'Tunggu sampai selesai. Jika memakai metode manual, unduh paket build agar folder partisi tetap lengkap.'],
  },
  macos: {
    title: 'macOS',
    summary: 'Chrome desktop mendukung USB Serial pada kombinasi yang kompatibel. Alternatifnya gunakan esptool di Terminal.',
    link: '/flipper-st7735-151/landscape/FLASH.md',
    command: 'python3 -m esptool --chip esp32s3 --port /dev/cu.usbmodemXXXX --baud 460800 --before default_reset --after hard_reset write_flash 0x0 bootloader/bootloader.bin 0x8000 partition_table/partition-table.bin 0x10000 furi_esp32.bin 0xbf0000 ota_data_initial.bin',
    steps: ['Pastikan Chrome terbaru dan kabel USB-C mendukung transfer data.', 'Buka installer web dan pilih port ESP32-S3 saat diminta.', 'Untuk Terminal, gunakan keempat file dari paket build yang sama dan ganti port serial sesuai perangkat.'],
  },
  linux: {
    title: 'Linux',
    summary: 'Gunakan Chrome atau Chromium yang mendukung USB Serial. Pastikan akun memiliki akses ke perangkat serial.',
    link: '/flipper-st7735-151/landscape/FLASH.md',
    command: 'python3 -m esptool --chip esp32s3 --port /dev/ttyACM0 --baud 460800 --before default_reset --after hard_reset write_flash 0x0 bootloader/bootloader.bin 0x8000 partition_table/partition-table.bin 0x10000 furi_esp32.bin 0xbf0000 ota_data_initial.bin',
    steps: ['Hubungkan board dan pastikan perangkat serial muncul.', 'Flash dari installer web bila browser mengenali port.', 'Jika memakai esptool, ganti /dev/ttyACM0 sesuai nama port board.'],
  },
  android: {
    title: 'Android',
    summary: 'Flash langsung hanya bisa jika ponsel mendukung USB OTG dan browser menyediakan dukungan serial/USB yang diperlukan.',
    link: '/flipper-st7735-151/landscape/FLASH.md',
    command: 'Jika installer USB tidak tersedia, gunakan komputer Windows, macOS, atau Linux untuk flash manual.',
    steps: ['Siapkan adapter OTG dan kabel data yang sesuai.', 'Buka halaman ini di browser yang mendukung USB Serial; dukungan berbeda antarperangkat.', 'Jika board tidak terdeteksi, pakai komputer desktop dan panduan manual.'],
  },
  ios: {
    title: 'iPhone / iPad',
    summary: 'iOS tidak mendukung jalur USB Serial yang diperlukan installer. Firmware dan dokumentasi tetap bisa dibuka dari ponsel.',
    link: '/flipper-st7735-151/landscape/FLASH.md',
    command: 'iPhone/iPad tidak dapat melakukan flash USB dari browser. Gunakan komputer Windows, macOS, atau Linux.',
    steps: ['Buka dokumentasi hardware di halaman ini.', 'Flash dari komputer dengan browser Chromium atau esptool.', 'Setelah board menyala, ponsel tetap dapat dipakai untuk melihat panduan dan riwayat versi.'],
  },
};

function updateManualCommand(platform) {
  const data = platforms[platform];
  $('#manual-os-label').textContent = ({ windows: 'Windows · PowerShell', macos: 'macOS · Terminal', linux: 'Linux · Terminal', android: 'Android · Alternatif', ios: 'iOS · Alternatif' })[platform];
  $('#manual-command').textContent = data.command;
}

function renderPlatform(key) {
  const data = platforms[key];
  if (!data) return;
  const tabs = [...document.querySelectorAll('[data-platform]')];
  const selectedTab = tabs.find((tab) => tab.dataset.platform === key);
  for (const tab of tabs) {
    const selected = tab === selectedTab;
    tab.classList.toggle('selected', selected);
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  }
  $('#platform-content').setAttribute('aria-labelledby', selectedTab.id);
  $('#platform-title').textContent = data.title;
  $('#platform-summary').textContent = data.summary;
  $('#platform-doc-link').href = data.link;
  const steps = $('#platform-steps');
  steps.replaceChildren(...data.steps.map((text, index) => {
    const row = document.createElement('div');
    const number = document.createElement('span');
    number.textContent = String(index + 1).padStart(2, '0');
    const copy = document.createElement('p');
    copy.textContent = text;
    row.append(number, copy);
    return row;
  }));
  updateManualCommand(key);
}

document.querySelectorAll('[data-platform]').forEach((tab) => {
  tab.addEventListener('click', () => renderPlatform(tab.dataset.platform));
  tab.addEventListener('keydown', (event) => {
    if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const tabs = [...document.querySelectorAll('[data-platform]')];
    const current = tabs.indexOf(tab);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (current + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    tabs[next].focus();
    renderPlatform(tabs[next].dataset.platform);
  });
});

$('#manual-copy').addEventListener('click', async (event) => {
  const button = event.currentTarget;
  try {
    await navigator.clipboard.writeText($('#manual-command').textContent || '');
    button.textContent = 'Tersalin ✓';
    setTimeout(() => { button.textContent = 'Salin perintah'; }, 1600);
  } catch {
    button.textContent = 'Pilih lalu salin manual';
  }
});

elements.confirm.addEventListener('change', updateButton);
window.addEventListener('pageshow', () => { updateBrowserStatus(); checkFirmware(); loadReleaseHistory(); });
updateBrowserStatus();
renderPlatform('windows');
checkFirmware();
loadReleaseHistory();
