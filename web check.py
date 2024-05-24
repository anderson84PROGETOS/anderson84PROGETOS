import sys
import re
import requests

print("""

██╗    ██╗███████╗██████╗      ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██║    ██║██╔════╝██╔══██╗    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██║ █╗ ██║█████╗  ██████╔╝    ██║     ███████║█████╗  ██║     █████╔╝ 
██║███╗██║██╔══╝  ██╔══██╗    ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
╚███╔███╔╝███████╗██████╔╝    ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
 ╚══╝╚══╝ ╚══════╝╚═════╝      ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝
                                                                      
""")

# Print an empty line for better readability
print("")

# Check if a URL parameter is provided; if not, prompt the user
if len(sys.argv) < 2:
    url = input("Digite a URL do website: ")
else:
    url = sys.argv[1]
print("")

# Validate the entered URL (simple validation)
if not re.match(r'^https?://', url):
    print("Error: Invalid URL. Please include http:// or https://")
    sys.exit(1)

# Send a request to the provided or entered URL
try:
    response = requests.get(url)
    
    # Print the content of the response
    print("\n↓ Response Content ↓\n")
    print(response.text)
    print("\n\n\n")
    # Print an empty line for better readability
    print("\n↓ Cabeçalho HTTP Headers ↓\n")
    
    # Print the HTTP headers
    for key, value in response.headers.items():
        print(f"{key}: {value}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    sys.exit(1)

# Print an empty line for better readability
input("\n\n🎯 Pressione Enter para sair 🎯\n")
