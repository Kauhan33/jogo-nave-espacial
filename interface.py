"""
Interface: HUD (vidas, pontos, inimigos), tela inicial, menu de pausa e tela
de fim de jogo. Também mostra a lista de teclas/controles dentro do jogo.
"""

from __future__ import annotations

import pygame

import config as cfg
from entidades import PODERES

# Lista única de controles: usada na tela inicial, no menu de pausa e no
# terminal (print), para nunca ficar desatualizada em um lugar só.
CONTROLES = [
    ("Setas / W A S D", "Mover a nave"),
    ("Espaço", "Atirar"),
    ("1 / 2 / 3", "Usar especial (quando carregado)"),
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

def desenhar_hud(tela, fontes, nave, inimigos, pontos, som_ligado, nivel, poderes_nivel,
                 especiais, teto_vidas, piscar):
    # faixa escura no topo
    faixa = pygame.Surface((cfg.LARGURA, 44), pygame.SRCALPHA)
    faixa.fill((0, 0, 0, 120))
    tela.blit(faixa, (0, 0))

    # vidas: um ícone de nave para cada vida restante
    texto(tela, fontes.pequena, "VIDAS", 12, 12, cfg.CINZA, alinhar="esquerda")
    for i in range(nave.vidas):
        nave.desenhar_icone(tela, 80 + i * 26, 8)
    texto(tela, fontes.pequena, f"{nave.vidas}/{teto_vidas}", 84 + nave.vidas * 26, 12, cfg.CINZA, alinhar="esquerda")

    # nível e inimigos restantes
    vivos = sum(1 for ini in inimigos if ini.vivo)
    texto(tela, fontes.media, f"NÍVEL {nivel}", cfg.LARGURA // 2, 14, cfg.BRANCO)
    texto(tela, fontes.pequena, f"INIMIGOS: {vivos}/{len(inimigos)}", cfg.LARGURA // 2, 34, cfg.VERMELHO)

    # poderes ativos na nave (com o tempo restante em segundos)
    ativos = []
    if nave.tiro_duplo > 0:
        ativos.append((PODERES["tiro_duplo"], nave.tiro_duplo))
    if nave.tiro_rapido > 0:
        ativos.append((PODERES["tiro_rapido"], nave.tiro_rapido))
    if nave.escudo:
        ativos.append((PODERES["escudo"], None))
    congelados = [ini.congelado for ini in inimigos if ini.vivo and ini.congelado > 0]
    if congelados:
        ativos.append((PODERES["congelar"], max(congelados)))
    # lista no canto inferior esquerdo (longe dos inimigos), crescendo para cima
    y = cfg.ALTURA - 52
    for info, frames in ativos:
        pygame.draw.circle(tela, info["cor"], (22, y), 9)
        pygame.draw.circle(tela, cfg.BRANCO, (22, y), 9, 1)
        rotulo = info["nome"]
        if frames is not None:
            rotulo += f" {frames // cfg.FPS + 1}s"
        texto(tela, fontes.pequena, rotulo, 38, y - 9, info["cor"], alinhar="esquerda")
        y -= 24

    # poder(es) que caem dos inimigos neste nível: rótulo + um ícone por poder
    rotulo = "Poder do nível:" if len(poderes_nivel) == 1 else "Poderes do nível:"
    largura_total = fontes.pequena.size(rotulo)[0] + 8 + len(poderes_nivel) * 28
    x = cfg.LARGURA // 2 - largura_total // 2
    texto(tela, fontes.pequena, rotulo, x, cfg.ALTURA - 26, cfg.CINZA, alinhar="esquerda")
    x += fontes.pequena.size(rotulo)[0] + 8 + 12
    for tipo in poderes_nivel:
        info = PODERES[tipo]
        pygame.draw.circle(tela, info["cor"], (x, cfg.ALTURA - 16), 11)
        pygame.draw.circle(tela, cfg.BRANCO, (x, cfg.ALTURA - 16), 11, 1)
        letra = fontes.pequena.render(info["letra"], True, cfg.PRETO)
        tela.blit(letra, letra.get_rect(center=(x, cfg.ALTURA - 16)))
        x += 28

    # barra de vida grande do chefe (logo abaixo da faixa do HUD)
    for ini in inimigos:
        if ini.vivo and ini.chefe:
            largura = 400
            x = cfg.LARGURA // 2 - largura // 2
            y = 50
            proporcao = ini.vida / ini.vida_max
            pygame.draw.rect(tela, cfg.CINZA, (x, y, largura, 12), border_radius=4)
            pygame.draw.rect(tela, (220, 50, 80), (x, y, int(largura * proporcao), 12), border_radius=4)
            pygame.draw.rect(tela, cfg.BRANCO, (x, y, largura, 12), 1, border_radius=4)
            texto(tela, fontes.pequena, f"{ini.nome}  {ini.vida}/{ini.vida_max}", cfg.LARGURA // 2, y + 22, cfg.ROSA)

    # especiais (canto inferior direito): barra de carga + tecla
    y = cfg.ALTURA - 52
    for i, esp in enumerate(especiais):
        largura = 120
        x = cfg.LARGURA - 12 - largura
        proporcao = min(1.0, esp["carga"] / esp["total"])
        pronto = proporcao >= 1.0
        cor = cfg.VERDE if pronto else cfg.CINZA
        pygame.draw.rect(tela, (40, 40, 50), (x, y - 6, largura, 12), border_radius=3)
        pygame.draw.rect(tela, cor, (x, y - 6, int(largura * proporcao), 12), border_radius=3)
        pygame.draw.rect(tela, cfg.BRANCO, (x, y - 6, largura, 12), 1, border_radius=3)
        if pronto:
            estado = "PRONTO" if piscar else ""
            cor_txt = cfg.VERDE
        else:
            estado = f"{(esp['total'] - esp['carga']) // cfg.FPS + 1}s"
            cor_txt = cfg.CINZA
        texto(tela, fontes.pequena, f"[{i + 1}] {esp['nome']} {estado}", x - 8, y - 9, cor_txt, alinhar="direita")
        y -= 24

    # pontuação
    texto(tela, fontes.media, f"{pontos:06d}", cfg.LARGURA - 12, 8, cfg.AMARELO, alinhar="direita")
    texto(tela, fontes.pequena, "PONTOS", cfg.LARGURA - 110, 12, cfg.CINZA, alinhar="direita")

    # indicador de som e dica do ESC
    icone_som = "SOM: ON" if som_ligado else "SOM: OFF"
    texto(tela, fontes.pequena, icone_som, cfg.LARGURA - 12, cfg.ALTURA - 26, cfg.CINZA, alinhar="direita")
    texto(tela, fontes.pequena, "ESC = pausa", 12, cfg.ALTURA - 26, cfg.CINZA, alinhar="esquerda")


# ---------------------------------------------------------------------------
# Tela inicial
# ---------------------------------------------------------------------------

def desenhar_menu_inicial(tela, fontes, piscar):
    texto(tela, fontes.titulo, "NAVE ESPACIAL", cfg.LARGURA // 2, 110, cfg.CIANO)
    texto(tela, fontes.media, "Sobreviva ao máximo de níveis que conseguir!", cfg.LARGURA // 2, 165, cfg.BRANCO)

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

def desenhar_fim(tela, fontes, nivel, pontos, recorde, piscar):
    escurecer(tela, 150)
    texto(tela, fontes.titulo, "GAME OVER", cfg.LARGURA // 2, 160, cfg.VERMELHO)
    texto(tela, fontes.media, f"Sua nave foi destruída no nível {nivel}.", cfg.LARGURA // 2, 220, cfg.BRANCO)

    texto(tela, fontes.grande, f"Pontuação: {pontos}", cfg.LARGURA // 2, 290, cfg.AMARELO)
    if pontos >= recorde and pontos > 0:
        texto(tela, fontes.media, "NOVO RECORDE!", cfg.LARGURA // 2, 330, cfg.VERDE)
    else:
        texto(tela, fontes.media, f"Recorde: {recorde}", cfg.LARGURA // 2, 330, cfg.CINZA)

    if piscar:
        texto(tela, fontes.media, "ENTER ou R = jogar de novo", cfg.LARGURA // 2, 400, cfg.CIANO)
    texto(tela, fontes.pequena, "ESC ou M = menu inicial      Q = sair", cfg.LARGURA // 2, 440, cfg.CINZA)


# ---------------------------------------------------------------------------
# Tela entre níveis
# ---------------------------------------------------------------------------

def desenhar_nivel(tela, fontes, nivel, qtd_inimigos, poderes_nivel, tem_chefe, teto_vidas):
    """Aviso de "NÍVEL N" com o(s) poder(es) que vão cair dos inimigos."""
    escurecer(tela, 160)
    texto(tela, fontes.titulo, f"NÍVEL {nivel}", cfg.LARGURA // 2, 120, cfg.AMARELO)
    if tem_chefe:
        texto(tela, fontes.grande, "!!! CHEFE !!!", cfg.LARGURA // 2, 175, cfg.ROSA)
        texto(tela, fontes.media, f"{qtd_inimigos} inimigos  -  vidas restauradas (teto {teto_vidas})",
              cfg.LARGURA // 2, 210, cfg.BRANCO)
    else:
        texto(tela, fontes.media, f"{qtd_inimigos} inimigos  -  vidas restauradas (teto {teto_vidas})",
              cfg.LARGURA // 2, 180, cfg.BRANCO)

    # ícones dos poderes do nível, lado a lado
    n = len(poderes_nivel)
    espaco = 60
    x0 = cfg.LARGURA // 2 - (n - 1) * espaco // 2
    for i, tipo in enumerate(poderes_nivel):
        info = PODERES[tipo]
        cx = x0 + i * espaco
        pygame.draw.circle(tela, info["cor"], (cx, 270), 22)
        pygame.draw.circle(tela, cfg.BRANCO, (cx, 270), 22, 2)
        texto(tela, fontes.media, info["letra"], cx, 270, cfg.PRETO)
    nomes = " + ".join(PODERES[t]["nome"] for t in poderes_nivel)
    rotulo = "Poder deste nível: " if n == 1 else "Poderes deste nível: "
    texto(tela, fontes.media, rotulo + nomes, cfg.LARGURA // 2, 315, PODERES[poderes_nivel[0]]["cor"])
    texto(tela, fontes.pequena, "Caem de inimigos destruídos - pegue encostando. Valem só nesta fase.",
          cfg.LARGURA // 2, 342, cfg.CINZA)

    # painel opaco embaixo (cobre o HUD) com a legenda de poderes e especiais
    pygame.draw.rect(tela, cfg.PRETO, (0, 362, cfg.LARGURA, cfg.ALTURA - 362))
    y = 380
    texto(tela, fontes.pequena, "PODERES", cfg.LARGURA // 2, y, cfg.AMARELO)
    y += 22
    for tipo in PODERES:
        p = PODERES[tipo]
        pygame.draw.circle(tela, p["cor"], (cfg.LARGURA // 2 - 250, y + 8), 8)
        texto(tela, fontes.pequena, f"{p['nome']}: {p['desc']}", cfg.LARGURA // 2 - 235, y, cfg.BRANCO, alinhar="esquerda")
        y += 19

    y += 14
    texto(tela, fontes.pequena, "ESPECIAIS (teclas 1/2/3, carregam com o tempo)", cfg.LARGURA // 2, y, cfg.AMARELO)
    y += 22
    texto(tela, fontes.pequena,
          "     ".join(f"[{i + 1}] {nome} {seg}s" for i, (_, nome, seg) in enumerate(cfg.ESPECIAIS)),
          cfg.LARGURA // 2, y, cfg.CIANO)

    # faixa opaca embaixo para o aviso não se misturar com o rodapé do HUD
    pygame.draw.rect(tela, cfg.PRETO, (0, cfg.ALTURA - 30, cfg.LARGURA, 30))
    texto(tela, fontes.pequena, "Pressione qualquer tecla para começar", cfg.LARGURA // 2, cfg.ALTURA - 14, cfg.AMARELO)
