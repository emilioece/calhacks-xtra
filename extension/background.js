const DEFAULT_CONFIG = {
  endpointUrl: "http://localhost:8000/ingest/frame",
  enabled: true,
  captureIntervalMs: 2000,  // 2 seconds (0.5 fps) - better for short video detection
  jpegQuality: 0.6
};

function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(DEFAULT_CONFIG, (cfg) => resolve({ ...DEFAULT_CONFIG, ...cfg }));
  });
}

async function postFrame(endpointUrl, payload) {
  if (!endpointUrl) return;
  try {
    await fetch(endpointUrl, {
      method: "POST",
      headers: {
        "content-type": "application/json"
      },
      body: JSON.stringify(payload),
      // avoid CORS preflight by staying simple; server should allow CORS
      mode: "cors",
      credentials: "omit"
    });
  } catch (e) {
    // swallow errors in MVP; could add retry/backoff
  }
}

chrome.runtime.onMessage.addListener(async (msg, _sender, _sendResponse) => {
  if (msg?.type === "FRAME_CAPTURED") {
    const cfg = await getConfig();
    if (!cfg.enabled) return;
    const { pageUrl, ts, frameBytes, contentType } = msg.data || {};
    const payload = {
      pageUrl,
      ts,
      contentType,
      frameB64: btoa(String.fromCharCode(...frameBytes))
    };
    await postFrame(cfg.endpointUrl, payload);
  }
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.get(DEFAULT_CONFIG, (cfg) => {
    chrome.storage.sync.set({ ...DEFAULT_CONFIG, ...cfg });
  });
});


