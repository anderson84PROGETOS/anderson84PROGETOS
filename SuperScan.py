#!/usr/bin/env python3

import subprocess
import os

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    print(output.decode("utf-8"))  # Imprimir a saída do comando
    return output.decode("utf-8"), error.decode("utf-8"), process.returncode

def clean_filename(filename):
    return ''.join(c for c in filename if c.isalnum() or c in ('.', '_'))

def create_temp_resolver_file():
    resolvers = ["8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9"]
    with open("temp_resolver.txt", "w") as file:
        for resolver in resolvers:
            file.write(f"{resolver}\n")
    return "temp_resolver.txt"

def main():
    print("\033[32;5m")
    print("Super Scan findomain subfinder massdns nmap")          
    print("\033[m")

    target_domain = input("Digite o nome do WebSite: ")

    if not target_domain:
        print("\nModo de uso: sudo python3 SuperScan.py")
        exit()

    if os.path.exists("ips_full.txt"):
        print("\033[41;1mErro !!\033[m diretório já preenchido com resultado de um alvo.")
        exit()

    clean_target_domain = clean_filename(target_domain)
    print(f"\n\n\nExecutando findomain website: {target_domain}\n")
    run_command(f"findomain -t {target_domain} --output")

    print(f"\nExecutando subfinder website: {target_domain}\n")
    run_command(f"subfinder -d {target_domain} -o subfinder.txt")

    with open("subfinder.txt") as subfinder_file:
        subfinder_data = subfinder_file.read().splitlines()

    with open(f"{clean_target_domain}.txt") as domain_file:
        domain_data = domain_file.read().splitlines()

    combined_data = set(subfinder_data) | set(domain_data)

    with open("subs.txt", "w") as subs_file:
        subs_file.write("\n".join(sorted(combined_data)))

    os.remove("subfinder.txt")

    temp_resolver_file = create_temp_resolver_file()
    
    print("\nExecutando massdns...\n")
    run_command(f"massdns -r {temp_resolver_file} -t A subs.txt | grep 'IN A' | awk -F ' ' '{{print $5}}' > ips.txt")
    
    with open("ips.txt") as ips_file:
        ips_data = ips_file.read().splitlines()

    if not ips_data:
        print("Nenhum IP encontrado.")
        exit()

    print("\nIP Encontrados\n==============\n")
    for ip in sorted(set(ips_data)):
        print(ip)

    with open("ips_full.txt", "w") as ips_full_file:
        ips_full_file.write("\n".join(sorted(set(ips_data))))

    os.remove("ips.txt")
    os.remove("subs.txt")
    os.remove(temp_resolver_file)

    print("\nExecutando nmap...\n")
    nmap_output, nmap_error, nmap_returncode = run_command(f"nmap -D RND:20 --open -sS --top-ports=100 -iL ips_full.txt -oN arquivo_nmap.txt -v")

    print("\nResultados do Nmap:\n")
    print(nmap_output)

    print("Results displayed on the screen.")

if __name__ == "__main__":
    main()
