"""
Configurações e constantes do jogo (tamanho da tela, cores, velocidades...).

Tudo que é "número mágico" fica aqui, para ser fácil de ajustar a dificuldade
sem precisar caçar valores espalhados pelo código.
"""

# --- Tela ---------------------------------------------------------------
LARGURA = 800
ALTURA = 600
FPS = 60
TITULO = "Nave Espacial - Space Shooter"

# --- Cores (R, G, B) ----------------------------------------------------
PRETO = (5, 5, 15)
BRANCO = (240, 240, 240)
CINZA = (120, 120, 130)
VERMELHO = (230, 60, 60)
VERDE = (70, 220, 90)
AMARELO = (250, 210, 60)
AZUL = (70, 160, 255)
CIANO = (90, 230, 240)
LARANJA = (255, 140, 40)
ROXO = (170, 90, 240)

# --- Nave do jogador ----------------------------------------------------
NAVE_VIDAS = 3
NAVE_VELOCIDADE = 5
NAVE_LARGURA = 44
NAVE_ALTURA = 36
NAVE_INTERVALO_TIRO = 15      # frames entre um tiro e outro
NAVE_INVENCIVEL = 90          # frames "piscando" depois de ser atingida

# --- Inimigos -----------------------------------------------------------
INIMIGO_VIDA = 3
INIMIGO_LARGURA = 48
INIMIGO_ALTURA = 32
INIMIGO_VELOCIDADE = 2.5
INIMIGO_CHANCE_TIRO = 0.012   # chance por frame de cada inimigo atirar
INIMIGO_INTERVALO_MIN = 40    # frames mínimos entre dois tiros do mesmo inimigo

# --- Tiros --------------------------------------------------------------
TIRO_VEL_NAVE = 9
TIRO_VEL_INIMIGO = 5
TIRO_LARGURA = 4
TIRO_ALTURA = 12

# --- Pontuação ----------------------------------------------------------
PONTOS_ACERTO = 100
PONTOS_DESTRUIR = 500

# --- Cenário ------------------------------------------------------------
QTD_ESTRELAS = 90
