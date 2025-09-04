importScripts("js/jszip.min.js");

// ---------- Menu de contexto ----------
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "uid-download-image",
    title: "⬇️ Baixar esta imagem",
    contexts: ["image"]
  });
});

chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId === "uid-download-image" && info.srcUrl) {
    downloadUrl(adjustUrl(info.srcUrl));
  }
});

// ---------- Mensagens do popup ----------
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.type === "UID_DOWNLOAD_ZIP" && Array.isArray(req.urls)) {
    const tabId = sender.tab?.id;

    if (!tabId) {
      chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
        if (!tab) {
          sendResponse({ ok: false, error: "Nenhuma aba ativa encontrada" });
          return;
        }
        criarZip(req.urls, tab.id)
          .then(() => sendResponse({ ok: true, count: req.urls.length }))
          .catch(() => sendResponse({ ok: false }));
      });
      return true;
    }

    criarZip(req.urls, tabId)
      .then(() => sendResponse({ ok: true, count: req.urls.length }))
      .catch(() => sendResponse({ ok: false }));
    return true;
  }

  if (req.type === "UID_DOWNLOAD_MANY" && Array.isArray(req.urls)) {
    req.urls.forEach(u => downloadUrl(adjustUrl(u)));
    sendResponse({ ok: true, count: req.urls.length });
    return true;
  }
});

// ---------- Utilitários ----------
function adjustUrl(url) {
  try {
    // Remove redimensionamento do Instagram (/s150x150/, /s320x320/, etc)
    return url.replace(/\/s\d+x\d+\//, "/");
  } catch (e) {
    return url;
  }
}

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
  });
}

// ---------- Função ZIP ----------
async function criarZip(urls, tabId) {
  try {
    if (!tabId) throw new Error("tabId não fornecido");

    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (urls) => {
        async function blobToBase64(blob) {
          return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
          });
        }

        const out = [];
        for (let i = 0; i < urls.length; i++) {
          try {
            const resp = await fetch(urls[i], { cache: "no-store" });
            if (!resp.ok) throw new Error("HTTP não OK");
            const blob = await resp.blob();
            const base64 = await blobToBase64(blob);
            let name = urls[i].split("/").pop().split("?")[0] || `img${i+1}.jpg`;
            if (!/\.[a-z0-9]{2,5}$/i.test(name)) name += ".jpg";
            out.push({ name, data: base64 });

            chrome.runtime.sendMessage({
              type: "UID_ZIP_PROGRESS",
              url: urls[i],
              index: i + 1,
              total: urls.length
            });
          } catch (e) {
            console.error("Falhou:", urls[i], e);
            chrome.runtime.sendMessage({
              type: "UID_ZIP_PROGRESS",
              url: urls[i],
              index: i + 1,
              total: urls.length,
              failed: true
            });
          }
        }
        return out;
      },
      args: [urls]
    });

    const zip = new JSZip();
    for (const file of result || []) {
      const base64 = file.data.split(",")[1];
      zip.file(file.name, base64, { base64: true });
    }

    const base64zip = await zip.generateAsync({ type: "base64" });
    chrome.downloads.download({
      url: "data:application/zip;base64," + base64zip,
      filename: "imagens.zip",
      saveAs: true
    });

  } catch (err) {
    console.error("Erro no criarZip:", err);
    throw err;
  }
}
