print(r"""
██████╗  ██████╗ ██████╗  ██████╗ ████████╗███████╗   ████████╗██╗  ██╗████████╗
██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝   ╚══██╔══╝╚██╗██╔╝╚══██╔══╝
██████╔╝██║   ██║██████╔╝██║   ██║   ██║   ███████╗      ██║    ╚███╔╝    ██║   
██╔══██╗██║   ██║██╔══██╗██║   ██║   ██║   ╚════██║      ██║    ██╔██╗    ██║   
██║  ██║╚██████╔╝██████╔╝╚██████╔╝   ██║   ███████║██╗   ██║   ██╔╝ ██╗   ██║   
╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝ """)
print("\n")
import urllib.request
import io
def get_robots_txt(url):
    if url.endswith('/'):
        path = url
    else:
        path = url + '/'
    req = urllib.request.urlopen(path + "robots.txt", data=None)
    data = io.TextIOWrapper(req, encoding='utf-8')
    return data.read()
x = input("\033[32mDigite URL :\033[m ")
print(get_robots_txt(x))
input('\n\033[31mPRESSIONE ENTER PARA SAIR')
