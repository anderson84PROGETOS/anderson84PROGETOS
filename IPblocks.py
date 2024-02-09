import subprocess

# Definindo códigos de escape ANSI para cor verde e reset
green_color = '\033[0;32m'
no_color = '\033[0m'

print("")
# Solicita ao usuário o nome do website
website = input("Digite o nome do website: ")

# Verifica se o argumento foi fornecido
if not website:
    print(f"{green_color}O nome do website não foi fornecido.{no_color}")
    exit(1)

print("")
# Realiza a consulta MX
print(f"{green_color}Consultando registros MX para {website}{no_color}")
print("")
subprocess.run(["dig", "-t", "mx", website, "+short"])

print("")
# Solicita ao usuário o nome do Post
post = input("Digite o Post (exemplo: post02.Exemplo.com): ")

print("")
# Se o usuário não fornecer nenhum valor para o post, exibe uma mensagem de aviso
if not post:
    print(f"{green_color}O nome do Post não foi fornecido. Não será usado na consulta.{no_color}")
    print("")
else:
    # Realiza a consulta MX com o nome do Post
    print(f"{green_color}Consultando registros MX para {post}{no_color}")
    print("")
    post_ip = subprocess.getoutput(f"dig +short {post}")
    if not post_ip:
        print(f"{green_color}Não foi possível encontrar o IP para {post}.{no_color}")
    else:
        print("")
        print(f"{green_color}Ping para {post}{no_color}")
        print("")
        subprocess.run(["ping", "-4", "-c", "1", post_ip])
        print("")

print("")
# Realiza o ping para o website original
print(f"{green_color}Ping para {website}{no_color}")
print("")
subprocess.run(["ping", "-4", "-c", "1", website])

print("")
# Solicita ao usuário o endereço IP
print("")
ip_address = input(f"{green_color}Digite o endereço IP para a consulta Whois: {no_color}")

# Verifica se o endereço IP foi fornecido
if not ip_address:
    print(f"{green_color}O endereço IP não foi fornecido. Consultando Whois para {website}...{no_color}")
    subprocess.run(["whois", website])
else:
    print("")
    print(f"{green_color}Consultando Whois para o endereço IP {ip_address}{no_color}")
    subprocess.run(["whois", ip_address])

print("")
print("")
input("➡️ PRESSIONE ENTER PARA SAIR ➡️")
