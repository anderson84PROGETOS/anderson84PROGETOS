import requests
import time
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
████████╗██████╗  █████╗  ██████╗██╗  ██╗    ██╗   ██╗███████╗███████╗██████╗ 
╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝    ██║   ██║██╔════╝██╔════╝██╔══██╗
   ██║   ██████╔╝███████║██║     █████╔╝     ██║   ██║███████╗█████╗  ██████╔╝
   ██║   ██╔══██╗██╔══██║██║     ██╔═██╗     ██║   ██║╚════██║██╔══╝  ██╔══██╗
   ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗    ╚██████╔╝███████║███████╗██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝
""")

# Função para verificar se o perfil existe
def check_profile(url, username):
    try:
        full_url = url.format(username)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        response = requests.get(full_url, timeout=5, headers=headers)
        if response.status_code == 200:
            return Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{'':<5}[+] Perfil Encontrado: {full_url}"
        return None
    except requests.RequestException as e:        
        return None

# Lista de 50 sites com seus formatos de URL
sites = {
    "Facebook": "https://www.facebook.com/{}",
    "Instagram": "https://www.instagram.com/{}",
    "YouTube": "https://www.youtube.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",
    "X": "https://x.com/{}",
    "Google": "https://www.google.com/search?q={}",
    "Twitter": "https://twitter.com/{}",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "GitHub": "https://github.com/{}",
    "Snapchat": "https://www.snapchat.com/add/{}",
    "Tumblr": "https://{}.tumblr.com",
    "Discord": "https://discord.com/users/{}",
    "Telegram": "https://t.me/{}",
    "Vimeo": "https://vimeo.com/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "DeviantArt": "https://{}.deviantart.com",
    "Flickr": "https://www.flickr.com/people/{}",
    "Medium": "https://medium.com/@{}",
    "Quora": "https://www.quora.com/profile/{}",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "Mixcloud": "https://www.mixcloud.com/{}",
    "Patreon": "https://www.patreon.com/{}",
    "Etsy": "https://www.etsy.com/shop/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Goodreads": "https://www.goodreads.com/user/show/{}",
    "Bandcamp": "https://{}.bandcamp.com",
    "Last.fm": "https://www.last.fm/user/{}",
    "Letterboxd": "https://letterboxd.com/{}",
    "CodePen": "https://codepen.io/{}",
    "Fiverr": "https://www.fiverr.com/{}",
    "Upwork": "https://www.upwork.com/freelancers/{}",
    "ReverbNation": "https://www.reverbnation.com/{}",
    "Myspace": "https://myspace.com/{}",
    "About.me": "https://about.me/{}",
    "500px": "https://500px.com/p/{}",
    "ProductHunt": "https://www.producthunt.com/@{}",
    "Hackerrank": "https://www.hackerrank.com/{}",
    "LeetCode": "https://leetcode.com/{}",
    "Bitbucket": "https://bitbucket.org/{}",
    "SlideShare": "https://www.slideshare.net/{}",
    "Trello": "https://trello.com/{}",
    "Wattpad": "https://www.wattpad.com/user/{}",
    "Imgur": "https://imgur.com/user/{}",
    "Periscope": "https://www.pscp.tv/{}",
    "Chess.com": "https://www.chess.com/member/{}",
}

# Função principal
def sherlock_search():
    username = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do usuário: ").strip()
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nProcurando por: {username}\n")
    
    found_profiles = []  # Lista para armazenar os perfis encontrados
    total_checked = 0  # Contador de sites verificados
    
    for site_name, url_template in sites.items():
        result = check_profile(url_template, username)
        total_checked += 1
        if result:
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{site_name:<15} {result}")
            found_profiles.append(f"{site_name:<15}     [+] Perfil Encontrado: {url_template.format(username)}")
        time.sleep(1)
    
    # Mostra a quantidade de perfis encontrados e sites verificados
    found_count = len(found_profiles)
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nTotal de perfis encontrados: {found_count} de {total_checked} sites verificados")
    
    if found_count == 0:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n[!] Nenhum perfil encontrado.")
    else:
        # Pergunta se deseja salvar
        save_choice = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDeseja salvar os resultados? (s/n): ").strip().lower()
        if save_choice == 's':
            filename = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo (ex: arquivo.txt): ").strip()
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(f"Resultados da busca por: {username}\n")
                    file.write(f"\nTotal de perfis encontrados: {found_count} de {total_checked} sites verificados\n\n")
                    for profile in found_profiles:
                        file.write(profile + "\n")
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos em: {filename}")
            except Exception as e:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n[!] Erro ao salvar o arquivo: {str(e)}")

# Executa o script
if __name__ == "__main__":
    sherlock_search()
    input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
