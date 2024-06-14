import requests

print("""

███╗   ███╗ █████╗  ██████╗     █████╗ ██████╗ ██████╗ ██████╗ ███████╗███████╗███████╗
████╗ ████║██╔══██╗██╔════╝    ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔════╝
██╔████╔██║███████║██║         ███████║██║  ██║██║  ██║██████╔╝█████╗  ███████╗███████╗
██║╚██╔╝██║██╔══██║██║         ██╔══██║██║  ██║██║  ██║██╔══██╗██╔══╝  ╚════██║╚════██║
██║ ╚═╝ ██║██║  ██║╚██████╗    ██║  ██║██████╔╝██████╔╝██║  ██║███████╗███████║███████║
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝    ╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
                                                                                       
""")

def obter_fabricante(mac_address):
    # URL da API que fornece informações do fabricante do endereço MAC
    url = f"https://api.macvendors.com/{mac_address}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta um erro para respostas com status de erro
        
        fabricante = response.text  # A resposta é retornada como texto simples
        return fabricante
    except requests.RequestException as e:
        print(f"Erro ao buscar dados: {e}")
        return None

if __name__ == "__main__":
    mac_address = input("\nDigite um Endereço MAC: ")
    fabricante = obter_fabricante(mac_address)
    
    if fabricante:
        print(f"\n\nO Fabricante Do Endereço MAC: {mac_address} É: {fabricante}")        
    else:
        print("\nNão foi possível recuperar as informações do fabricante.")

    input("\n\n\n🎯============ PRESSIONE ENTER PARA SAIR ============🎯\n")

