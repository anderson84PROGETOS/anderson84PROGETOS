import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# specify the URL of the website you want to scrape
url = input("\ndigite a url do website: ")

print("\n")
# send a GET request to the website
response = requests.get(url)

# parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# find all the <a> tags on the page
links = soup.find_all("a")

# loop through all the links and print out the ones that start with "http" or "https"
for link in links:
    href = link.get("href")
    if href:
        parsed_url = urlparse(href)
        if parsed_url.scheme in ["http", "https"]:
            print(href)

input("\n➡️ fim do scaner website aperte Enter pra sair ⬅️\n")
