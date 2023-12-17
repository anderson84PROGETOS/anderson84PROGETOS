#!/usr/bin/env python

import subprocess
import os

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    print(output.decode("utf-8"))  # Imprimir a saída do comando
    return output.decode("utf-8"), error.decode("utf-8"), process.returncode

def clean_filename(filename):
    return ''.join(c for c in filename if c.isalnum() or c in ('.', '_'))

def main():
    print("\033[32;5m")
    print("Super Scan findomain subfinder  massdns nmap")          
    print("\033[m")

    target_domain = input("Digite o nome do WebSite: ")

    if not target_domain:
        print("Modo de uso: python3 SuperScan_findomain_subfinder_massdns_nmap.py")
        exit()

    if os.path.exists("ips_full.txt"):
        print("\033[41;1mErro !!\033[m diretório já preenchido com resultado de um alvo.")
        exit()

    clean_target_domain = clean_filename(target_domain)
    print(f"\nRunning findomain for {target_domain}...\n")
    run_command(f"findomain -t {target_domain} --output")

    print(f"\nRunning subfinder for {target_domain}...\n")
    run_command(f"subfinder -d {target_domain} -o subfinder.txt")

    with open("subfinder.txt") as subfinder_file:
        subfinder_data = subfinder_file.read().splitlines()

    with open(f"{clean_target_domain}.txt") as domain_file:
        domain_data = domain_file.read().splitlines()

    combined_data = set(subfinder_data) | set(domain_data)

    with open("subs.txt", "w") as subs_file:
        subs_file.write("\n".join(sorted(combined_data)))

    os.remove("subfinder.txt")

    print("\nRunning massdns...\n")
    run_command(f"massdns -r resolver-dbs.txt -t A subs.txt | grep 'IN A' | awk -F ' ' '{{print $5}}' >> ips.txt")
    
    with open("ips.txt") as ips_file:
        ips_data = ips_file.read().splitlines()

    with open("ips_full.txt", "w") as ips_full_file:
        ips_full_file.write("\n".join(sorted(set(ips_data))))

    os.remove("ips.txt")

    print("\nRunning nmap...\n")
    run_command(f"nmap -D RND:20 --open -sS --top-ports=100 -iL ips_full.txt -oN arquivo_nmap.txt -v")

    print("Results displayed on the screen.")

if __name__ == "__main__":
    main()
