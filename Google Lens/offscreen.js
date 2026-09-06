chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "RECORTAR_E_OCR") {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      const rect = request.rect;
      const dpr = request.dpr || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;

      ctx.drawImage(
        img,
        rect.left * dpr, rect.top * dpr, rect.width * dpr, rect.height * dpr,
        0, 0, rect.width * dpr, rect.height * dpr
      );

      sendResponse({ croppedBase64: canvas.toDataURL("image/png") });
    };
    img.onerror = () => sendResponse({ croppedBase64: null });
    img.src = request.imageUri;
    return true;
  }
});
