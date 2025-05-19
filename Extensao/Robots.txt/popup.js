document.addEventListener('DOMContentLoaded', async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = new URL(tab.url);
    const robotsUrl = `${url.origin}/robots.txt`;

    const response = await fetch(robotsUrl);
    if (!response.ok) {
      return;
    }

    const content = await response.text();
    const display = document.getElementById('robots-content');
    display.textContent = content || 'Nenhum conteúdo encontrado';
  } catch (error) {
    const display = document.getElementById('robots-content');
    display.textContent = '';
  }

  const saveButton = document.getElementById('save-button');
  saveButton.addEventListener('click', saveToFile);
});

function saveToFile() {
  const content = document.getElementById('robots-content').textContent;
  const blob = new Blob([content], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'robots.txt';
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
