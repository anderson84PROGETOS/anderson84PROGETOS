
// Cria menu de contexto para baixar imagem diretamente
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "uid-download-image",
    title: "Baixar esta imagem",
    contexts: ["image"]
  });
  chrome.contextMenus.create({
    id: "uid-download-link-image",
    title: "Baixar imagem do link",
    contexts: ["link"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "uid-download-image" && info.srcUrl) {
    downloadUrl(info.srcUrl);
  }
  if (info.menuItemId === "uid-download-link-image" && info.linkUrl) {
    // baixa somente se parecer imagem
    const isImg = /\.(png|jpe?g|gif|webp|bmp|svg|avif)(\?|#|$)/i.test(info.linkUrl);
    if (isImg) downloadUrl(info.linkUrl);
  }
});

// Recebe pedidos do popup para baixar N URLs
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.type === "UID_DOWNLOAD_MANY" && Array.isArray(req.urls)) {
    req.urls.forEach(u => downloadUrl(u)); // baixa todas de uma vez
    sendResponse({ok: true, count: req.urls.length});
    return true;
  }
});


function inferFilename(url) {
  try {
    const u = new URL(url);
    const pathname = u.pathname.split("/").filter(Boolean).pop() || "imagem";
    const clean = pathname.split("?")[0].split("#")[0] || "imagem";
    const hasExt = /\.[a-z0-9]{2,5}$/i.test(clean);
    return hasExt ? clean : (clean + ".jpg");
  } catch (e) {
    return "imagem.jpg";
  }
}

function downloadUrl(url) {
  chrome.downloads.download({
    url,
    filename: inferFilename(url),
    saveAs: false
  }, (id) => {
    if (chrome.runtime.lastError) {
      // fallback: tenta via dataURL (quando é blob: ou precisa de referer)
      if (url.startsWith("blob:")) {
        // pede para a aba ativa transformar blob em dataURL
        chrome.tabs.query({active: true, currentWindow: true}, tabs => {
          if (!tabs[0]) return;
          chrome.scripting.executeScript({
            target: {tabId: tabs[0].id},
            func: (blobUrl) => new Promise((resolve) => {
              fetch(blobUrl).then(r => r.blob()).then(b => {
                const fr = new FileReader();
                fr.onload = () => resolve(fr.result);
                fr.readAsDataURL(b);
              }).catch(() => resolve(null));
            }),
            args: [url]
          }, (res) => {
            const dataUrl = res && res[0] && res[0].result;
            if (dataUrl) {
              chrome.downloads.download({
                url: dataUrl,
                filename: inferFilename(url),
                saveAs: false
              });
            }
          });
        });
      }
    }
  });
}
