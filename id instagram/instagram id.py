import requests
import re

def coletar_target_id(nome_usuario):
    """
    Coleta o Target ID de um perfil público do Instagram.
    
    :param nome_usuario: Nome de usuário do perfil do Instagram.
    """
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

        # Buscar pelo padrão do Target ID no código-fonte
        match = re.search(r'"profile_id":"(\d+)"', response.text)
        if match:
            target_id = match.group(1)
            print(f"\nTarget ID encontrado: {target_id}")
            print("\n\nAcesse o site para descobrir o nome de usuário pelo ID  -> https://commentpicker.com/instagram-username.php")
            
        else:
            print("\nTarget ID não encontrado. Verifique se o nome de usuário está correto.")
    except requests.exceptions.RequestException as e:
        print(f"\nErro ao acessar o perfil: {e}")

# Exemplo de uso
if __name__ == "__main__":
    nome_usuario = input("\nDigite o nome de usuário do Instagram: ").strip()
    coletar_target_id(nome_usuario)

    input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
