let selecionando = false, startX = 0, startY = 0, overlay, selecaoBox;

chrome.runtime.onMessage.addListener((request) => {
  if (request.action === "INICIAR_SELECAO_LENS") {
    ativarModoLens();
  }
});

function ativarModoLens() {
  if (document.getElementById("lens-overlay")) return;

  overlay = document.createElement("div");
  overlay.id = "lens-overlay";
  selecaoBox = document.createElement("div");
  selecaoBox.id = "lens-selecao";
  overlay.appendChild(selecaoBox);
  document.body.appendChild(overlay);

  overlay.addEventListener("mousedown", (e) => {
    selecionando = true;
    startX = e.clientX; startY = e.clientY;
    selecaoBox.style.left = startX + "px"; selecaoBox.style.top = startY + "px";
    selecaoBox.style.width = "0px"; selecaoBox.style.height = "0px";
    selecaoBox.style.display = "block";
  });

  overlay.addEventListener("mousemove", (e) => {
    if (!selecionando) return;
    const currentX = e.clientX, currentY = e.clientY;
    selecaoBox.style.width = Math.abs(currentX - startX) + "px";
    selecaoBox.style.height = Math.abs(currentY - startY) + "px";
    selecaoBox.style.left = Math.min(currentX, startX) + "px";
    selecaoBox.style.top = Math.min(currentY, startY) + "px";
  });

  overlay.addEventListener("mouseup", async () => {
    if (!selecionando) return;
    selecionando = false;
    const rect = selecaoBox.getBoundingClientRect();
    overlay.remove();
    if (rect.width < 10 || rect.height < 10) return;

    mostrarToast("🔍 Lendo texto da imagem...", "info");

    const dpr = window.devicePixelRatio || 1;

    chrome.runtime.sendMessage({
      action: "PROCESSAR_OCR",
      rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
      dpr: dpr
    }, async (response) => {
      if (response && response.sucesso && response.texto && response.texto.trim()) {
        const textoFinal = response.texto.trim();
        try {
          await navigator.clipboard.writeText(textoFinal);
        } catch(e){}
        mostrarToast("✅ Copiado: \"" + textoFinal + "\"", "sucesso");
      } else {
        mostrarToast("⚠️ Nenhum texto encontrado nessa área.", "erro");
      }
    });
  });
}

function mostrarToast(msg, tipo) {
  const a = document.getElementById("lens-toast"); if (a) a.remove();
  const t = document.createElement("div");
  t.id = "lens-toast"; t.className = tipo; t.innerText = msg;
  document.body.appendChild(t);
  if (tipo !== "info") setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 300); }, 4000);
}
