import requests
import time

# Dicionário de URLs com lugares onde o nome de usuário será verificado
platforms = {
    'Fortnite (Tracker)': 'https://fortnitetracker.com/profile/all/{}',
    'Facebook': 'https://www.facebook.com/{}',
    'Instagram': 'https://www.instagram.com/{}',
    'YouTube': 'https://www.youtube.com/{}',
    'LinkedIn': 'https://www.linkedin.com/in/{}',
    'TikTok': 'https://www.tiktok.com/@{}',
    'Reddit': 'https://www.reddit.com/user/{}',
    'Twitch': 'https://www.twitch.tv/{}',
    'Google': 'https://profiles.google.com/{}',
    'Gmail': 'https://mail.google.com/mail/u/{}',
    'Hotmail': 'https://outlook.live.com/owa/{}',
    'Pinterest': 'https://www.pinterest.com/{}',
    'Snapchat': 'https://www.snapchat.com/add/{}',
    'Spotify': 'https://open.spotify.com/user/{}',
    'Patreon': 'https://www.patreon.com/{}',
    'Etsy': 'https://www.etsy.com/people/{}',
    'Medium': 'https://medium.com/@{}',    
    'Github': 'https://github.com/{}',
    'Disqus': 'https://disqus.com/by/{}',
    'About.me': 'https://about.me/{}',
    'Meetup': 'https://www.meetup.com/members/{}',
    'Periscope': 'https://www.pscp.tv/{}',
    'Behance': 'https://www.behance.net/{}',    
    'Buzzfeed': 'https://buzzfeed.com/{}',
    'Vk': 'https://vk.com/{}',    
    'Gravatar': 'https://en.gravatar.com/{}',
    'Bitbucket': 'https://bitbucket.org/{}',
    '99Designs': 'https://99designs.com/profiles/{}',
    'IFTTT': 'https://ifttt.com/p/{}',
    'SlideShare': 'https://www.slideshare.net/{}',
    'DeviantArt': 'https://www.deviantart.com/{}',
    'CNET': 'https://www.cnet.com/profiles/{}',    
    'Ask.FM': 'https://ask.fm/{}',
    'SourceForge': 'https://sourceforge.net/u/{}',
    'SoundCloud': 'https://soundcloud.com/{}',
    'Shutterstock': 'https://www.shutterstock.com/g/{}',
    'OK.RU': 'https://ok.ru/{}',
    'Last.FM': 'https://www.last.fm/user/{}',
    'Vimeo': 'https://vimeo.com/{}',
    'Dribble': 'https://dribbble.com/{}',    
    'Quora': 'https://www.quora.com/profile/{}',
    'Wikipedia': 'https://en.wikipedia.org/wiki/User:{}',
    'Dailymotion': 'https://www.dailymotion.com/{}',
    'Goodreads': 'https://www.goodreads.com/{}',
    'Indiegogo': 'https://www.indiegogo.com/individuals/{}',
    'TaskRabbit': 'https://www.taskrabbit.com/profile/{}',
    'Dev.to': 'https://dev.to/{}',
    'Houzz': 'https://www.houzz.com/user/{}',
    'GitLab': 'https://gitlab.com/{}',
    'Mastodon': 'https://mastodon.social/@{}',
    'ImageShack': 'https://imageshack.us/user/{}',
    'Steam': 'https://steamcommunity.com/id/{}',
    'Hacker Noon': 'https://hackernoon.com/u/{}',
    'WikiHow': 'https://www.wikihow.com/User:{}',
    'Discord': 'https://discord.com/users/{}',
    'Telegram': 'https://t.me/{}',
    'Ebay': 'https://www.ebay.com/usr/{}',
    'Product Hunt': 'https://www.producthunt.com/@{}',
    'DonationAlerts': 'https://www.donationalerts.com/r/{}',
    'Linktree': 'https://linktr.ee/{}',
    'Roblox': 'https://www.roblox.com/users/{}/profile',
    'IGN': 'https://www.ign.com/users/{}',    
    'Quizlet': 'https://quizlet.com/{}',
    'Genius': 'https://genius.com/{}',
    'Steemit': 'https://steemit.com/@{}',
    'Fandom': 'https://www.fandom.com/u/{}',
    'Yandex Images': 'https://yandex.com/images/{}',  
}

# Cabeçalhos HTTP para evitar erro 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://fortnitetracker.com/',
    'Accept-Encoding': 'gzip, deflate, br'
}

def check_user(username):
    found_urls = []
    print(f"\nProcurando perfis de: {username}\n")
    for platform, url in platforms.items():
        user_url = url.format(username)
        
        try:
            # Passa os cabeçalhos na requisição
            response = requests.get(user_url, headers=headers)
            if response.status_code == 200:
                found_urls.append(f"{platform}: {user_url}")
                print(f"[+] Encontrado no {platform}: {user_url}")
            elif response.status_code == 403:
                print(f"[!] Acesso proibido para {platform}: {user_url}")
            else:
                print(f"[!] Status {response.status_code} ao acessar {user_url}")

            # Adicionar um pequeno delay entre as requisições
            time.sleep(1)  # Espera 1 segundo

        except requests.RequestException as e:
            print(f"[!] Erro ao acessar {user_url}: {e}")
    
    return found_urls

if __name__ == "__main__":
    user_input = input("\nDigite o nome de usuário para buscar: ")
    found_urls = check_user(user_input)
    
    if found_urls:
        print(f"\n\nTotal de redes sociais Encontradas: {len(found_urls)}")
        save_choice = input("\n\nVocê deseja salvar os Resultados? (s/n): ").strip().lower()
        
        if save_choice == 's':
            file_name = input("\n\nDigite o nome do arquivo para salvar os resultados (exemplo: redessocial.txt): ")
            with open(file_name, 'w') as file:
                for url in found_urls:
                    file.write(url + '\n')
            print(f"\n\nResultados salvos Em: {file_name}")
        else:
            print("\n\nResultados não foram salvos.")
    else:
        print("\n\nNenhum resultado Encontrado.")

    input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
