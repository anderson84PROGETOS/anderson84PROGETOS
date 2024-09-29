import requests

print("""

███████╗ ██████╗  ██████╗██╗ █████╗ ██╗         ███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝██╔═══██╗██╔════╝██║██╔══██╗██║         ██╔════╝██╔════╝██╔══██╗████╗  ██║
███████╗██║   ██║██║     ██║███████║██║         ███████╗██║     ███████║██╔██╗ ██║
╚════██║██║   ██║██║     ██║██╔══██║██║         ╚════██║██║     ██╔══██║██║╚██╗██║
███████║╚██████╔╝╚██████╗██║██║  ██║███████╗    ███████║╚██████╗██║  ██║██║ ╚████║
╚══════╝ ╚═════╝  ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
                                                                                 
""")

# Definir URLs base das redes sociais e plataformas
social_networks = {
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

def check_username(username):
    found_urls = []
    print(f"\n\nProcurando em redes sociais: {username}\n")
    for network, url in social_networks.items():
        user_url = url.format(username)
        try:
            response = requests.get(user_url)
            if response.status_code == 200:
                print(f"[ {network:<15} ]  Encontrado: {user_url}")
                found_urls.append(user_url)
        except:
            # Ignorando todos os erros para não exibir mensagens
            continue
    
    return found_urls

if __name__ == "__main__":
    user_input = input("\nDigite o nome de usuário que deseja procurar: ")
    found_urls = check_username(user_input)

    if found_urls:
        print(f"\n\nTotal de redes sociais Encontradas: {len(found_urls)}")
        save_choice = input("\n\nVocê deseja salvar os resultados? (s/n): ").strip().lower()
        
        if save_choice == 's':
            file_name = input("\n\nDigite o nome do arquivo para salvar os resultados (exemplo: redessocial.txt): ")
            with open(file_name, 'w') as file:
                for url in found_urls:
                    file.write(url + '\n')
            print(f"\n\nResultados salvos em: {file_name}")
        else:
            print("\n\nResultados não foram salvos.")
    else:
        print("\n\nNenhum resultado encontrado.")

    input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
