import subprocess

# Prompt the user for a domain name
domain_name = input('\nDigite o nome do website que deseja consultar: ')

# Perform 'dig' command for the first query
query1 = subprocess.run(['dig', 'ns', domain_name, '+short'], capture_output=True, text=True)

# Print the output of the first query
print('\n↓↓ Servidores DNS ↓↓\n')
print(query1.stdout)

# Perform 'dig' command for the second query
query2 = subprocess.run(['dig', 'ns', domain_name, '+short'], capture_output=True, text=True)

# Prompt the user for a nameserver to use for the zone transfer
nameserver = input('Insira um servidor de nomes para a transferência de zona: ')

# Perform 'dig' command for the zone transfer query
zone_transfer = subprocess.run(['dig', 'axfr', '@' + nameserver, domain_name], capture_output=True, text=True)

# Print the output of the zone transfer query
print('\n↓↓ Saída da consulta de transferência de zona ↓↓\n')
print(zone_transfer.stdout)

input("\nconsulta de transferência de zona terminada [ENTER]")
