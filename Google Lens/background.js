// ============================================================
// BACKGROUND.JS
// Extensão: Copiar Texto (Google Lens)
// Manifest V3
// ============================================================

// ============================================================
// INSTALAÇÃO DA EXTENSÃO
// ============================================================

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "copiar-texto-lens",
    title: "📷 Copiar Texto (Google Lens)",
    contexts: ["all"]
  });
});


// ============================================================
// MENU DE CONTEXTO
// ============================================================

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "copiar-texto-lens") {
    return;
  }

  // Verifica se existe uma aba válida
  if (!tab || !tab.id) {
    console.error("Aba inválida.");
    return;
  }

  try {
    await chrome.tabs.sendMessage(tab.id, {
      action: "INICIAR_SELECAO_LENS"
    });
  } catch (erro) {
    console.warn(
      "Não foi possível enviar mensagem para a página. " +
      "Talvez seja necessário recarregar a página.",
      erro
    );

    // NÃO usar alert() aqui.
    // Service Worker do Manifest V3 não possui alert().
    //
    // Tentamos mostrar o aviso através do content script.
    try {
      await chrome.tabs.sendMessage(tab.id, {
        action: "MOSTRAR_AVISO",
        mensagem: "Por favor, recarregue a página (F5) para ativar a extensão."
      });
    } catch (erroAviso) {
      console.warn(
        "Content script não está disponível nesta página.",
        erroAviso
      );
    }
  }
});


// ============================================================
// CRIAR DOCUMENTO OFFSCREEN
// ============================================================

async function criarOffscreen() {
  try {
    // Se já existe, não cria novamente
    if (await chrome.offscreen.hasDocument()) {
      return;
    }

    await chrome.offscreen.createDocument({
      url: "offscreen.html",
      reasons: ["USER_MEDIA"],
      justification: "Recortar a imagem capturada da tela para processamento OCR."
    });

    console.log("Documento offscreen criado.");
  } catch (erro) {
    console.error("Erro ao criar documento offscreen:", erro);
    throw erro;
  }
}


// ============================================================
// PROCESSAMENTO DE OCR
// ============================================================

chrome.runtime.onMessage.addListener(
  (request, sender, sendResponse) => {

    // --------------------------------------------------------
    // AÇÃO: PROCESSAR OCR
    // --------------------------------------------------------

    if (request.action !== "PROCESSAR_OCR") {
      return false;
    }

    (async () => {
      try {

        // ====================================================
        // 1. VERIFICAR ABA
        // ====================================================

        const tabId = sender.tab?.id;

        if (!tabId) {
          throw new Error("Não foi possível identificar a aba.");
        }


        // ====================================================
        // 2. CAPTURAR A TELA VISÍVEL
        // ====================================================

        console.log("Capturando tela...");

        const imageUri = await chrome.tabs.captureVisibleTab(
          null,
          {
            format: "png"
          }
        );

        if (!imageUri) {
          throw new Error("Não foi possível capturar a tela.");
        }


        // ====================================================
        // 3. CRIAR OFFSCREEN
        // ====================================================

        await criarOffscreen();


        // ====================================================
        // 4. ENVIAR IMAGEM PARA O OFFSCREEN
        // ====================================================

        console.log("Enviando imagem para processamento...");

        const resultadoRecorte = await chrome.runtime.sendMessage({
          action: "RECORTAR_E_OCR",
          imageUri: imageUri,
          rect: request.rect,
          dpr: request.dpr
        });


        // ====================================================
        // 5. VERIFICAR RESULTADO DO RECORTE
        // ====================================================

        if (
          !resultadoRecorte ||
          !resultadoRecorte.croppedBase64
        ) {
          sendResponse({
            sucesso: false,
            erro: "Falha ao recortar a imagem."
          });

          return;
        }


        // ====================================================
        // 6. PREPARAR OCR.SPACE
        // ====================================================

        console.log("Enviando imagem para OCR...");

        const formData = new FormData();

        formData.append(
          "base64Image",
          resultadoRecorte.croppedBase64
        );

        formData.append(
          "language",
          "por"
        );

        formData.append(
          "isOverlayRequired",
          "false"
        );

        formData.append(
          "OCREngine",
          "2"
        );


        // ====================================================
        // 7. ENVIAR PARA OCR.SPACE
        // ====================================================

        const apiRes = await fetch(
          "https://api.ocr.space/parse/image",
          {
            method: "POST",

            headers: {
              "apikey": "helloworld"
            },

            body: formData
          }
        );


        // ====================================================
        // 8. VERIFICAR RESPOSTA HTTP
        // ====================================================

        if (!apiRes.ok) {
          throw new Error(
            `Erro HTTP da API OCR: ${apiRes.status}`
          );
        }


        // ====================================================
        // 9. CONVERTER RESPOSTA PARA JSON
        // ====================================================

        const data = await apiRes.json();


        // ====================================================
        // 10. VERIFICAR ERRO DA API
        // ====================================================

        if (data.IsErroredOnProcessing) {

          let mensagemErro = "Erro ao processar OCR.";

          if (
            Array.isArray(data.ErrorMessage) &&
            data.ErrorMessage.length > 0
          ) {
            mensagemErro = data.ErrorMessage.join(" ");
          } else if (data.ErrorMessage) {
            mensagemErro = String(data.ErrorMessage);
          }

          sendResponse({
            sucesso: false,
            erro: mensagemErro
          });

          return;
        }


        // ====================================================
        // 11. PEGAR TEXTO RECONHECIDO
        // ====================================================

        if (
          data &&
          Array.isArray(data.ParsedResults) &&
          data.ParsedResults.length > 0
        ) {

          const texto =
            data.ParsedResults[0].ParsedText || "";

          if (texto.trim() !== "") {

            console.log("OCR concluído com sucesso.");

            sendResponse({
              sucesso: true,
              texto: texto
            });

          } else {

            sendResponse({
              sucesso: false,
              erro: "Nenhum texto encontrado na imagem."
            });
          }

        } else {

          sendResponse({
            sucesso: false,
            erro: "Nenhum texto encontrado na imagem."
          });
        }

      } catch (erro) {

        console.error(
          "Erro no processamento OCR:",
          erro
        );

        sendResponse({
          sucesso: false,
          erro: erro?.message || "Erro desconhecido."
        });
      }
    })();


    // ========================================================
    // IMPORTANTE:
    // Mantém o canal aberto para sendResponse assíncrono.
    // ========================================================

    return true;
  }
);


// ============================================================
// MENSAGEM DE TESTE
// ============================================================

console.log(
  "📷 Extensão Copiar Texto (Google Lens) carregada."
);
