const BASE = '/firmware/';
const NAME = 'flipper-esp32s3-diy240-20261116-merged.bin';
const $ = (selector) => document.querySelector(selector);

const elements = {
  confirm: $('#hardware-confirm'),
  locked: $('#installer-locked'),
  wrapper: $('#installer-wrap'),
  browser: $('#browser-label'),
  browserDot: $('#browser-dot'),
  firmware: $('#firmware-label'),
  firmwareDot: $('#firmware-dot'),
  version: $('#release-version'),
  size: $('#file-size'),
  download: $('#download-bin'),
  installer: $('#web-installer'),
};

let firmwareReady = false;
let browserSupported = false;
let release = null;

function browserInfo() {
  const ua = navigator.userAgent || '';
  const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const isAndroid = /Android/.test(ua);
  const webSerialNative = Boolean(navigator.serial && typeof navigator.serial.requestPort === 'function');
  return { isIOS, isAndroid, webSerialNative };
}

function updateButton() {
  const agreed = elements.confirm.checked;
  const available = agreed && firmwareReady && browserSupported;
  elements.wrapper.hidden = !available;
  elements.locked.hidden = available;

  if (!agreed) elements.locked.textContent = 'Centang konfirmasi perangkat untuk mengaktifkan flashing.';
  else if (!firmwareReady) elements.locked.textContent = 'Firmware untuk web belum tersedia atau gagal dimuat. Gunakan link GitHub dan coba lagi setelah jaringan tersedia.';
  else if (!browserSupported) elements.locked.textContent = 'Flashing USB tidak tersedia di browser ini. Gunakan Chrome / Edge desktop atau panduan manual.';
}

function updateBrowserStatus() {
  const info = browserInfo();
  const webToolsSupported = elements.installer.hasAttribute('install-supported');
  const webToolsUnsupported = elements.installer.hasAttribute('install-unsupported');
  // Prefer the support attributes from ESP Web Tools: it also supports
  // browsers with a USB polyfill, where navigator.serial may be absent.
  browserSupported = !info.isIOS && window.isSecureContext && !webToolsUnsupported &&
    (info.webSerialNative || webToolsSupported);

  if (info.isIOS) elements.browser.textContent = 'Tidak didukung (iOS)';
  else if (!window.isSecureContext) elements.browser.textContent = 'Perlu HTTPS';
  else if (webToolsUnsupported) elements.browser.textContent = 'Tidak didukung';
  else if (info.webSerialNative) elements.browser.textContent = 'USB tersedia';
  else if (webToolsSupported) elements.browser.textContent = 'USB via installer';
  else elements.browser.textContent = 'Memeriksa dukungan USB';

  elements.browserDot.textContent = browserSupported ? '✓' : '!';
  elements.browserDot.classList.toggle('good', browserSupported);
  elements.browserDot.classList.toggle('bad', !browserSupported);
  updateButton();
}

// The custom element can determine support after its module has loaded.
if (window.customElements && elements.installer) {
  const observer = new MutationObserver(updateBrowserStatus);
  observer.observe(elements.installer, {
    attributes: true,
    attributeFilter: ['install-supported', 'install-unsupported', 'install-not-allowed'],
  });
  customElements.whenDefined('esp-web-install-button').then(updateBrowserStatus).catch(() => {});
}

function prettyBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return 'Tidak diketahui';
  return (bytes / 1024 / 1024).toFixed(1).replace('.', ',') + ' MB';
}

async function checkFirmware() {
  elements.firmware.textContent = 'Memeriksa…';
  elements.version.textContent = 'Memeriksa firmware…';
  try {
    const [manifestResponse, metadataResponse, imageResponse] = await Promise.all([
      fetch(BASE + 'manifest.json', { cache: 'no-store' }),
      fetch(BASE + 'release.json', { cache: 'no-store' }),
      fetch(BASE + NAME, { method: 'HEAD', cache: 'no-store' }),
    ]);
    if (!manifestResponse.ok || !metadataResponse.ok || !imageResponse.ok) throw new Error('Firmware belum lengkap di server.');
    const manifest = await manifestResponse.json();
    const metadata = await metadataResponse.json();
    const build = Array.isArray(manifest.builds) ? manifest.builds.find((item) => item.chipFamily === 'ESP32-S3') : null;
    const part = build?.parts?.[0];
    if (!part || build.parts.length !== 1 || part.offset !== 0 || part.path !== NAME) throw new Error('Manifest tidak sesuai target.');
    if (metadata.filename !== NAME || metadata.chip !== 'ESP32-S3' || !/^[a-f0-9]{64}$/.test(metadata.sha256 || '')) throw new Error('Metadata tidak valid.');
    const length = Number(imageResponse.headers.get('Content-Length'));
    if (length > 0 && metadata.size_bytes !== length) throw new Error('Ukuran firmware tidak cocok.');
    if (!Number.isInteger(metadata.size_bytes) || metadata.size_bytes <= 0 || metadata.size_bytes > 16 * 1024 * 1024) throw new Error('Ukuran image tidak valid.');
    firmwareReady = true;
    release = metadata;
    elements.firmware.textContent = 'Siap diunduh';
    elements.firmwareDot.textContent = '✓';
    elements.firmwareDot.classList.remove('bad');
    elements.firmwareDot.classList.add('good');
    elements.version.textContent = 'BUILD ' + (metadata.version || manifest.version);
    elements.size.textContent = prettyBytes(metadata.size_bytes);
    elements.download.href = BASE + NAME;
    elements.download.setAttribute('download', NAME);
    elements.download.classList.remove('is-disabled');
    elements.download.removeAttribute('aria-disabled');
    elements.download.title = 'SHA256: ' + metadata.sha256;
  } catch (error) {
    firmwareReady = false;
    release = null;
    elements.firmware.textContent = 'Belum tersedia';
    elements.firmwareDot.textContent = '!';
    elements.firmwareDot.classList.add('bad');
    elements.firmwareDot.classList.remove('good');
    elements.version.textContent = 'Firmware web tidak tersedia';
    elements.size.textContent = '—';
    elements.download.href = 'https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43889135916';
    elements.download.removeAttribute('download');
    elements.download.classList.add('is-disabled');
    elements.download.setAttribute('aria-disabled', 'true');
    elements.download.title = 'Gunakan artifact firmware asli dari GitHub sampai file web tersedia.';
    console.info('DIY240 firmware check:', error.message);
  }
  updateButton();
}

const platforms = {
  windows: {
    title: 'Windows 10 / 11',
    summary: 'Pilihan utama: Chrome atau Edge terbaru. Jika browser tidak mendukung USB, gunakan firmware dan esptool melalui PowerShell.',
    link: 'https://github.com/gungsss/flipper-esp32s3-diy240/blob/main/docs/INSTALL_WINDOWS.md',
    steps: [
      'Sambungkan ESP32-S3 ke komputer melalui kabel USB-C data; tutup Arduino IDE atau Serial Monitor.',
      'Centang konfirmasi hardware di flasher, lalu pilih <strong>Hubungkan &amp; Flash</strong>. Berikan izin USB untuk perangkat yang benar.',
      'Setelah selesai, periksa TFT, tombol, microSD dan log boot. Gunakan panduan PowerShell bila flashing web gagal.',
    ],
  },
  macos: {
    title: 'macOS',
    summary: 'Chrome desktop dengan dukungan Web Serial bisa melakukan flashing melalui browser. Alternatifnya, gunakan esptool dan Terminal.',
    link: 'https://github.com/gungsss/flipper-esp32s3-diy240/blob/main/docs/FLASH.md',
    steps: [
      'Gunakan Chrome terbaru dan kabel USB-C yang mendukung data. Temukan port serial jika memakai Terminal.',
      'Flash melalui installer web bila tersedia. Untuk flashing manual, ikuti perintah esptool pada dokumentasi.',
      'Restart perangkat dan verifikasi layar, SD card, tombol, serta koneksi Wi-Fi / BLE.',
    ],
  },
  linux: {
    title: 'Linux',
    summary: 'Browser Chromium dengan Web Serial dapat digunakan langsung. Pastikan izin akses port serial sudah benar.',
    link: 'https://github.com/gungsss/flipper-esp32s3-diy240/blob/main/docs/FLASH.md',
    steps: [
      'Hubungkan ESP32-S3, pastikan port serial terdeteksi dan akunmu punya izin akses perangkat serial.',
      'Pilih port pada installer web. Jika tidak didukung, gunakan script flash_macos_linux.sh pada artifact CI.',
      'Periksa log startup, kualitas kabel daya, dan pembacaan microSD setelah restart.',
    ],
  },
  android: {
    title: 'Android',
    summary: 'Dukungan flashing langsung bergantung pada browser, perangkat, dan USB OTG. Tidak semua kombinasi Android bisa memakai Web Serial.',
    link: 'https://github.com/gungsss/flipper-esp32s3-diy240/blob/main/docs/FLASH.md',
    steps: [
      'Gunakan ponsel Android dengan USB OTG dan kabel data yang sesuai; coba Chrome terbaru.',
      'Jika tombol installer tersedia dan browser mengenali board, berikan izin USB lalu ikuti dialog flashing.',
      'Jika tidak terdeteksi atau tidak didukung, unduh file firmware dan gunakan Windows, Linux, atau macOS untuk flashing.',
    ],
  },
  ios: {
    title: 'iPhone / iPad',
    summary: 'Flashing langsung melalui USB dari browser iPhone/iPad belum didukung oleh situs ini. Dokumentasi dan firmware tetap bisa diakses.',
    link: 'https://github.com/gungsss/flipper-esp32s3-diy240/blob/main/docs/INSTALL_WINDOWS.md',
    steps: [
      'Baca dokumentasi hardware dan siapkan ESP32-S3 N16R8 serta kabel USB data.',
      'Gunakan Windows, Linux, atau macOS untuk flashing. Safari dan browser iOS tidak menyediakan jalur USB Serial yang diperlukan.',
      'Setelah board di-flash lewat komputer, ponsel tetap bisa digunakan untuk membaca panduan dan melaporkan masalah.',
    ],
  },
};

function renderPlatform(key) {
  const data = platforms[key];
  if (!data) return;
  const content = $('#platform-content');
  const selectedTab = document.querySelector('[data-platform="' + key + '"]');
  
const manualCommands = {
  windows: 'py -3 -m esptool --chip esp32s3 --port COM5 --baud 460800 write_flash 0x0 flipper-esp32s3-diy240-20261116-merged.bin',
  macos: 'python -m esptool --chip esp32s3 --port /dev/cu.usbmodemXXXX --baud 460800 write_flash 0x0 flipper-esp32s3-diy240-20261116-merged.bin',
  linux: 'python -m esptool --chip esp32s3 --port /dev/ttyACM0 --baud 460800 write_flash 0x0 flipper-esp32s3-diy240-20261116-merged.bin',
  android: 'Gunakan komputer Windows, Linux, atau macOS untuk flashing manual bila Web Serial tidak tersedia.',
  ios: 'iPhone/iPad tidak mendukung USB flashing lewat browser. Gunakan komputer Windows, Linux, atau macOS.',
};

function updateManualCommand(platform) {
  const label = $('#manual-os-label');
  const code = $('#manual-command');
  if (!label || !code) return;
  label.textContent = ({ windows: 'Windows · PowerShell', macos: 'macOS · Terminal', linux: 'Linux · Terminal', android: 'Android · Alternatif', ios: 'iOS · Alternatif' })[platform];
  code.textContent = manualCommands[platform];
}

const manualCopyButton = $('#manual-copy');
manualCopyButton?.addEventListener('click', async () => {
  const value = $('#manual-command')?.textContent || '';
  try {
    await navigator.clipboard.writeText(value);
    const text = manualCopyButton.textContent;
    manualCopyButton.textContent = 'Tersalin ✓';
    setTimeout(() => { manualCopyButton.textContent = text; }, 1600);
  } catch {
    manualCopyButton.textContent = 'Pilih lalu salin manual';
  }
});

document.querySelectorAll('[data-platform]').forEach((tab) => {
    const selected = tab === selectedTab;
    tab.classList.toggle('selected', selected);
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  content.setAttribute('aria-labelledby', selectedTab.id || 'tab-' + key);
  $('#platform-title').textContent = data.title;
  $('#platform-summary').textContent = data.summary;
  $('#platform-doc-link').href = data.link;
  $('#platform-steps').innerHTML = data.steps.map((step, i) =>
    '<div><span>' + String(i + 1).padStart(2, '0') + '</span><p>' + step + '</p></div>'
  ).join('');
  updateManualCommand(key);
}

document.querySelectorAll('[data-platform]').forEach((tab) => {
  tab.addEventListener('click', () => renderPlatform(tab.dataset.platform));
  tab.addEventListener('keydown', (event) => {
    if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const tabs = [...document.querySelectorAll('[data-platform]')];
    const currentIndex = tabs.indexOf(tab);
    const nextIndex = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 :
      (currentIndex + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    tabs[nextIndex].focus();
    renderPlatform(tabs[nextIndex].dataset.platform);
  });
});

elements.confirm.addEventListener('change', updateButton);
window.addEventListener('pageshow', () => { updateBrowserStatus(); checkFirmware(); });
updateBrowserStatus();
renderPlatform('windows');
checkFirmware();
