const statusEl = document.getElementById("status");
const gridEl = document.getElementById("grid");

let urls = [];
let selected = new Set();

function setStatus(msg) {
  statusEl.textContent = msg;
  console.log(msg); // Adiciona log para debug
}

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
    fetch(u)
      .then(r => {
        if (!r.ok) throw new Error("Falha ao buscar a imagem");
        return r.blob();
      })
      .then(b => {
        img.src = URL.createObjectURL(b);
      })
      .catch(err => {
        console.error("Erro ao carregar imagem:", u, err);
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
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Verifica se a URL da aba é válida
    if (!tab.url || !tab.url.startsWith('http://') && !tab.url.startsWith('https://')) {
      setStatus("Esta página não pode ser processada (URL inválida).");
      return;
    }

    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
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

    if (!result) {
      setStatus("Nenhuma imagem encontrada ou erro ao processar.");
      return;
    }

    const uniq = Array.from(new Set(result));
    uniq.sort((a, b) => (b.length - a.length));
    urls = uniq;
    selected = new Set(urls);
    setStatus(`imagens Encontradas: ${urls.length}`);
    render();
  } catch (error) {
    console.error("Erro ao coletar imagens:", error);
    setStatus("Erro ao listar imagens. Verifique o console para detalhes.");
  }
}

document.getElementById("listar").addEventListener("click", collectImagesInPage);

document.getElementById("desmarcarTodas").addEventListener("click", () => {
  selected.clear();
  setStatus("Todas Desmarcadas");
  render();
});

document.getElementById("baixarSelecionadas").addEventListener("click", () => {
  const arr = Array.from(selected);
  if (!arr.length) return;
  chrome.runtime.sendMessage({ type: "UID_DOWNLOAD_MANY", urls: arr });
  setStatus(`Baixando ${arr.length} imagem selecionada`);
});

document.getElementById("copiarLinks").addEventListener("click", async () => {
  const arr = Array.from(selected);
  if (!arr.length) return;
  try {
    await navigator.clipboard.writeText(arr.join("\n\n"));
    setStatus(`${arr.length} Link Copiado para a área de Transferência`);
  } catch {
    setStatus("Não foi possível copiar automaticamente.");
  }
});
