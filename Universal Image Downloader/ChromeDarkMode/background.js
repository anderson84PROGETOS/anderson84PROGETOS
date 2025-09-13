// Mensagem quando a extensão for instalada
chrome.runtime.onInstalled.addListener(() => {
  console.log("Dark Mode com Botões instalado!");
});

// Ação quando clicar no ícone da extensão
chrome.action.onClicked.addListener((tab) => {
  if (tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://")) {
    // Aviso se não puder aplicar
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        alert("Não deu para aplicar o Dark nesta página.");
      }
    });
  } else {
    // Alterna a exibição dos botões dentro da aba
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    });
  }
});
