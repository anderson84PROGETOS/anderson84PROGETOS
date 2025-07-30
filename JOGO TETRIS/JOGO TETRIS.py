import pygame
import random
import json
import os

pygame.init()
pygame.mixer.init()

# --- Sons ---
try:
    som_queda = pygame.mixer.Sound("som_queda.wav")
    som_linha = pygame.mixer.Sound("som_linha.wav")
    som_rotacao = pygame.mixer.Sound("som_rotacao.wav")
    som_clique = pygame.mixer.Sound("som_clique.wav")
except Exception as e:
    print("⚠️ Arquivos de som não encontrados. Sons serão ignorados.")
    som_queda = som_linha = som_rotacao = som_clique = lambda: None

# --- Configurações ---
LARGURA_TELA = 700
ALTURA_TELA = 800
TAMANHO_BLOCO = 30
COLUNAS = 15
LINHAS = 26
AREA_JOGO = COLUNAS * TAMANHO_BLOCO, LINHAS * TAMANHO_BLOCO

# --- Cores ---
PRETO = (0, 0, 0)
CINZA = (50, 50, 50)
BRANCO = (255, 255, 255)
AZUL_ESCURO = (0, 0, 100)
VERMELHO = (255, 0, 0)
COR_BOTAO_START = (100, 255, 100)
COR_BOTAO_PAUSE = (255, 182, 193)
COR_BOTAO_SAVE = (135, 206, 250)
COR_BOTAO_RESET = (255, 255, 102)
COR_BOTAO_CARREGAR = (200, 200, 255)

CORES = {
    'I': (0, 255, 255),
    'O': (255, 255, 0),
    'T': (128, 0, 128),
    'S': (0, 255, 0),
    'Z': (255, 0, 0),
    'J': (0, 0, 255),
    'L': (255, 165, 0)
}

PEÇAS = {
    'S': [['.....', '.....', '..00.', '.00..', '.....'],
          ['.....', '..0..', '..00.', '...0.', '.....']],
    'Z': [['.....', '.....', '.00..', '..00.', '.....'],
          ['.....', '..0..', '.00..', '.0...', '.....']],
    'I': [['..0..', '..0..', '..0..', '..0..', '.....'],
          ['.....', '0000.', '.....', '.....', '.....']],
    'O': [['.....', '.....', '.00..', '.00..', '.....']],
    'J': [['.....', '.0...', '.000.', '.....', '.....'],
          ['.....', '..00.', '..0..', '..0..', '.....'],
          ['.....', '.....', '.000.', '...0.', '.....'],
          ['.....', '..0..', '..0..', '.00..', '.....']],
    'L': [['.....', '...0.', '.000.', '.....', '.....'],
          ['.....', '..0..', '..0..', '..00.', '.....'],
          ['.....', '.....', '.000.', '.0...', '.....'],
          ['.....', '.00..', '..0..', '..0..', '.....']],
    'T': [['.....', '..0..', '.000.', '.....', '.....'],
          ['.....', '..0..', '..00.', '..0..', '.....'],
          ['.....', '.....', '.000.', '..0..', '.....'],
          ['.....', '..0..', '.00..', '..0..', '.....']]
}

class Peca:
    def __init__(self, x, y, tipo):
        self.x = x
        self.y = y
        self.tipo = tipo
        self.forma = PEÇAS[tipo]
        self.cor = CORES[tipo]
        self.rotacao = 0

def formatar_peca(peca):
    posicoes = []
    formato = peca.forma[peca.rotacao % len(peca.forma)]
    for i, linha in enumerate(formato):
        for j, coluna in enumerate(linha):
            if coluna == '0':
                posicoes.append((peca.x + j - 2, peca.y + i - 4))
    return posicoes

def posicao_valida(peca, grade):
    for x, y in formatar_peca(peca):
        if x < 0 or x >= COLUNAS or y >= LINHAS or (y >= 0 and grade[y][x] != PRETO):
            return False
    return True

def criar_grade(bloqueadas):
    grade = [[PRETO for _ in range(COLUNAS)] for _ in range(LINHAS)]
    for (x, y), cor in bloqueadas.items():
        if 0 <= x < COLUNAS and 0 <= y < LINHAS:
            grade[y][x] = cor
    return grade

def limpar_linhas(grade, bloqueadas):
    linhas_removidas = 0
    for i in range(LINHAS - 1, -1, -1):
        if PRETO not in grade[i]:
            linhas_removidas += 1
            for j in range(COLUNAS):
                bloqueadas.pop((j, i), None)
    if linhas_removidas:
        som_linha.play()
        novos = {}
        for (x, y), cor in sorted(bloqueadas.items(), key=lambda item: -item[0][1]):
            nova_y = y
            while nova_y + 1 < LINHAS and (x, nova_y + 1) not in bloqueadas:
                nova_y += 1
            novos[(x, nova_y)] = cor
        bloqueadas.clear()
        bloqueadas.update(novos)
    return linhas_removidas

def nova_peca():
    return Peca(COLUNAS // 2, 0, random.choice(list(PEÇAS.keys())))

def drop_peca(peca, grade):
    while posicao_valida(peca, grade):
        peca.y += 1
    peca.y -= 1
    som_queda.play()

def desenhar_tela(win, grade, peca, proxima, pontos, pausado, game_over):
    win.fill(PRETO)
    pygame.draw.rect(win, AZUL_ESCURO, (AREA_JOGO[0], 0, LARGURA_TELA - AREA_JOGO[0], ALTURA_TELA))
    for i in range(LINHAS):
        for j in range(COLUNAS):
            pygame.draw.rect(win, grade[i][j], (j*TAMANHO_BLOCO, i*TAMANHO_BLOCO, TAMANHO_BLOCO, TAMANHO_BLOCO))
    for x, y in formatar_peca(peca):
        if y >= 0:
            pygame.draw.rect(win, peca.cor, (x*TAMANHO_BLOCO, y*TAMANHO_BLOCO, TAMANHO_BLOCO, TAMANHO_BLOCO))
    for i in range(LINHAS):
        pygame.draw.line(win, CINZA, (0, i*TAMANHO_BLOCO), (AREA_JOGO[0], i*TAMANHO_BLOCO))
    for j in range(COLUNAS):
        pygame.draw.line(win, CINZA, (j*TAMANHO_BLOCO, 0), (j*TAMANHO_BLOCO, AREA_JOGO[1]))
    pygame.draw.rect(win, BRANCO, (AREA_JOGO[0]+20, 20, 170, 160))
    fonte = pygame.font.SysFont('Arial', 24)
    win.blit(fonte.render(f"Pontos: {pontos}", True, PRETO), (AREA_JOGO[0]+30, 30))
    if pausado and not game_over:
        win.blit(fonte.render("Pausado", True, (255, 0, 0)), (AREA_JOGO[0]+30, 70))
    if game_over:
        fonte_grande = pygame.font.SysFont('Arial', 48, bold=True)
        texto = fonte_grande.render("GAME OVER", True, VERMELHO)
        ret = texto.get_rect(center=(AREA_JOGO[0]//2, ALTURA_TELA//2))
        win.blit(texto, ret)

def desenhar_botoes(win, pausado):
    fonte = pygame.font.SysFont("Arial", 24)
    botoes = {
        "start": pygame.Rect(AREA_JOGO[0]+20, 220, 170, 50),
        "pause": pygame.Rect(AREA_JOGO[0]+20, 280, 170, 50),
        "save": pygame.Rect(AREA_JOGO[0]+20, 340, 170, 50),
        "reset": pygame.Rect(AREA_JOGO[0]+20, 400, 170, 50),
        "load": pygame.Rect(AREA_JOGO[0]+20, 460, 170, 50)
    }
    pygame.draw.rect(win, COR_BOTAO_START, botoes["start"])
    pygame.draw.rect(win, COR_BOTAO_PAUSE, botoes["pause"])
    pygame.draw.rect(win, COR_BOTAO_SAVE, botoes["save"])
    pygame.draw.rect(win, COR_BOTAO_RESET, botoes["reset"])
    pygame.draw.rect(win, COR_BOTAO_CARREGAR, botoes["load"])
    win.blit(fonte.render("Começar Jogo", True, PRETO), (AREA_JOGO[0]+30, 230))
    win.blit(fonte.render("Pausar Jogo", True, PRETO), (AREA_JOGO[0]+30, 290))
    win.blit(fonte.render("Salvar Jogo", True, PRETO), (AREA_JOGO[0]+30, 350))
    win.blit(fonte.render("Resetar Jogo", True, PRETO), (AREA_JOGO[0]+30, 410))
    win.blit(fonte.render("Carregar Jogo", True, PRETO), (AREA_JOGO[0]+30, 470))
    return botoes

def desenhar_legenda(win):
    fonte = pygame.font.SysFont("Arial", 18)
    textos = [
        "Teclas:",
        "← / → / ↓ : Mover peça",
        "↑         : Rotacionar",
        "Espaço    : Descer rápido",
        "P         : Pausar",
        "S         : Salvar",
        "C         : Carregar",
        "R         : Resetar"
    ]
    y = 530
    for texto in textos:
        win.blit(fonte.render(texto, True, BRANCO), (AREA_JOGO[0]+20, y))
        y += 25

def salvar_jogo(bloqueadas, peca, proxima, pontos):
    dados = {
        "bloqueadas": {f"{k[0]},{k[1]}": v for k, v in bloqueadas.items()},
        "peca": [peca.x, peca.y, peca.tipo, peca.rotacao],
        "proxima": proxima.tipo,
        "pontos": pontos
    }
    with open("salvo.json", "w") as arq:
        json.dump(dados, arq)

def carregar_jogo():
    if not os.path.exists("salvo.json"):
        return {}, nova_peca(), nova_peca(), 0
    with open("salvo.json") as arq:
        dados = json.load(arq)
    bloqueadas = {}
    for k, v in dados["bloqueadas"].items():
        x, y = map(int, k.split(","))
        bloqueadas[(x, y)] = tuple(v)
    p = Peca(*dados["peca"][:2], dados["peca"][2])
    p.rotacao = dados["peca"][3]
    prox = Peca(COLUNAS // 2, 0, dados["proxima"])
    return bloqueadas, p, prox, dados["pontos"]

def resetar_jogo():
    return {}, nova_peca(), nova_peca(), 0

def checar_game_over(bloqueadas):
    # Se alguma das posições bloqueadas estiver nas linhas acima (ex: y < 0 ou y < 1)
    # ou se a peça nova não pode ser colocada
    for (x, y) in bloqueadas:
        if y < 1:
            return True
    return False

def main():
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption("JOGO TETRIS COM SOM")
    bloqueadas, peca, proxima, pontos = {}, nova_peca(), nova_peca(), 0
    grade = criar_grade(bloqueadas)
    relogio = pygame.time.Clock()
    tempo_queda = 0
    rodando = True
    pausado = True
    game_over = False

    while rodando:
        grade = criar_grade(bloqueadas)
        tempo_queda += relogio.get_rawtime()
        relogio.tick(60)

        if not pausado and not game_over and tempo_queda / 1000 > 0.4:
            tempo_queda = 0
            peca.y += 1
            if not posicao_valida(peca, grade):
                peca.y -= 1
                for pos in formatar_peca(peca):
                    bloqueadas[pos] = peca.cor
                som_queda.play()  # Som de queda da peça
                peca = proxima
                proxima = nova_peca()
                pontos += limpar_linhas(grade, bloqueadas) * 10
                if checar_game_over(bloqueadas):
                    game_over = True
                    pausado = True

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                rodando = False
            if e.type == pygame.KEYDOWN:
                if game_over:
                    # Se game over, só aceita resetar o jogo
                    if e.key == pygame.K_r:
                        bloqueadas, peca, proxima, pontos = resetar_jogo()
                        game_over = False
                        pausado = True
                else:
                    if e.key == pygame.K_LEFT:
                        peca.x -= 1
                        if not posicao_valida(peca, grade):
                            peca.x += 1
                        else:
                            som_clique.play()
                    elif e.key == pygame.K_RIGHT:
                        peca.x += 1
                        if not posicao_valida(peca, grade):
                            peca.x -= 1
                        else:
                            som_clique.play()
                    elif e.key == pygame.K_DOWN:
                        peca.y += 1
                        if not posicao_valida(peca, grade):
                            peca.y -= 1
                        else:
                            som_clique.play()
                    elif e.key == pygame.K_UP:
                        peca.rotacao += 1
                        if not posicao_valida(peca, grade):
                            peca.rotacao -= 1
                        else:
                            som_rotacao.play()
                    elif e.key == pygame.K_SPACE and not pausado:
                        drop_peca(peca, grade)
                        for pos in formatar_peca(peca):
                            bloqueadas[pos] = peca.cor
                        som_queda.play()
                        peca = proxima
                        proxima = nova_peca()
                        pontos += limpar_linhas(grade, bloqueadas) * 10
                        if checar_game_over(bloqueadas):
                            game_over = True
                            pausado = True
                    elif e.key == pygame.K_p:
                        pausado = not pausado
                    elif e.key == pygame.K_s:
                        salvar_jogo(bloqueadas, peca, proxima, pontos)
                    elif e.key == pygame.K_c:
                        bloqueadas, peca, proxima, pontos = carregar_jogo()
                        pausado = False
                    elif e.key == pygame.K_r:
                        bloqueadas, peca, proxima, pontos = resetar_jogo()
                        pausado = True
            if e.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                botoes = desenhar_botoes(tela, pausado)
                if botoes["start"].collidepoint((x, y)):
                    if not game_over:
                        pausado = False
                        som_clique.play()
                elif botoes["pause"].collidepoint((x, y)):
                    if not game_over:
                        pausado = True
                        som_clique.play()
                elif botoes["save"].collidepoint((x, y)):
                    if not game_over:
                        salvar_jogo(bloqueadas, peca, proxima, pontos)
                        som_clique.play()
                elif botoes["reset"].collidepoint((x, y)):
                    bloqueadas, peca, proxima, pontos = resetar_jogo()
                    pausado = True
                    game_over = False
                    som_clique.play()
                elif botoes["load"].collidepoint((x, y)):
                    if not game_over:
                        bloqueadas, peca, proxima, pontos = carregar_jogo()
                        pausado = False
                        som_clique.play()

        desenhar_tela(tela, grade, peca, proxima, pontos, pausado, game_over)
        desenhar_botoes(tela, pausado)
        desenhar_legenda(tela)
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
