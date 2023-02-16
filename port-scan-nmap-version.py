import nmap

# install:pip install python-nmap

nm = nmap.PortScanner()

host = input("\nDigite o endereço IP do host: ")
start_port = int(input("\nDigite a porta inicial: "))
end_port = int(input("\nDigite a porta final: "))
print("\nEscaneando Aguarde......")
nm.scan(host, str(start_port) + "-" + str(end_port))

for host in nm.all_hosts():
    if nm[host].state() == 'up':
        print('----------------------------------------------------')
        print('Host : %s (%s)' % (host, nm[host].hostname()))
        print('State : %s' % nm[host].state())

        for proto in nm[host].all_protocols():
            print('----------')
            print('Protocol : %s' % proto)

            lport = nm[host][proto].keys()
            for port in lport:
                if nm[host][proto][port]['state'] == 'open':
                    print ('Porta : %s\tServiço : %s\tVersão : %s' % (port, nm[host][proto][port]['name'], nm[host][proto][port]['version']))

input("\n -------FIM DO RESULTADO APERTE ENTER SAIR-------")
