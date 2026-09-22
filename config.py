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
GELO = (180, 220, 255)
ROSA = (255, 110, 180)

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

# --- Níveis ---------------------------------------------------------------
INIMIGOS_NIVEL_1 = 2          # nível N tem INIMIGOS_NIVEL_1 + (N - 1) inimigos
NIVEL_VEL_EXTRA = 0.2         # velocidade a mais dos inimigos por nível
NIVEL_TIRO_EXTRA = 0.10       # +10% na chance de tiro por nível
NIVEL_TELA_FRAMES = 150       # tempo (frames) da tela "NÍVEL N"
NIVEIS_SEM_REPETIR = 4        # até esse nível os poderes não se repetem

# --- Poderes --------------------------------------------------------------
NAVE_VIDAS_MAX = 5
PODER_VEL_QUEDA = 2.0
PODER_CHANCE = 0.4            # chance de cair poder nas mortes seguintes à 1ª do nível
PODER_DURACAO = 12 * FPS      # frames de tiro duplo / tiro rápido
CONGELAR_DURACAO = 5 * FPS
EXPLOSAO_ALVOS = 3            # inimigos destruídos pelo poder "explosão"
