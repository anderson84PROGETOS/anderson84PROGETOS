<?php

// URL base da API do "crt.sh"
$apiUrl = "https://crt.sh/?q=%.{d}&output=json";
echo"\n";
// Domínio alvo (informado pelo usuário)
$alvo = readline("Digite o domínio alvo: ");
echo"\n";
// Realiza a requisição na API, substituindo o placeholder "{d}" pelo domínio alvo
$resultado = file_get_contents(str_replace("{d}", $alvo, $apiUrl));

// Decodifica o resultado da API em um array associativo
$subdominios = json_decode($resultado, true);
echo"\n";
// Cria um arquivo para salvar os subdomínios encontrados
$nomeArquivo = readline("Digite o nome do arquivo para salvar os resultados: ");
$arquivo = fopen($nomeArquivo, "w");

// Percorre o array de subdomínios e salva cada um em uma linha no arquivo
foreach ($subdominios as $subdominio) {
    fwrite($arquivo, $subdominio["name_value"]."\n");
}

// Fecha o arquivo
fclose($arquivo);

// Lê o arquivo e exibe seu conteúdo na tela
echo"\n";
echo "↓↓ Subdomínios Encontrados ↓↓\n";
echo"\n";
echo file_get_contents($nomeArquivo);
