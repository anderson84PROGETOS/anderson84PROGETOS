import requests
import time
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from tkinter import filedialog
import subprocess
import webbrowser

# ==== FUNÇÃO PARA ABRIR URL NO CHROME ANÔNIMO ====
def abrir_url_no_chrome_anonima(event=None):
    try:
        selecionado = text_area.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um link para abrir!")
            return

        executavel = None
        if sys.platform == "win32":
            caminhos = [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            ]
            for caminho in caminhos:
                if os.path.exists(caminho):
                    executavel = caminho
                    break

        if executavel:
            subprocess.Popen([executavel, "--incognito", selecionado], shell=False)
        else:
            webbrowser.open_new(selecionado)

    except tk.TclError:
        messagebox.showwarning("Aviso", "Nenhum texto selecionado!")

# Função chamada pelo botão
def iniciar_busca():
    thread = threading.Thread(target=buscar)
    thread.start()

# Cabeçalho HTTP
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Lista de serviços e URLs
servicos = {
    # Sites normais
    "Facebook": "https://www.facebook.com/{}",
    "YouTube": "https://www.youtube.com/@{}",
    "Yandex Search": "https://yandex.com/search/?text={}",
    "X.com": "https://x.com/{}",
    "Instagram": "https://www.instagram.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",    
    "Reddit": "https://www.reddit.com/user/{}",
    "Ebay": "https://www.ebay.com/usr/{}",
    "Wordpress": "https://{}.wordpress.com",
    "Pinterest": "https://www.pinterest.com/{}",
    "Yelp": "https://www.yelp.com/user_details?userid={}",
    "Slack": "https://{}.slack.com",
    "Github": "https://github.com/{}",
    "Tumblr": "https://{}.tumblr.com",
    "Flickr": "https://www.flickr.com/people/{}",
    "Pandora": "https://www.pandora.com/profile/{}",
    "ProductHunt": "https://www.producthunt.com/@{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Vimeo": "https://vimeo.com/{}",
    "Etsy": "https://www.etsy.com/shop/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "BitBucket": "https://bitbucket.org/{}",
    "Meetup": "https://www.meetup.com/members/{}",
    "DailyMotion": "https://www.dailymotion.com/{}",
    "Disqus": "https://disqus.com/by/{}",
    "Medium": "https://medium.com/@{}",
    "Behance": "https://www.behance.net/{}",
    "PayPal": "https://www.paypal.com/paypalme/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Imgur": "https://imgur.com/user/{}",
    "Flipboard": "https://flipboard.com/@{}",
    "Vk": "https://vk.com/{}",
    "Codecademy": "https://www.codecademy.com/profiles/{}",
    "Roblox": "https://www.roblox.com/users/{}",
    "Pastebin": "https://pastebin.com/u/{}",
    "Coinbase": "https://www.coinbase.com/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "Houzz": "https://www.houzz.com/pro/{}",
    "TripAdvisor": "https://www.tripadvisor.com/members/{}",
    "Scribd": "https://www.scribd.com/{}",
    "Venmo": "https://venmo.com/{}",
    "Canva": "https://www.canva.com/{}",
    "Bandcamp": "https://{}.bandcamp.com",
    "Patreon": "https://www.patreon.com/{}",
    "Mixcloud": "https://www.mixcloud.com/{}",
    "Gumroad": "https://gumroad.com/{}",
    "Quora": "https://www.quora.com/profile/{}",
    "Clubhouse": "https://www.clubhouse.com/@{}",
    "Freelance.habr": "https://freelance.habr.com/freelancers/{}",
    "Freelancer": "https://www.freelancer.com/u/{}",
    "GNOME VCS": "https://gitlab.gnome.org/{}",
    "LibraryThing": "https://www.librarything.com/profile/{}",
    "Linktree": "https://linktr.ee/{}",
    "Mydramalist": "https://mydramalist.com/profile/{}",
    "NationStates Nation": "https://www.nationstates.net/nation={}",
    "NationStates Region": "https://www.nationstates.net/region={}",
    "Rajce.net": "https://www.rajce.idnes.cz/{}",
    "SlideShare": "https://www.slideshare.net/{}",
    "TorrentGalaxy": "https://torrentgalaxy.to/torrents.php?search={}",
    "VSCO": "https://vsco.co/{}/gallery",
    "Xbox Gamertag": "https://xboxgamertag.com/search/{}",
    "YandexMusic": "https://music.yandex.com/users/{}/playlists",
    "furaffinity": "https://www.furaffinity.net/user/{}",
    "threads": "https://www.threads.net/@{}",
    "Bluesky": "https://bsky.app/profile/{}.bsky.social",
    "Google Search": "https://www.google.com/search?q={}",
    "Gmail (Google": "https://www.google.com/search?q={}@gmail.com",
    "Hotmail (Google": "https://www.google.com/search?q={}@hotmail.com",
    "Hotmail (Bing": "https://www.bing.com/search?q={}@hotmail.com",

    # Sites adicionais
    "UnrulyAgency": "https://unrulyagency.be/{}",    
    "KeyMGMT": "https://key-mgmt.com/{}",   
       
}
sites_normais = {k: v for k, v in servicos.items()}
# Função para verificar perfil
def verificar_nome_usuario(servico, nome_usuario):
    url_base = servicos[servico]
    try:
        url = url_base.format(nome_usuario)
        resposta = requests.get(url, headers=headers, timeout=5)
        if resposta.status_code == 200:
            return url
    except requests.RequestException:
        pass
    return None

# Função principal de busca
def buscar():
    nome_usuario = entry.get().strip()
    if not nome_usuario:
        messagebox.showerror("Erro", "Digite um nome de usuário!")
        return

    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, f"Procurando por: {nome_usuario}\n\n")

    total_sites = len(servicos)
    progress["maximum"] = total_sites
    progress["value"] = 0

    encontrados, encontrados_adultos, encontrados_extra = [], [], []

    # Sites normais
    text_area.insert(tk.END, "[+] Verificando sites Selecione o Link e Abrir Chrome \n\n\n")
    for i, servico in enumerate(sites_normais):
        url = verificar_nome_usuario(servico, nome_usuario)
        if url:
            text_area.insert(tk.END, f"[✔] {servico}: {url}\n\n")
            encontrados.append(f"{servico}: {url}")
        progress["value"] += 1
        root.update_idletasks()
        time.sleep(0.2)    

    total = len(encontrados) + len(encontrados_adultos) + len(encontrados_extra)
    text_area.insert(tk.END, f"\nTotal de perfis Encontrados: {total}\n")

# Função para salvar manualmente os resultados
def salvar_resultados():
    conteudo = text_area.get("1.0", tk.END).strip()
    if not conteudo:
        messagebox.showwarning("Aviso", "Nenhum resultado para salvar!")
        return
    
    caminho_arquivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        title="Salvar resultados como"
    )
    if caminho_arquivo:
        try:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", f"Resultados salvos em\n\n{caminho_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

# ==== GUI Tkinter ====
root = tk.Tk()
root.title("Ferramenta OSINT - Busca de Usuários")
root.geometry("1020x830")

# Campo de entrada
frame_top = tk.Frame(root)
frame_top.pack(pady=10)

label = tk.Label(frame_top, text="Digite o nome de usuário", font=("Arial", 12))
label.pack(pady=10)

entry = tk.Entry(frame_top, width=40, font=("Arial", 12))
entry.pack(pady=10)

btn = tk.Button(frame_top, text="Buscar", bg="#03fc24", fg="black", command=iniciar_busca, font=("Arial", 10))
btn.pack(pady=10)

# Botão salvar manual
btn_salvar = tk.Button(frame_top, text="Salvar Resultados", bg="#f5b507", fg="black", command=salvar_resultados, font=("Arial", 10))
btn_salvar.pack(pady=5)

btn_abrir = tk.Button(frame_top, text="Abrir Chrome", bg="#07f5f5", fg="black", command=abrir_url_no_chrome_anonima, font=("Arial", 10))
btn_abrir.pack(pady=5)

# Barra de progresso
progress = ttk.Progressbar(root, orient="horizontal", length=800, mode="determinate")
progress.pack(pady=10)

# Área de texto com Scroll
text_area = scrolledtext.ScrolledText(root, width=100, height=26, font=("Consolas", 12))
text_area.pack(pady=10)

root.mainloop()
