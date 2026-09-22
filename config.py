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

# --- Pontuação e moedas ---------------------------------------------------
PONTOS_INIMIGO = 10           # cada inimigo destruído vale 10 pontos...
PONTOS_CHEFE = 50             # ...e o chefe 50 x número do chefe
MOEDAS_POR_PONTO = 1          # cada ponto ganho vira 1 moeda para a loja

# --- Cenário ------------------------------------------------------------
QTD_ESTRELAS = 90

# --- Níveis ---------------------------------------------------------------
INIMIGOS_NIVEL_1 = 2          # nível N tem INIMIGOS_NIVEL_1 + (N - 1) inimigos
NIVEL_VEL_EXTRA = 0.2         # velocidade a mais dos inimigos por nível
NIVEL_TIRO_EXTRA = 0.10       # +10% na chance de tiro por nível
NIVEL_TELA_FRAMES = 150       # tempo (frames) da tela "NÍVEL N"
NIVEIS_SEM_REPETIR = 4        # até esse nível os poderes não se repetem

# --- Poderes --------------------------------------------------------------
NAVE_VIDAS_MAX = 5            # teto de vidas (vida extra não passa disso)
PODER_VEL_QUEDA = 2.0
PODER_FRACAO = 0.5            # fração dos inimigos de cada fase que carrega poder
PODER_DURACAO = 12 * FPS      # frames de tiro duplo / tiro rápido
CONGELAR_DURACAO = 5 * FPS
EXPLOSAO_ALVOS = 3            # inimigos destruídos pelo poder "explosão"

# --- Chefe (a cada CHEFE_A_CADA níveis) -----------------------------------
CHEFE_A_CADA = 5
CHEFE_LARGURA = 120
CHEFE_ALTURA = 64
CHEFE_VIDA_BASE = 22          # vida do 1º chefe (nível 5) - ele vem sozinho, por isso mais forte
CHEFE_VIDA_EXTRA = 15         # vida a mais a cada chefe seguinte
CHEFE_VELOCIDADE = 2.4
CHEFE_VEL_EXTRA = 0.4         # velocidade a mais por chefe
CHEFE_CHANCE_TIRO = 0.045
CHEFE_CHANCE_EXTRA = 0.012    # chance de tiro a mais por chefe
CHEFE_TIROS_BASE = 3          # tiros por rajada (leque) do 1º chefe
CHEFE_TIROS_EXTRA = 2         # tiros a mais por chefe (máximo CHEFE_TIROS_MAX)
CHEFE_TIROS_MAX = 9

# --- Ciclos de níveis -------------------------------------------------------
NIVEIS_POR_CICLO = 10         # a cada 10 níveis: +1 chefe permanente, inimigos recomeçam
VIDA_EXTRA_POR_CICLO = 1      # inimigos comuns ganham +1 de vida a cada ciclo
NIVEL_ESCALA_MAX = 10         # o bônus de velocidade/tiro por nível para de crescer aqui

# --- Especiais (carregam com o tempo; tecla 1/2/3) --------------------------
ESPECIAIS = [
    # tipo, nome, segundos para carregar
    ("vida", "Vida extra", 30),
    ("explosao", "Explosão", 60),
    ("tempestade", "Tempestade", 90),
]

# --- Loja (upgrades por partida) --------------------------------------------
LOJA = {
    "movimento": {"nome": "Velocidade de movimento", "max": 5, "precos": [40, 80, 120, 160, 200],
                  "desc": "+20% de velocidade da nave por nível"},
    "cadencia":  {"nome": "Velocidade de tiro", "max": 5, "precos": [50, 100, 150, 200, 250],
                  "desc": "+20% de cadência de tiro por nível"},
    "potencia":  {"nome": "Potência do tiro", "max": 5, "precos": [60, 120, 180, 240, 300],
                  "desc": "+20% de dano por tiro por nível"},
    "ressurgir": {"nome": "Ressurgir", "max": 1, "precos": [150],
                  "desc": "Morreu? Continua de onde parou com 3 vidas"},
}
UPGRADE_BONUS = 0.20          # cada nível de upgrade dá +20% (velocidade, cadência, dano)
