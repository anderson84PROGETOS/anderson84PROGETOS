#!/usr/bin/env python3
# coding=utf-8

from bs4 import BeautifulSoup
import requests
import requests.exceptions
import urllib.parse
from collections import deque
import re
import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

print ()

print (f"{Fore.CYAN}")
print ('''


███████╗███╗   ███╗ █████╗ ██╗██╗         ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
██╔════╝████╗ ████║██╔══██╗██║██║         ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
█████╗  ██╔████╔██║███████║██║██║         ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██╔══╝  ██║╚██╔╝██║██╔══██║██║██║         ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
███████╗██║ ╚═╝ ██║██║  ██║██║███████╗    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                                
''')

print (f"{Fore.CYAN}")
print ("")

user_url=str(input(f'{Fore.CYAN}[+]Insira o URL de destino a ser verificado [https://example.com] : '))
urls = deque([user_url])

scrapped_urls= set()
emails = set()

count = 0
try:
	while len(urls):
		count += 1
		if count == 100:

			break
		url = urls.popleft()
		scrapped_urls.add(url)

		parts=urllib.parse.urlsplit(url)
		base_url = '{0.scheme}://{0.netloc}' . format(parts)

		path=url[:url.rfind('/')+1] if '/' in parts.path else url
		print('[%d] Em processamento: %s' % (count, url))
		
		try:
			response = requests.get(url)	

		except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
			continue

		new_emails = set(re.findall(r'[a-z0-9\. \-+_]+@[a-z0-9\. \-+_]+\.[a-z]+', response.text,re.I))
		emails.update(new_emails)
                
		#windows
		#soup = BeautifulSoup(response.text, features="html.parser")
		
		#kali linux
		soup = BeautifulSoup(response.text, features="lxml")

		for anchor in soup.find_all("a"):
			link = anchor.attrs['href'] if 'href' in anchor.attrs else ''
			if link.startswith('/'):
				link = base_url+ link
			elif not link.startswith('http'):
				link = path + link
			if not link in urls and not link in scrapped_urls:
				urls.append(link)

except KeyboardInterrupt:
	print('[-] Closing!')

print("")
print(f"{Fore.RED}##################" + f"{Fore.CYAN} E-mails :" + f"{Fore.RED}###################### ")
print("")

for mail in emails:
	print(mail)

input("\033[32m\n APERTE ENTER FECHE PROGRAMA !")

