import requests
import re

def fazer_requisicao():
    url = input("\nDigite a URL do website (exemplo: http://example.com): ").strip()

    # Lista de cabeçalhos HTTP com dois User-Agents
    headers_list = [
        {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    ]

    for idx, headers in enumerate(headers_list, start=1):
        try:            
            response = requests.get(url, headers=headers)
            
            print(f"\n\n\nRequisição concluída com o User-Agent: {idx}")
            print("\nStatus Code:", response.status_code)

            if idx == 1:
                # Exibir apenas os cabeçalhos da resposta para o primeiro User-Agent
                print("\nCabeçalhos da Resposta\n")
                for key, value in response.headers.items():
                    print(f"{key}: {value}")
            elif idx == 2:
                # Exibir todos os cabeçalhos da resposta e URLs encontradas para o segundo User-Agent
                print("\nCabeçalhos da Resposta\n")
                for key, value in response.headers.items():
                    print(f"{key}: {value}")

                # Extrair URLs completas do conteúdo da resposta, removendo repetições
                print("\n\nURL Encontradas (sem repetições)\n")
                urls = re.findall(r'https?://[^\s"\'>]+', response.text)
                unique_urls = sorted(set(urls))  # Remover duplicatas e ordenar

                if unique_urls:
                    for url in unique_urls:
                        print(url)
                    print(f"\n\nNúmero total de URL Encontradas: {len(unique_urls)}")
                else:
                    print("\nNenhuma URL encontrada no conteúdo.")
        
        except requests.exceptions.RequestException as e:
            print(f"\nErro ao realizar a requisição com User-Agent:", e)

if __name__ == "__main__":
    fazer_requisicao()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
