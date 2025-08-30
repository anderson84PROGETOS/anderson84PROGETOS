
const statusEl = document.getElementById("status");
const gridEl = document.getElementById("grid");

let urls = [];
let selected = new Set();

function setStatus(msg) { statusEl.textContent = msg; }

function render() {
  gridEl.innerHTML = "";
  urls.forEach((u, i) => {
    const card = document.createElement("div");
    card.className = "card";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = selected.has(u);
    cb.addEventListener("change", () => {
      if (cb.checked) selected.add(u); else selected.delete(u);
    });
    const img = document.createElement("img");
    img.className = "thumb";
    img.loading = "lazy";
    fetch(u).then(r => r.blob()).then(b => {
      img.src = URL.createObjectURL(b);
    }).catch(() => {
      img.removeAttribute("src");
    });
    const small = document.createElement("div");
    small.className = "url";
    small.textContent = u;

    card.appendChild(cb);
    card.appendChild(img);
    card.appendChild(small);
    gridEl.appendChild(card);
  });
}

async function collectImagesInPage() {
  setStatus("Procurando imagens...");
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  const [{result}] = await chrome.scripting.executeScript({
    target: {tabId: tab.id},
    func: () => {
      const found = new Set();
      document.querySelectorAll("img").forEach(img => {
        const c = img.currentSrc || img.src;
        if (c) found.add(c);
        if (img.srcset) {
          const parts = img.srcset.split(",").map(s => s.trim());
          const last = parts[parts.length - 1]?.split(" ")[0];
          if (last) found.add(last);
        }
      });
      const all = Array.from(document.querySelectorAll("*"));
      for (const el of all) {
        const bg = getComputedStyle(el).getPropertyValue("background-image");
        if (bg && bg.startsWith("url(")) {
          const m = bg.match(/url\((['"]?)(.*?)\1\)/);
          if (m && m[2]) found.add(m[2]);
        }
      }
      document.querySelectorAll("picture source").forEach(s => {
        const srcset = s.getAttribute("srcset");
        if (srcset) {
          const parts = srcset.split(",").map(p => p.trim());
          const last = parts[parts.length - 1]?.split(" ")[0];
          if (last) found.add(last);
        }
      });
      const absolutized = Array.from(found).map(u => {
        try { return new URL(u, location.href).href; } catch { return null; }
      }).filter(Boolean);
      return Array.from(new Set(absolutized));
    }
  });

  const uniq = Array.from(new Set(result));
  uniq.sort((a, b) => (b.length - a.length));
  urls = uniq;
  selected = new Set(urls);
  setStatus(`Encontradas ${urls.length} imagens`);
  render();
}

document.getElementById("listar").addEventListener("click", collectImagesInPage);

document.getElementById("desmarcarTodas").addEventListener("click", () => {
  selected.clear();
  setStatus("Todas Desmarcadas");
  render();
});

document.getElementById("baixarSelecionadas").addEventListener("click", () => {
  const arr = Array.from(selected); // pega apenas as selecionadas
  if (!arr.length) return;
  chrome.runtime.sendMessage({type: "UID_DOWNLOAD_MANY", urls: arr});
  setStatus(`Baixando ${arr.length} imagem(ns) selecionada(s)...`);
});

document.getElementById("copiarLinks").addEventListener("click", async () => {
  const arr = Array.from(selected); // pega apenas as selecionadas
  if (!arr.length) return;
  try {
    await navigator.clipboard.writeText(arr.join("\n\n"));
    setStatus(`${arr.length} Link Copiado para a área de Transferência`);
  } catch {
    setStatus("Não foi possível copiar automaticamente.");
  }
});
