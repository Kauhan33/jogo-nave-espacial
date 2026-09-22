"""
Interface: HUD (vidas, pontos, inimigos), tela inicial, menu de pausa e tela
de fim de jogo. Também mostra a lista de teclas/controles dentro do jogo.
"""

from __future__ import annotations

import pygame

import config as cfg

# Lista única de controles: usada na tela inicial, no menu de pausa e no
# terminal (print), para nunca ficar desatualizada em um lugar só.
CONTROLES = [
    ("Setas / W A S D", "Mover a nave"),
    ("Espaço", "Atirar"),
    ("ESC", "Pausar / abrir o menu"),
    ("Enter", "Confirmar / começar"),
    ("Setas Cima/Baixo", "Navegar no menu"),
    ("R", "Reiniciar (na pausa ou no fim)"),
    ("M", "Ligar / desligar o som"),
    ("Q", "Sair do jogo"),
]

# Opções do menu de pausa (texto, ação)
OPCOES_PAUSA = [
    ("Continuar", "continuar"),
    ("Reiniciar", "reiniciar"),
    ("Ligar/Desligar som", "som"),
    ("Voltar ao menu inicial", "menu"),
    ("Sair do jogo", "sair"),
]


class Fontes:
    """Guarda as fontes já carregadas para não recriá-las a cada frame."""

    def __init__(self):
        self.titulo = pygame.font.SysFont("consolas", 64, bold=True)
        self.grande = pygame.font.SysFont("consolas", 36, bold=True)
        self.media = pygame.font.SysFont("consolas", 24)
        self.pequena = pygame.font.SysFont("consolas", 18)


def texto(tela, fonte, msg, x, y, cor=cfg.BRANCO, alinhar="centro"):
    """Desenha `msg` na tela.

    `alinhar` diz o que (x, y) representa: "centro" (centro do texto),
    "esquerda" (canto superior esquerdo) ou "direita" (canto superior direito).
    """
    superficie = fonte.render(msg, True, cor)
    rect = superficie.get_rect()
    if alinhar == "centro":
        rect.center = (x, y)
    elif alinhar == "direita":
        rect.topright = (x, y)
    else:
        rect.topleft = (x, y)
    tela.blit(superficie, rect)
    return rect


def escurecer(tela, alpha=170):
    """Cobre a tela com uma camada escura semitransparente (fundo dos menus)."""
    camada = pygame.Surface((cfg.LARGURA, cfg.ALTURA), pygame.SRCALPHA)
    camada.fill((0, 0, 0, alpha))
    tela.blit(camada, (0, 0))


def desenhar_controles(tela, fontes, y_inicial, titulo=True):
    """Tabela tecla -> função, usada na tela inicial e no menu de pausa."""
    y = y_inicial
    if titulo:
        texto(tela, fontes.media, "CONTROLES", cfg.LARGURA // 2, y, cfg.AMARELO)
        y += 32
    # duas colunas: tecla alinhada à direita, função alinhada à esquerda
    for tecla, funcao in CONTROLES:
        texto(tela, fontes.pequena, tecla, cfg.LARGURA // 2 - 20, y, cfg.CIANO, alinhar="direita")
        texto(tela, fontes.pequena, funcao, cfg.LARGURA // 2 + 20, y, cfg.BRANCO, alinhar="esquerda")
        y += 24
    return y


# ---------------------------------------------------------------------------
# HUD (durante o jogo)
# ---------------------------------------------------------------------------

def desenhar_hud(tela, fontes, nave, inimigos, pontos, som_ligado):
    # faixa escura no topo
    faixa = pygame.Surface((cfg.LARGURA, 44), pygame.SRCALPHA)
    faixa.fill((0, 0, 0, 120))
    tela.blit(faixa, (0, 0))

    # vidas: um ícone de nave para cada vida restante
    texto(tela, fontes.pequena, "VIDAS", 12, 12, cfg.CINZA, alinhar="esquerda")
    for i in range(nave.vidas):
        nave.desenhar_icone(tela, 80 + i * 30, 8)

    # inimigos restantes
    vivos = sum(1 for ini in inimigos if ini.vivo)
    texto(tela, fontes.pequena, f"INIMIGOS: {vivos}/{len(inimigos)}", cfg.LARGURA // 2, 22, cfg.VERMELHO)

    # pontuação
    texto(tela, fontes.media, f"{pontos:06d}", cfg.LARGURA - 12, 8, cfg.AMARELO, alinhar="direita")
    texto(tela, fontes.pequena, "PONTOS", cfg.LARGURA - 110, 12, cfg.CINZA, alinhar="direita")

    # indicador de som e dica do ESC
    icone_som = "SOM: ON" if som_ligado else "SOM: OFF"
    texto(tela, fontes.pequena, icone_som, cfg.LARGURA - 12, cfg.ALTURA - 26, cfg.CINZA, alinhar="direita")
    texto(tela, fontes.pequena, "ESC = pausa   M = som", 12, cfg.ALTURA - 26, cfg.CINZA, alinhar="esquerda")


# ---------------------------------------------------------------------------
# Tela inicial
# ---------------------------------------------------------------------------

def desenhar_menu_inicial(tela, fontes, piscar):
    texto(tela, fontes.titulo, "NAVE ESPACIAL", cfg.LARGURA // 2, 110, cfg.CIANO)
    texto(tela, fontes.media, "Destrua as duas naves inimigas!", cfg.LARGURA // 2, 165, cfg.BRANCO)

    # nave e inimigos decorativos
    _desenhar_nave_decorativa(tela, cfg.LARGURA // 2, 235)

    desenhar_controles(tela, fontes, 290)

    if piscar:
        texto(tela, fontes.grande, "Pressione ENTER para jogar", cfg.LARGURA // 2, 540, cfg.AMARELO)
    texto(tela, fontes.pequena, "Q para sair", cfg.LARGURA // 2, 578, cfg.CINZA)


def _desenhar_nave_decorativa(tela, cx, cy):
    corpo = [(cx, cy - 22), (cx + 26, cy + 14), (cx, cy + 6), (cx - 26, cy + 14)]
    pygame.draw.polygon(tela, cfg.AZUL, corpo)
    pygame.draw.polygon(tela, cfg.BRANCO, corpo, 2)
    pygame.draw.circle(tela, cfg.CIANO, (cx, cy - 4), 7)
    for dx, cor in ((-140, cfg.VERMELHO), (140, cfg.ROXO)):
        x = cx + dx
        ini = [(x - 24, cy - 6), (x, cy + 16), (x + 24, cy - 6), (x + 12, cy - 16), (x - 12, cy - 16)]
        pygame.draw.polygon(tela, cor, ini)
        pygame.draw.polygon(tela, cfg.BRANCO, ini, 2)


# ---------------------------------------------------------------------------
# Menu de pausa
# ---------------------------------------------------------------------------

def desenhar_pausa(tela, fontes, selecionada, som_ligado):
    escurecer(tela)
    texto(tela, fontes.titulo, "PAUSA", cfg.LARGURA // 2, 80, cfg.AMARELO)

    y = 150
    for i, (nome, acao) in enumerate(OPCOES_PAUSA):
        if acao == "som":
            nome = f"Som: {'LIGADO' if som_ligado else 'DESLIGADO'}"
        if i == selecionada:
            cor = cfg.CIANO
            nome = f"> {nome} <"
        else:
            cor = cfg.BRANCO
        texto(tela, fontes.media, nome, cfg.LARGURA // 2, y, cor)
        y += 36

    texto(tela, fontes.pequena, "Cima/Baixo para escolher, ENTER para confirmar, ESC para voltar",
          cfg.LARGURA // 2, y + 6, cfg.CINZA)

    desenhar_controles(tela, fontes, y + 40, titulo=False)


# ---------------------------------------------------------------------------
# Fim de jogo
# ---------------------------------------------------------------------------

def desenhar_fim(tela, fontes, venceu, pontos, piscar):
    escurecer(tela, 150)
    if venceu:
        texto(tela, fontes.titulo, "VITÓRIA!", cfg.LARGURA // 2, 180, cfg.VERDE)
        texto(tela, fontes.media, "Todos os inimigos foram destruídos.", cfg.LARGURA // 2, 240, cfg.BRANCO)
    else:
        texto(tela, fontes.titulo, "GAME OVER", cfg.LARGURA // 2, 180, cfg.VERMELHO)
        texto(tela, fontes.media, "Sua nave foi destruída.", cfg.LARGURA // 2, 240, cfg.BRANCO)

    texto(tela, fontes.grande, f"Pontuação: {pontos}", cfg.LARGURA // 2, 310, cfg.AMARELO)

    if piscar:
        texto(tela, fontes.media, "ENTER ou R = jogar de novo", cfg.LARGURA // 2, 400, cfg.CIANO)
    texto(tela, fontes.pequena, "M = menu inicial      Q = sair", cfg.LARGURA // 2, 440, cfg.CINZA)
