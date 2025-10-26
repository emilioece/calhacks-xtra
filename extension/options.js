const DEFAULTS = { 
  endpointUrl: "http://localhost:8000/ingest/frame", 
  captureIntervalMs: 2000,  // 2 seconds (0.5 fps)
  jpegQuality: 0.6, 
  enabled: true 
};

function load() {
  chrome.storage.sync.get(DEFAULTS, (cfg) => {
    document.getElementById('endpointUrl').value = cfg.endpointUrl || '';
    document.getElementById('captureIntervalMs').value = cfg.captureIntervalMs || 2000;
    document.getElementById('jpegQuality').value = cfg.jpegQuality || 0.6;
    document.getElementById('enabled').checked = !!cfg.enabled;
  });
}

function save() {
  const cfg = {
    endpointUrl: document.getElementById('endpointUrl').value.trim(),
    captureIntervalMs: Math.max(100, Number(document.getElementById('captureIntervalMs').value || 2000)),
    jpegQuality: Math.min(1, Math.max(0.1, Number(document.getElementById('jpegQuality').value || 0.6))),
    enabled: document.getElementById('enabled').checked
  };
  chrome.storage.sync.set(cfg, () => {
    document.getElementById('status').textContent = 'Saved';
    setTimeout(() => document.getElementById('status').textContent = '', 1500);
    chrome.tabs.query({ url: '*://www.tiktok.com/*' }, (tabs) => {
      for (const t of tabs) chrome.tabs.sendMessage(t.id, { type: 'EXTENSION_CONFIG_UPDATED' });
    });
  });
}

document.getElementById('save').addEventListener('click', save);
document.addEventListener('DOMContentLoaded', load);
