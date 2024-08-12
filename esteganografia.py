import zlib
from stegano import lsb

# Caminho para a imagem original e a imagem de saída
input_image = "imagem.png"  # Nome do seu arquivo de imagem
output_image = "imagem_com_payload.png"

# Caminho para o payload que você quer esconder (por exemplo, um arquivo .exe)
payload_file = "payload.exe"

# Lendo o payload como um texto binário
with open(payload_file, "rb") as file:
    payload_data = file.read()

# Comprimindo o payload
compressed_payload = zlib.compress(payload_data)

# Convertendo o payload comprimido em uma string para esconder usando LSB
compressed_payload_str = compressed_payload.decode('latin-1')

# Escondendo o payload na imagem usando LSB
lsb.hide(input_image, compressed_payload_str).save(output_image)

print(f"Payload escondido em {output_image}")
