import requests
import sys
import time
from colorama import Fore, Style, init

init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

 █████╗ ██╗     ██╗          ██████╗ ███████╗██╗███╗   ██╗████████╗    ███████╗██╗████████╗███████╗
██╔══██╗██║     ██║         ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝    ██╔════╝██║╚══██╔══╝██╔════╝
███████║██║     ██║         ██║   ██║███████╗██║██╔██╗ ██║   ██║       ███████╗██║   ██║   █████╗  
██╔══██║██║     ██║         ██║   ██║╚════██║██║██║╚██╗██║   ██║       ╚════██║██║   ██║   ██╔══╝  
██║  ██║███████╗███████╗    ╚██████╔╝███████║██║██║ ╚████║   ██║       ███████║██║   ██║   ███████╗
╚═╝  ╚═╝╚══════╝╚══════╝     ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝       ╚══════╝╚═╝   ╚═╝   ╚══════╝
                                                                                                   
""")

print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nFerramenta OSINT - Procurando perfis existentes em redes sociais\n")

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

    # Sites adultos
    "Pornhub": "https://www.pornhub.com/users/{}",
    "RedTube": "https://www.redtube.com/users/{}",
    "XVideos": "https://www.xvideos.com/profiles/{}",
    "YouPorn": "https://www.youporn.com/user/{}",
    "xHamster": "https://xhamster.com/users/{}",
    "SpankBang": "https://spankbang.com/{}",
    "Fapello": "https://fapello.com/{}", 

    # Sites adicionais
    "UnrulyAgency": "https://unrulyagency.be/{}",    
    "KeyMGMT": "https://key-mgmt.com/{}",   
       
}

# Separação de categorias
sites_adultos = {k: v for k, v in servicos.items() if k.lower() in [
    "pornhub", "redtube", "xvideos", "youporn", "xhamster", "spankbang", "fapello"]}

sites_adicionais = {k: v for k, v in servicos.items() if k in [
    "UnrulyAgency", "KeyMGMT"]}

sites_normais = {k: v for k, v in servicos.items() if k not in sites_adultos and k not in sites_adicionais}

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

def obter_nome_usuario():
    nome_usuario = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o nome de usuário para pesquisar: ").strip()
    if not nome_usuario:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n[-] Nome de usuário não pode ser vazio.")
        sys.exit(1)
    return nome_usuario

def main():
    nome_usuario = obter_nome_usuario()
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[#] Procurando por: {nome_usuario}\n")
    encontrados, encontrados_adultos, encontrados_extra = [], [], []

    # Sites normais
    for servico in sites_normais:
        url = verificar_nome_usuario(servico, nome_usuario)
        if url:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"[+] Encontrado em {servico}:".ljust(35) + f"{Fore.CYAN}{url}")
            encontrados.append(f"{servico}: {url}")
        time.sleep(0.5)

    # Sites adultos
    print(Fore.LIGHTMAGENTA_EX + "\n[!] Verificando sites adultos...\n")
    for servico in sites_adultos:
        url = verificar_nome_usuario(servico, nome_usuario)
        if url:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"[+] Encontrado em {servico}:".ljust(45) + f"{Fore.CYAN}{url}")
            encontrados_adultos.append(f"{servico}: {url}")
        time.sleep(0.5)

    # Sites adicionais
    print(Fore.LIGHTBLUE_EX + "\n[!] Verificando sites adicionais...\n")
    for servico in sites_adicionais:
        url = verificar_nome_usuario(servico, nome_usuario)
        if url:
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT +  f"[+] Encontrado em {servico}:".ljust(45) + f"{Fore.CYAN}{url}")
            encontrados_extra.append(f"{servico}: {url}")
        time.sleep(0.5)

    total = len(encontrados) + len(encontrados_adultos) + len(encontrados_extra)
    if total == 0:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n[-] Nenhum perfil encontrado.")
    else:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[#] Total de perfis encontrados: {total}")

    salvar = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT +  "\nDeseja salvar os resultados em um arquivo .txt? (s/n): ").strip().lower()
    if salvar == 's':
        with open(f"{nome_usuario}_osint_resultados.txt", "w", encoding="utf-8") as f:
            f.write(f"Total de perfis encontrados: {total}\n\n")
            f.write("Perfis encontrados\n\n")
            for item in encontrados:
                f.write(f"{item}\n")
            if encontrados_adultos:
                f.write("\nPerfis encontrados em sites adultos\n\n")
                for item in encontrados_adultos:
                    f.write(f"{item}\n")
            if encontrados_extra:
                f.write("\nPerfis encontrados em sites adicionais\n\n")
                for item in encontrados_extra:
                    f.write(f"{item}\n")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[✔] Resultados salvos em: {nome_usuario} osint_resultados.txt")

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
