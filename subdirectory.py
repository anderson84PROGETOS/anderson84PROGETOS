import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

url = input("\nEnter the url of the site to consult: (exemplo: http://testphp.vulnweb.com ): ")
print("\n")
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

for link in soup.find_all('a'):

    href = link.get('href')

    parsed_href = urlparse(href)

    if parsed_href.scheme in ['http', 'https']:

        print(href)

input("\nQuery Closed Press Enter Exit !\n")

