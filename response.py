import subprocess

headers = {"User-Agent": "Mozilla/5.0"}

def curl_request(url):
    result = subprocess.run(["curl", "-s", "--head", url], stdout=subprocess.PIPE)
    return result.stdout.decode()

response = curl_request(input("\n Digite nome do Site ou a URL: "))

print("\n",response)

input("\nENTER PRA SAIR !")
