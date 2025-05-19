document.addEventListener('DOMContentLoaded', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      try {
        const urls = new Set();

        document.querySelectorAll('[href], [src]').forEach(el => {
          const link = el.getAttribute('href') || el.getAttribute('src');
          if (link && link.startsWith('http')) {
            urls.add(link);
          }
        });

        document.querySelectorAll('meta[content]').forEach(meta => {
          const content = meta.getAttribute('content');
          if (content && content.startsWith('http')) {
            urls.add(content);
          }
        });

        return Array.from(urls);
      } catch (e) {
        return [`Erro ao executar script: ${e.message}`];
      }
    }
  }, (injectionResults) => {
    const display = document.getElementById('url-list');
    if (chrome.runtime.lastError) {
      display.textContent = 'Erro ao injetar script: ' + chrome.runtime.lastError.message;
    } else {
      const result = injectionResults[0].result;
      if (result.length) {
        display.textContent = `Total de URL Encontradas: ${result.length}

${result.join('\n')}`;
      } else {
        display.textContent = 'Nenhuma URL Encontrada.';
      }
    }
  });

  document.getElementById('save-button').addEventListener('click', () => {
    const content = document.getElementById('url-list').textContent;
    const blob = new Blob([content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'urls.txt';
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });
});