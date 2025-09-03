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
      fetch(u).then(r => r.ok ? r.blob() : Promise.reject())
        .then(b => img.src = URL.createObjectURL(b))
        .catch(() => img.removeAttribute("src"));

      const small = document.createElement("div");
      small.className = "url";
      small.textContent = u;

      const btnDownload = document.createElement("button");
      btnDownload.textContent = "Download";
      btnDownload.className = "mini-download";
      btnDownload.addEventListener("click", () => {
        chrome.runtime.sendMessage({ type: "UID_DOWNLOAD_MANY", urls: [u] });
        setStatus(`Baixando: ${u}`);
      });

      const btnOpen = document.createElement("button");
      btnOpen.textContent = "Abrir";
      btnOpen.className = "mini-open";
      btnOpen.style.marginLeft = "5px";
      btnOpen.style.backgroundColor = "#3df50f";
      btnOpen.style.color = "black";
      btnOpen.style.border = "1px solid #ccc";
      btnOpen.style.borderRadius = "4px";
      btnOpen.style.padding = "2px 6px";
      btnOpen.addEventListener("click", () => {
        window.open(u, "_blank");
        setStatus(`Abrindo: ${u}`);
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
    setStatus("Procurando imagens da página...");
    try {
      const [tab] = await chrome.tabs.query({ active:true, currentWindow:true });
      if (!tab.url.startsWith("http")) { setStatus("URL inválida"); return; }

      const [{ result }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const found = new Set();
          document.querySelectorAll("img").forEach(img => {
            const srcs = [img.currentSrc || img.src];
            if (img.srcset) img.srcset.split(",").map(s => s.trim().split(" ")[0]).forEach(p => srcs.push(p));
            srcs.forEach(s => s && found.add(s));
          });
          document.querySelectorAll("*").forEach(el => {
            const bg = getComputedStyle(el).getPropertyValue("background-image");
            if (bg && bg.startsWith("url(")) {
              const m = bg.match(/url\((['"]?)(.*?)\1\)/);
              if (m && m[2]) found.add(m[2]);
            }
          });
          return Array.from(new Set(found));
        }
      });

      urls = result.sort((a,b)=>b.length-a.length);
      selected = new Set(urls);
      setStatus(`Imagens encontradas: ${urls.length}`);
      render();

    } catch (err) {
      setStatus("Erro ao listar imagens.");
      console.error(err);
    }
  }

  async function collectAllImages() {
    setStatus("Procurando TODAS as imagens (incluindo perfis)...");
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.url.startsWith("http")) { setStatus("URL inválida"); return; }

      const [{ result }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const found = new Set();

          // 1. Todas as imagens <img>
          document.querySelectorAll("img").forEach(img => {
            if (img.currentSrc) found.add(img.currentSrc);
            else if (img.src) found.add(img.src);
            if (img.srcset) img.srcset.split(",").map(s => s.trim().split(" ")[0]).forEach(url => found.add(url));
          });

          // 2. Imagens <picture><source>
          document.querySelectorAll("picture source").forEach(src => {
            const srcset = src.getAttribute("srcset");
            if (srcset) srcset.split(",").map(s => s.trim().split(" ")[0]).forEach(url => found.add(url));
          });

          // 3. Qualquer background-image
          document.querySelectorAll("*").forEach(el => {
            const bg = getComputedStyle(el).getPropertyValue("background-image");
            if (bg && bg.startsWith("url(")) {
              const m = bg.match(/url\((['"]?)(.*?)\1\)/);
              if (m && m[2]) found.add(m[2]);
            }
          });

          // 4. Absolutiza URLs
          const absolutized = Array.from(found).map(u => {
            try { return new URL(u, location.href).href; } catch { return null; }
          }).filter(Boolean);

          // 5. Filtra miniaturas pequenas
          return Array.from(new Set(absolutized))
            .filter(u => !/s150x150|s320x320|\/vp\//i.test(u));
        }
      });

      urls = result.sort((a,b)=>b.length-a.length);
      selected = new Set(urls);
      setStatus(`TODAS as imagens encontradas: ${urls.length}`);
      render();

    } catch (err) {
      setStatus("Erro ao listar todas as imagens.");
      console.error(err);
    }
  }

  // Botões
  document.getElementById("listar").addEventListener("click", collectImagesInPage);
  document.getElementById("listarPerfil").addEventListener("click", collectAllImages);

  document.getElementById("baixarSelecionadas").addEventListener("click", () => {
    const arr = Array.from(selected);
    if (!arr.length) { alert("Nenhuma imagem selecionada"); return; }

    setStatus(`Iniciando ZIP com ${arr.length} imagens...`);
    chrome.runtime.sendMessage({ type: "UID_DOWNLOAD_ZIP", urls: arr }, (res) => {
      if (res && res.ok) {
        setStatus(`ZIP iniciado com ${res.count} imagens.`);
      } else {
        setStatus("Falha ao criar ZIP.");
      }
    });
  });

  chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === "UID_ZIP_PROGRESS") {
    const statusHtml = msg.failed
      ? `<span style="color:red;font-weight:bold;">Falhou: ${msg.index}/${msg.total}</span><br><span style="font-size:1.00em;">${msg.url}</span>`
      : `<span>Adicionando: ${msg.index}/${msg.total}</span><br><span style="font-size:1.00em;color:#555;">${msg.url}</span>`;

    statusEl.innerHTML = statusHtml;
  }
});


  document.getElementById("salvarLinks").addEventListener("click", () => {
    const selecionadas = Array.from(document.querySelectorAll(".card input[type=checkbox]:checked"))
      .map(chk => chk.dataset.url);

    if (!selecionadas.length) { alert("Nenhuma imagem selecionada."); return; }

    const content = `Imagens Encontradas: ${selecionadas.length}\n\n${selecionadas.join("\n\n")}`;
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "urls.txt";
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById("desmarcarTodas").addEventListener("click", () => {
    selected.clear();
    setStatus("Todas desmarcadas");
    render();
  });
});
