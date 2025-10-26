(() => {
  const STATE = {
    captureIntervalMs: 500, // default 2 fps
    jpegQuality: 0.6,
    isCapturing: false,
    timerId: null
  };

  function readConfigFromStorage() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(
        {
          endpointUrl: "",
          captureIntervalMs: 500,
          jpegQuality: 0.6,
          enabled: true
        },
        (items) => resolve(items)
      );
    });
  }

  function findPrimaryVideo() {
    // TikTok desktop uses multiple videos; we target the visible one
    const videos = Array.from(document.querySelectorAll("video"));
    if (!videos.length) return null;
    const visible = videos
      .map((v) => ({ v, rect: v.getBoundingClientRect() }))
      .filter(({ rect }) => rect.width > 200 && rect.height > 300);
    if (!visible.length) return null;
    // choose the largest in viewport
    visible.sort((a, b) => b.rect.height * b.rect.width - a.rect.height * a.rect.width);
    return visible[0].v;
  }

  function drawFrameToCanvas(video) {
    const width = Math.min(480, video.videoWidth || 480);
    const height = Math.round((width / (video.videoWidth || width)) * (video.videoHeight || width * (16 / 9)));
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    try {
      ctx.drawImage(video, 0, 0, width, height);
    } catch (e) {
      return null;
    }
    return canvas;
  }

  function canvasToBlob(canvas, quality) {
    return new Promise((resolve) => canvas.toBlob((blob) => resolve(blob), "image/jpeg", quality));
  }

  async function captureOnce(cfg) {
    const video = findPrimaryVideo();
    if (!video) return;
    if (video.readyState < 2) return; // HAVE_CURRENT_DATA
    const canvas = drawFrameToCanvas(video);
    if (!canvas) return;
    const blob = await canvasToBlob(canvas, cfg.jpegQuality);
    if (!blob) return;
    const arrayBuffer = await blob.arrayBuffer();
    const bytes = Array.from(new Uint8Array(arrayBuffer));
    chrome.runtime.sendMessage({
      type: "FRAME_CAPTURED",
      data: {
        pageUrl: location.href,
        ts: Date.now(),
        frameBytes: bytes,
        contentType: "image/jpeg"
      }
    });
  }

  async function start() {
    if (STATE.isCapturing) return;
    const cfg = await readConfigFromStorage();
    if (!cfg.enabled) return;
    STATE.isCapturing = true;
    STATE.captureIntervalMs = cfg.captureIntervalMs || 500;
    STATE.jpegQuality = cfg.jpegQuality || 0.6;
    STATE.timerId = setInterval(() => captureOnce(STATE), STATE.captureIntervalMs);
  }

  function stop() {
    STATE.isCapturing = false;
    if (STATE.timerId) {
      clearInterval(STATE.timerId);
      STATE.timerId = null;
    }
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg?.type === "EXTENSION_CONFIG_UPDATED") {
      stop();
      start();
    }
  });

  const observer = new MutationObserver(() => {
    // restart capture if DOM structure changes significantly
    if (STATE.isCapturing) return;
    start();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });

  start();
})();


