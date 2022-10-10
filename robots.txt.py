import urllib.request
import io
print(r"""           

██████   ██████  ██████   ██████  ████████ ███████    ████████ ██   ██ ████████ 
██   ██ ██    ██ ██   ██ ██    ██    ██    ██            ██     ██ ██     ██    
██████  ██    ██ ██████  ██    ██    ██    ███████       ██      ███      ██    
██   ██ ██    ██ ██   ██ ██    ██    ██         ██       ██     ██ ██     ██    
██   ██  ██████  ██████   ██████     ██    ███████ ██    ██    ██   ██    ██   
                                                                                                                                            """)
print("\n")
def get_robots_txt(url):
    if url.endswith('/'):
        path = url
    else:
        path = url + '/'
    req = urllib.request.urlopen(path + "robots.txt", data=None)
    data = io.TextIOWrapper(req, encoding='utf-8')
    return data.read()
x = input("Digite URL :")
print("\n")
print(get_robots_txt(x))
input("\nAPERTE ENTER PRA SAIR!")
