import subprocess

# Prompt the user for a domain name
domain_name = input('\nEnter a domain name: ')

# Perform 'dig' command for the first query
query1 = subprocess.run(['dig', 'ns', domain_name, '+short'], capture_output=True, text=True)

# Print the output of the first query
print('Output of the first query:')
print(query1.stdout)

# Perform 'dig' command for the second query
query2 = subprocess.run(['dig', 'ns', domain_name, '+short'], capture_output=True, text=True)

# Print the output of the second query
print('Output of the second query:')
print(query2.stdout)

# Prompt the user for a nameserver to use for the zone transfer
nameserver = input('Enter a nameserver for the zone transfer (nsztm1.digi.ninja): ')

# Perform 'dig' command for the zone transfer query
zone_transfer = subprocess.run(['dig', 'axfr', '@' + nameserver, domain_name], capture_output=True, text=True)

# Print the output of the zone transfer query
print('Output of the zone transfer query:')
print(zone_transfer.stdout)
