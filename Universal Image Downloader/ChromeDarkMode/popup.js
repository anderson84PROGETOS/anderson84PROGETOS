document.getElementById("dark").addEventListener("click", async () => {
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://")) {
    alert("impossivel aplicar o Dark nesta pagina");
    return;
  }
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: aplicarDark
  });
});

document.getElementById("normal").addEventListener("click", async () => {
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://")) {
    alert("Não é possível remover o Dark nesta página.");
    return;
  }
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: removerDark
  });
});

// Funções que serão injetadas
function aplicarDark() {
  if (!document.getElementById("dark-mode-style")) {
    const style = document.createElement("style");
    style.id = "dark-mode-style";
    style.textContent = `
      html {
        filter: invert(100%) hue-rotate(180deg) !important;
        background-color: #121212 !important;
      }
      img, video, iframe {
        filter: invert(100%) hue-rotate(180deg) !important;
      }
    `;
    document.head.appendChild(style);
    alert("Dark aplicado com sucesso!");
  } else {
    alert("Dark já está ativo!");
  }
}

function removerDark() {
  const style = document.getElementById("dark-mode-style");
  if (style) {
    style.remove();
    alert("Dark removido!");
  } else {
    alert("Dark não foi aplicado");
  }
}
