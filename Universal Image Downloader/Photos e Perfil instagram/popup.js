document.addEventListener("DOMContentLoaded", () => { 
  const statusEl = document.getElementById("status");
  const gridEl = document.getElementById("grid");

  let urls = [];
  let selected = new Set();

  function setStatus(msg) {
    statusEl.textContent = msg;
    console.log(msg);
  }

  function render() {
    gridEl.innerHTML = "";
    urls.forEach((u) => {
      const card = document.createElement("div");
      card.className = "card";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = selected.has(u);
      cb.dataset.url = u;
      cb.addEventListener("change", () => {
        if (cb.checked) selected.add(u);
        else selected.delete(u);
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

      // Botão Download
      const btnDownload = document.createElement("button");
      btnDownload.textContent = "Download";
      btnDownload.className = "mini-download";
      btnDownload.addEventListener("click", () => {
        chrome.runtime.sendMessage({ type: "UID_DOWNLOAD_MANY", urls: [u] });
        setStatus(`Baixando imagem: ${u}`);
      });

      // Botão Abrir Imagem
      const btnOpen = document.createElement("button");
      btnOpen.textContent = "Abrir";
      btnOpen.className = "mini-open";
      btnOpen.style.marginLeft = "5px"; // pequeno espaço entre os botões
      btnOpen.style.backgroundColor = "#3df50f"; // COR VERDE
      btnOpen.style.color = "black"; // texto legível
      btnOpen.style.border = "1px solid #ccc";
      btnOpen.style.borderRadius = "4px";
      btnOpen.style.padding = "2px 6px";
      btnOpen.addEventListener("click", () => {
        window.open(u, "_blank");
        setStatus(`Abrindo imagem: ${u}`);
      });


      const btnContainer = document.createElement("div");
      btnContainer.appendChild(btnDownload);
      btnContainer.appendChild(btnOpen);

      card.appendChild(cb);
      card.appendChild(img);
      card.appendChild(small);
      card.appendChild(btnContainer);
      gridEl.appendChild(card);
    });
  }

  async function collectImagesInPage() {
    setStatus("Procurando imagens desta página (sem perfil)...");
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.url || (!tab.url.startsWith('http://') && !tab.url.startsWith('https://'))) {
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
            if (img.srcset) img.srcset.split(",").map(s => s.trim().split(" ")[0]).forEach(p => found.add(p));
          });
          Array.from(document.querySelectorAll("*")).forEach(el => {
            const bg = getComputedStyle(el).getPropertyValue("background-image");
            if (bg && bg.startsWith("url(")) {
              const m = bg.match(/url\((['"]?)(.*?)\1\)/);
              if (m && m[2]) found.add(m[2]);
            }
          });
          document.querySelectorAll("picture source").forEach(s => {
            const srcset = s.getAttribute("srcset");
            if (srcset) srcset.split(",").map(p => p.trim().split(" ")[0]).forEach(p => found.add(p));
          });
          const absolutized = Array.from(found).map(u => {
            try { return new URL(u, location.href).href; } catch { return null; }
          }).filter(Boolean);
          const filtradas = Array.from(new Set(absolutized)).map(u => u.replace(/\/s\d+x\d+\//, "/")).filter(u => {
            if (u.includes("s150x150") || u.includes("s320x320")) return false;
            if (/\/vp\//.test(u)) return false;
            if (/profile|avatar|userpic|pfp/i.test(u)) return false;
            return true;
          });
          return filtradas;
        }
      });
      const uniq = Array.from(new Set(result || []));
      uniq.sort((a, b) => b.length - a.length);
      urls = uniq;
      selected = new Set(urls);
      setStatus(`Imagens Encontradas: ${urls.length}`);
      render();
    } catch (error) {
      console.error("Erro ao coletar imagens:", error);
      setStatus("Erro ao listar imagens.");
    }
  }

  async function collectAllImages() {
    setStatus("Procurando TODAS as imagens (incluindo perfil)...");
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.url || (!tab.url.startsWith('http://') && !tab.url.startsWith('https://'))) {
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
            if (img.srcset) img.srcset.split(",").map(s => s.trim().split(" ")[0]).forEach(p => found.add(p));
          });
          Array.from(document.querySelectorAll("*")).forEach(el => {
            const bg = getComputedStyle(el).getPropertyValue("background-image");
            if (bg && bg.startsWith("url(")) {
              const m = bg.match(/url\((['"]?)(.*?)\1\)/);
              if (m && m[2]) found.add(m[2]);
            }
          });
          document.querySelectorAll("picture source").forEach(s => {
            const srcset = s.getAttribute("srcset");
            if (srcset) srcset.split(",").map(p => p.trim().split(" ")[0]).forEach(p => found.add(p));
          });
          const absolutized = Array.from(found).map(u => {
            try { return new URL(u, location.href).href; } catch { return null; }
          }).filter(Boolean);
          return Array.from(new Set(absolutized));
        }
      });
      const uniq = Array.from(new Set(result || []));
      uniq.sort((a, b) => b.length - a.length);
      urls = uniq;
      selected = new Set(urls);
      setStatus(`TODAS as imagens Encontradas: ${urls.length}`);
      render();
    } catch (error) {
      console.error("Erro ao listar todas as imagens:", error);
      setStatus("Erro ao listar todas as imagens.");
    }
  }

  document.getElementById("salvarLinks").addEventListener("click", () => {
    const selecionadas = Array.from(document.querySelectorAll(".card input[type=checkbox]:checked"))
      .map(chk => chk.dataset.url);

    if (selecionadas.length === 0) {
      alert("Nenhuma imagem selecionada.");
      return;
    }

    const content = `Imagens Encontradas: ${selecionadas.length}\n\n${selecionadas.join("\n\n")}`;
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "urls.txt";
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById("listar").addEventListener("click", collectImagesInPage);
  document.getElementById("listarPerfil").addEventListener("click", collectAllImages);

  document.getElementById("desmarcarTodas").addEventListener("click", () => {
    selected.clear();
    setStatus("Todas desmarcadas");
    render();
  });

  document.getElementById("baixarSelecionadas").addEventListener("click", () => {
    const arr = Array.from(selected);
    if (!arr.length) return;
    chrome.runtime.sendMessage({ type: "UID_DOWNLOAD_MANY", urls: arr });
    setStatus(`Baixando ${arr.length} imagens selecionadas`);
  });
});
