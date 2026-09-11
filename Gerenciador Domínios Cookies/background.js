let janelaId = null;

chrome.action.onClicked.addListener(async () => {
  if (janelaId !== null) {
    try {
      await chrome.windows.update(janelaId, { focused: true });
      return;
    } catch (_) {
      janelaId = null;
    }
  }

  const janela = await chrome.windows.create({
    url: chrome.runtime.getURL('index.html'),
    type: 'popup',
    width: 1200,
    height: 800,
    focused: true
  });

  janelaId = janela.id;
});

chrome.windows.onRemoved.addListener((id) => {
  if (id === janelaId) janelaId = null;
});
