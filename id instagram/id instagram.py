import requests
import re

def coletar_target_id(nome_usuario):
    # URL do perfil do Instagram
    url = f"https://www.instagram.com/{nome_usuario}/"

    # Cabeçalhos para evitar bloqueios
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        # Fazer requisição GET para obter o código-fonte
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta uma exceção para status de erro

        # Buscar pelo padrão do target ID
        match = re.search(r'"profile_id":"(\d+)"', response.text)
        if match:
            target_id = match.group(1)
            print(f"\nTarget ID Encontrado: {target_id}")
            return target_id
        else:
            print("\nTarget ID não encontrado. Verifique se o nome de usuário está correto.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"\nErro ao acessar o perfil: {e}")
        return None

def converter_id_para_nome(target_id):
    # URL pública para conversão (não oficial, pode mudar ou exigir ajustes)
    url = f"https://i.instagram.com/api/v1/users/{target_id}/info/"

    # Cabeçalhos típicos
    headers = {
        'User-Agent': 'Instagram 155.0.0.37.107 Android (30/11; 320dpi; 720x1280; Xiaomi; Redmi Note 8; Redmi Note 8; qcom; en_US)',
        'Accept-Language': 'en-US',
        'Connection': 'keep-alive',
    }

    try:
        # Fazer requisição GET para obter informações do usuário
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Verifica erros de status HTTP

        # Parsear JSON retornado
        data = response.json()
        username = data.get('user', {}).get('username', 'Usuário não encontrado')
        print(f"\nNome de usuário correspondente: {username}")
        return username

    except requests.exceptions.RequestException as e:
        print(f"\nErro ao acessar a API para conversão: {e}")
        return None

# Exemplo de uso
if __name__ == "__main__":
    nome_usuario = input("\nDigite o nome de usuário do Instagram: ")
    target_id = coletar_target_id(nome_usuario)
    
    if target_id:
        print("\n\nConvertendo Target ID para nome de usuário")
        converter_id_para_nome(target_id)

    # Pergunta ao usuário se deseja converter outro ID manualmente
    while True:
        opcao = input("\nDeseja converter outro Target ID para nome de usuário? (s/n): ").strip().lower()
        if opcao == 's':
            outro_id = input("\nDigite o Target ID que deseja converter: ")
            converter_id_para_nome(outro_id)
        elif opcao == 'n':
            print("\nSaindo do programa. Até mais!")
            break
        else:
            print("\nOpção inválida. Por favor, digite 's' para sim ou 'n' para não.")

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
