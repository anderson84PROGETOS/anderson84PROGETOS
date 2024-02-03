import requests

print(r"""            

  ██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗
  ██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝
  ██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   
  ██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   
  ██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   
  ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝                                                           
                                                                             
""")  

def follow_redirects(url):
    try:
        response = requests.get(url, allow_redirects=True)
        print("\n ⬇️   Redirecionamentos ⬇️")
        for i, resp in enumerate(response.history, start=1):
            print(f"\n\n{i}. 🔵 ({resp.status_code}) {resp.url}")
        
        if response.status_code == 200:
            print(f"\n\n\n{len(response.history) + 1}. 🟢 (200 - OK) {response.url}")
        else:
            print(f"\n{len(response.history) + 1}. 🔴 ({response.status_code}) {response.url}")

    except requests.RequestException as e:
        print("\nErro ao seguir redirecionamentos:", e)

def main():
    url = input("\nDigite a URL para verificar o redirecionamento: ")
    follow_redirects(url)

if __name__ == "__main__":
    main()
print("\n\n")
input("\n\nRedirecionamento Finalizado. Pressione 🔚  ​ENTER  🔚​\n")
