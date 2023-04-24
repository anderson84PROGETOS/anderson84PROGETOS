import os
import requests
from bs4 import BeautifulSoup
from PIL import Image


image_name = input('\nDigite o nome da imagem: ')
max_images = int(input('\nDigite o número máximo de imagens a serem baixadas: '))
formats = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'ico', 'svg', 'icns'] # formatos suportados

search_url = f'https://www.google.com.br/search?q={image_name}&tbm=isch'
response = requests.get(search_url)
response.raise_for_status()
soup = BeautifulSoup(response.content, 'html.parser')
img_urls = []

for img in soup.find_all('img'):
    try:
        # Verifica se a URL inclui o esquema (http ou https) e adiciona-o se não estiver presente
        img_url = img.attrs['src']
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif not img_url.startswith(('http', 'https')):
            img_url = f'https:{img_url}'

        # Faz uma requisição HEAD para verificar o tipo de conteúdo da URL
        response = requests.head(img_url)
        content_type = response.headers.get('content-type')
        if content_type and content_type.startswith('image'):
            img_urls.append(img_url)

    except Exception as e:
        print(f'Erro ao processar imagem: {e}')


if not img_urls:
    print(f'Não foi possível encontrar a imagem {image_name}.')
else:
    os.makedirs(image_name, exist_ok=True)
    count = 0
    for img_url in img_urls:
        try:
            # Define o nome do arquivo como um número sequencial
            count += 1
            ext = os.path.splitext(img_url)[1]
            file_name = f'{count}{ext}'

            # Faz o download da imagem e salva no diretório atual
            response = requests.get(img_url)
            with open(os.path.join(image_name, file_name), 'wb') as f:
                f.write(response.content)

            # Verifica se a imagem tem um tamanho mínimo
            with Image.open(os.path.join(image_name, file_name)) as img:
                if min(img.size) < 10:
                    os.remove(os.path.join(image_name, file_name))
                    print(f'A imagem {file_name} foi removida porque é muito pequena.')
                else:
                    print(f'A imagem {file_name} foi baixada com sucesso!')

            # Salva a imagem em outros formatos suportados
            for fmt in formats:
                if ext.lower() != f'.{fmt}':
                    try:
                        img = Image.open(os.path.join(image_name, file_name))
                        new_file_name = f'{count}.{fmt}'
                        img.save(os.path.join(image_name, new_file_name))
                        print(f'A imagem {new_file_name} foi salva com sucesso em formato {fmt.upper()}')
                    except Exception as e:
                        print(f'Erro ao salvar imagem em formato {fmt.upper()}: {e}')

        except Exception as e:
            print(f'Erro ao baixar imagem: {e}')

        if count >= max_images:
            break

if os.path.abspath(image_name) == os.path.abspath('/'):
    print('Não é possível salvar as imagens no diretório raiz do sistema.')
    exit()
