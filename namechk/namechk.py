import requests
import sys
import time
from colorama import Fore, Style, init

init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
	███╗   ██╗ █████╗ ███╗   ███╗███████╗ ██████╗██╗  ██╗██╗  ██╗
	████╗  ██║██╔══██╗████╗ ████║██╔════╝██╔════╝██║  ██║██║ ██╔╝
	██╔██╗ ██║███████║██╔████╔██║█████╗  ██║     ███████║█████╔╝ 
	██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝  ██║     ██╔══██║██╔═██╗ 
	██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗╚██████╗██║  ██║██║  ██╗
	╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝
""")

print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nFerramenta OSINT - Procurando perfis existentes em redes sociais\n")

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

servicos = {
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
    "Gmail (Google)": "https://www.google.com/search?q={}@gmail.com",
    "Hotmail (Google)": "https://www.google.com/search?q={}@hotmail.com",
    "Hotmail (Bing)": "https://www.bing.com/search?q={}@hotmail.com",    
    "UnrulyAgency": "https://unrulyagency.be/{}",    
}

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
    nome_usuario = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o nome de usuário para pesquisar: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"").strip()
    if not nome_usuario:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n[-] Nome de usuário não pode ser vazio.")
        sys.exit(1)
    return nome_usuario


def main():
    nome_usuario = obter_nome_usuario()
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[#] Procurando por: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{nome_usuario}\n")
    encontrados = []

    for servico in servicos:
        url = verificar_nome_usuario(servico, nome_usuario)
        if url:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"[+] Encontrado em " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{servico}:".ljust(32) + f"{Fore.CYAN}{url}")
            encontrados.append(f"[+] Encontrado em {servico}:".ljust(42) + url)

        time.sleep(0.5)

    if not encontrados:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n[-] Nenhum perfil encontrado.")
    else:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[#] Total de perfis Encontrados: {len(encontrados)}")

    salvar = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar os resultados em um arquivo .txt? (s/n): ").strip().lower()
    if salvar == 's':
        with open(f"{nome_usuario}_osint_resultados.txt", "w", encoding="utf-8") as f:
            for item in encontrados:
                f.write(f"{item}\n")
            f.write(f"\nTotal de perfis Encontrados: {len(encontrados)}\n")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[✔] Resultados salvos em: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{nome_usuario}_osint_resultados.txt")

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
