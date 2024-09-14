import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext
import webbrowser

# Dicionário para converter códigos de país para nomes completos
PAIS_CODIGO_NOME = {
    'US': 'Estados Unidos',
    'BR': 'Brasil',
    'FR': 'França',
    'DE': 'Alemanha',
    'CN': 'China',
    'JP': 'Japão',
    'IN': 'Índia',
    'IT': 'Itália',
    'RU': 'Rússia',
    'KR': 'Coreia do Sul',
    'MX': 'México',
    'CA': 'Canadá',
    'AU': 'Austrália',
    'ZA': 'África do Sul',
    'AR': 'Argentina',
    'CO': 'Colômbia',
    'CL': 'Chile',
    'PE': 'Peru',
    'VE': 'Venezuela',
    'EG': 'Egito',
    'NG': 'Nigéria',
    'SA': 'Arábia Saudita',
    'TR': 'Turquia',
    'ID': 'Indonésia',
    'SG': 'Singapura',
    'GB': 'Reino Unido',   
    'NL': 'Holanda', 

    # Adicione outros códigos e nomes conforme necessário
}

def obter_informacoes_geonet(website):
    url = f"https://geonet.shodan.io/api/geoping/{website}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        resposta = requests.get(url, headers=headers)
        resposta.raise_for_status()  # Lança uma exceção se a resposta HTTP for um erro
        dados = resposta.json()  # Converte a resposta JSON em um dicionário Python
        return dados
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro", f"Erro ao fazer a solicitação: {e}")
        return None

def formatar_informacoes(dados, text_widget):
    if isinstance(dados, list) and len(dados) > 0:
        for info in dados:
            latlon = info.get('from_loc', {}).get('latlon', 'N/A')
            latitude, longitude = latlon.split(',') if latlon != 'N/A' else ('N/A', 'N/A')
            maps_url = f"https://www.google.com/maps?q={latitude},{longitude}" if latitude != 'N/A' and longitude != 'N/A' else 'N/A'
            
            # Converte o código do país para o nome completo usando o dicionário
            codigo_pais = info.get('from_loc', {}).get('country', 'N/A')
            nome_pais = PAIS_CODIGO_NOME.get(codigo_pais, 'N/A')
            
            formatted_info = (
                f"IP: {info.get('ip', 'N/A')}\n\n"
                f"Está  Online: {'Sim' if info.get('is_alive', False) else 'Não'}\n\n"
                f"RTT Mínimo: {info.get('min_rtt', 'N/A')} ms\n"
                f"RTT Médio: {info.get('avg_rtt', 'N/A')} ms\n"
                f"RTT Máximo: {info.get('max_rtt', 'N/A')} ms\n"
                f"Pacotes Enviados: {info.get('packets_sent', 'N/A')}\n"
                f"Pacotes Recebidos: {info.get('packets_received', 'N/A')}\n"
                f"Perda de Pacotes: {info.get('packet_loss', 'N/A') * 100}%\n"
                f"\nCidade: {info.get('from_loc', {}).get('city', 'N/A')}\n"
                f"País: {nome_pais}\n"  # Exibe o nome completo do país
                f"Latitude: {latitude}\n"
                f"Longitude: {longitude}\n"
                f"URL do Google Maps: {maps_url}\n"
                f"===========================================================\n\n"
            )
            text_widget.insert(tk.END, formatted_info)

def abrir_google_maps_selecionado(text_widget):
    try:
        # Captura o texto selecionado no widget
        selected_text = text_widget.selection_get()
        if "https://www.google.com/maps" in selected_text:
            webbrowser.open(selected_text)  # Abre o link no navegador padrão
        else:
            messagebox.showerror("Erro", "Por favor, selecione um link válido do Google Maps.")
    except tk.TclError:
        messagebox.showerror("Erro", "Nenhum texto foi selecionado.")

def buscar_informacoes():
    website = entrada_website.get()
    if not website:
        messagebox.showerror("Erro", "Por favor, insira um nome de website.")
        return
    text_resultado.delete(1.0, tk.END)  # Limpa o campo de texto
    dados = obter_informacoes_geonet(website)
    if dados:
        formatar_informacoes(dados, text_resultado)

# Criação da janela principal
janela = tk.Tk()
janela.title("Informações de Geolocalização")
janela.geometry("1040x830")

# Campo para inserir o nome do website
tk.Label(janela, text="Digite o nome do website", font=("TkDefaultFont", 11, "bold")).pack(pady=5)
entrada_website = tk.Entry(janela, width=30, font=("TkDefaultFont", 11, "bold"))
entrada_website.pack(pady=5)


# Botão para buscar as informações
btn_buscar = tk.Button(janela, text="Buscar Informações", command=buscar_informacoes, fg="black", bg="#09e845")
btn_buscar.pack(pady=10)

# Botão para abrir o link selecionado do Google Maps
btn_maps = tk.Button(janela, text="Abrir no Google Maps", command=lambda: abrir_google_maps_selecionado(text_resultado), fg="black", bg="#05f2ea")
btn_maps.pack(pady=10)

# Campo para exibir os resultados
text_resultado = scrolledtext.ScrolledText(janela, width=120, height=35, wrap=tk.WORD, font=("TkDefaultFont", 11, "bold"))
text_resultado.pack(pady=5)

# Inicia o loop da janela
janela.mainloop()
