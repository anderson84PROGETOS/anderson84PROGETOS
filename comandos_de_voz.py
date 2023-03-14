import speech_recognition as sr
import subprocess

# Definir o reconhecedor de voz
r = sr.Recognizer()

# falar ABRIR PRA ABRIR O chrome
print("FALA ABRIR")
# Definir uma função para ouvir comandos de voz
def ouvir_comandos():
    with sr.Microphone() as source:
        print("\nOuvindo...")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        print("Reconhecendo comando...")
        comando = r.recognize_google(audio, language='pt-BR')
        print(f"Comando: {comando}\n")
        return comando.lower()
    except sr.UnknownValueError:
        print("Não entendi o comando.\n")
        return ""

# Ouvir comandos de voz
comando = ouvir_comandos()

# Verificar se o comando é para abrir o Chrome
if 'abrir' in comando:
    # Ouvir o URL a ser aberto
    print("Qual o Nnome do site que você quer abrir?")
    url = ouvir_comandos()
    # Abrir o Chrome com o URL especificado
    subprocess.Popen(["C:\Program Files\Google\Chrome\Application\chrome.exe", url])
    print(f"Abrindo o Chrome na URL: {url}\n")
    
input("\nAPERTE ENTER SAIR")
