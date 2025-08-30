document.getElementById("coletar").addEventListener("click", async () => {
  // Pega a aba ativa
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  // Verifica se a URL é válida (não é chrome://)
  if (tab.url.startsWith("http://") || tab.url.startsWith("https://")) {
    // Executa script na aba ativa
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const imagens = document.querySelectorAll("img");
        return Array.from(imagens).map(img => img.src);
      }
    }, (results) => {
      // Verifica se results está definido e contém dados
      if (results && results.length > 0 && results[0].result) {
        const urls = results[0].result;

        // Coloca cada URL com uma linha em branco entre elas
        document.getElementById("resultado").value = urls.join('\n\n');

        // Atualiza contador
        document.getElementById("contador").textContent = `URL Encontradas: ${urls.length}`;
      } else {
        document.getElementById("resultado").value = "Nenhuma URL encontrada ou erro ao processar a página.";
        document.getElementById("contador").textContent = "URL Encontradas: 0";
      }
    });
  } else {
    document.getElementById("resultado").value = "Esta página não suporta a coleta de URLs (ex.: chrome:// URLs).";
    document.getElementById("contador").textContent = "URL Encontradas: 0";
  }
});

document.getElementById("salvar").addEventListener("click", () => {
  const texto = document.getElementById("resultado").value;

  if (!texto) {
    alert("Nenhuma URL encontrada.");
    return;
  }

  const blob = new Blob([texto], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "urls_imagens.txt";
  link.click();
});
