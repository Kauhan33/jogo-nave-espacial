"""
Interface: HUD (vidas, pontos, moedas, inimigos, especiais), tela inicial,
tela de nível, menu de pausa, loja e tela de fim de jogo.

Todas as telas de menu devolvem a lista de `Botao` que desenharam, para o
jogo saber onde o mouse pode clicar. Cada botão carrega uma `acao` (texto)
que o jogo executa — a mesma ação que a tecla equivalente dispara.
"""

from __future__ import annotations

import math

import pygame

import config as cfg
from entidades import PODERES

# Lista única de controles: usada na tela inicial, no menu de pausa e no
# terminal (print), para nunca ficar desatualizada em um lugar só.
CONTROLES = [
    ("Setas / W A S D", "Mover a nave"),
    ("Espaço", "Atirar"),
    ("1 / 2 / 3", "Usar especial (quando carregado)"),
    ("ESC", "Pausar / voltar"),
    ("Enter", "Confirmar / começar"),
    ("Setas Cima/Baixo", "Navegar nos menus"),
    ("L", "Abrir a loja (fim de nível / menu)"),
    ("R", "Reiniciar (pausa) / Ressurgir (fim)"),
    ("M", "Ligar / desligar o som"),
    ("Q", "Sair do jogo"),
    ("Mouse", "Clicar nos botões dos menus"),
]

# Opções do menu de pausa (texto, ação)
OPCOES_PAUSA = [
    ("Continuar", "continuar"),
    ("Reiniciar", "reiniciar"),
    ("Ligar/Desligar som", "som"),
    ("Voltar ao menu inicial", "menu"),
    ("Sair do jogo", "sair"),
]

# Itens da loja na ordem em que aparecem
ITENS_LOJA = list(cfg.LOJA)


class Fontes:
    """Guarda as fontes já carregadas para não recriá-las a cada frame."""

    def __init__(self):
        self.titulo = pygame.font.SysFont("consolas", 64, bold=True)
        self.grande = pygame.font.SysFont("consolas", 36, bold=True)
        self.media = pygame.font.SysFont("consolas", 24)
        self.pequena = pygame.font.SysFont("consolas", 18)


class Botao:
    """Retângulo clicável com um rótulo. `acao` é o que o jogo executa."""

    def __init__(self, x, y, largura, altura, rotulo, acao, cor=cfg.CIANO, ativo=True):
        self.rect = pygame.Rect(int(x), int(y), int(largura), int(altura))
        self.rotulo = rotulo
        self.acao = acao
        self.cor = cor
        self.ativo = ativo

    def contem(self, pos):
        return self.ativo and self.rect.collidepoint(pos)

    def desenhar(self, tela, fonte, mouse, selecionado=False):
        destaque = selecionado or self.contem(mouse)
        if not self.ativo:
            fundo, borda, cor_txt = (25, 25, 35), (70, 70, 80), (110, 110, 120)
        elif destaque:
            fundo = tuple(min(255, c // 3) for c in self.cor)
            borda, cor_txt = self.cor, cfg.BRANCO
        else:
            fundo, borda, cor_txt = (20, 20, 35), (90, 90, 110), self.cor
        pygame.draw.rect(tela, fundo, self.rect, border_radius=8)
        pygame.draw.rect(tela, borda, self.rect, 2, border_radius=8)
        texto(tela, fonte, self.rotulo, self.rect.centerx, self.rect.centery, cor_txt)


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
        y += 30
    # duas colunas: tecla alinhada à direita, função alinhada à esquerda
    for tecla, funcao in CONTROLES:
        texto(tela, fontes.pequena, tecla, cfg.LARGURA // 2 - 20, y, cfg.CIANO, alinhar="direita")
        texto(tela, fontes.pequena, funcao, cfg.LARGURA // 2 + 20, y, cfg.BRANCO, alinhar="esquerda")
        y += 21
    return y


def _icone_poder(tela, fonte, tipo, cx, cy, raio):
    info = PODERES[tipo]
    pygame.draw.circle(tela, info["cor"], (cx, cy), raio)
    pygame.draw.circle(tela, cfg.BRANCO, (cx, cy), raio, 2 if raio > 12 else 1)
    letra = fonte.render(info["letra"], True, cfg.PRETO)
    tela.blit(letra, letra.get_rect(center=(cx, cy)))


# ---------------------------------------------------------------------------
# HUD (durante o jogo)
# ---------------------------------------------------------------------------

def desenhar_hud(tela, fontes, jogo, piscar):
    nave, inimigos = jogo.nave, jogo.inimigos
    # faixa escura no topo
    faixa = pygame.Surface((cfg.LARGURA, 44), pygame.SRCALPHA)
    faixa.fill((0, 0, 0, 120))
    tela.blit(faixa, (0, 0))

    # vidas: um ícone de nave para cada vida restante
    texto(tela, fontes.pequena, "VIDAS", 12, 12, cfg.CINZA, alinhar="esquerda")
    for i in range(nave.vidas):
        nave.desenhar_icone(tela, 80 + i * 26, 8)
    texto(tela, fontes.pequena, f"{nave.vidas}/{cfg.NAVE_VIDAS_MAX}", 84 + nave.vidas * 26, 12, cfg.CINZA, alinhar="esquerda")

    # nível e inimigos restantes
    vivos = sum(1 for ini in inimigos if ini.vivo)
    texto(tela, fontes.media, f"NÍVEL {jogo.nivel}", cfg.LARGURA // 2, 14, cfg.BRANCO)
    texto(tela, fontes.pequena, f"INIMIGOS: {vivos}/{len(inimigos)}", cfg.LARGURA // 2, 34, cfg.VERMELHO)

    # pontuação e moedas
    texto(tela, fontes.media, f"{jogo.pontos:06d}", cfg.LARGURA - 12, 2, cfg.AMARELO, alinhar="direita")
    texto(tela, fontes.pequena, "PONTOS", cfg.LARGURA - 110, 6, cfg.CINZA, alinhar="direita")
    texto(tela, fontes.pequena, f"MOEDAS: {jogo.moedas}", cfg.LARGURA - 12, 26, cfg.LARANJA, alinhar="direita")

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
    if jogo.ressurgir > 0:
        ativos.append(({"nome": "Ressurgir guardado", "cor": cfg.VERDE}, None))
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
    poderes_nivel = jogo.poderes_nivel
    rotulo = "Poder do nível:" if len(poderes_nivel) == 1 else "Poderes do nível:"
    largura_total = fontes.pequena.size(rotulo)[0] + 8 + len(poderes_nivel) * 28
    x = cfg.LARGURA // 2 - largura_total // 2
    texto(tela, fontes.pequena, rotulo, x, cfg.ALTURA - 26, cfg.CINZA, alinhar="esquerda")
    x += fontes.pequena.size(rotulo)[0] + 8 + 12
    for tipo in poderes_nivel:
        _icone_poder(tela, fontes.pequena, tipo, x, cfg.ALTURA - 16, 11)
        x += 28

    # barras de vida grandes dos chefes (logo abaixo da faixa do HUD)
    chefes = [ini for ini in inimigos if ini.chefe]
    if chefes:
        faixa_util = cfg.LARGURA - 40
        largura = min(400, faixa_util // len(chefes) - 24)
        for k, ini in enumerate(chefes):
            cx = 20 + int((k + 0.5) * faixa_util / len(chefes))
            x = cx - largura // 2
            y = 50
            proporcao = max(0.0, ini.vida / ini.vida_max)
            pygame.draw.rect(tela, cfg.CINZA, (x, y, largura, 12), border_radius=4)
            pygame.draw.rect(tela, (220, 50, 80), (x, y, int(largura * proporcao), 12), border_radius=4)
            pygame.draw.rect(tela, cfg.BRANCO, (x, y, largura, 12), 1, border_radius=4)
            rotulo = f"{ini.nome}  {math.ceil(ini.vida)}/{ini.vida_max}" if ini.vivo else f"{ini.nome}  destruído"
            texto(tela, fontes.pequena, rotulo, cx, y + 22, cfg.ROSA if ini.vivo else cfg.CINZA)

    # especiais (canto inferior direito): barra de carga + tecla
    y = cfg.ALTURA - 52
    for i, esp in enumerate(jogo.especiais):
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

    # indicador de som, ressurgir e dica do ESC
    icone_som = "SOM: ON" if jogo.som_ligado else "SOM: OFF"
    texto(tela, fontes.pequena, icone_som, cfg.LARGURA - 12, cfg.ALTURA - 26, cfg.CINZA, alinhar="direita")
    texto(tela, fontes.pequena, "ESC = pausa", 12, cfg.ALTURA - 26, cfg.CINZA, alinhar="esquerda")


# ---------------------------------------------------------------------------
# Tela inicial
# ---------------------------------------------------------------------------

def desenhar_menu_inicial(tela, fontes, mouse, piscar):
    texto(tela, fontes.titulo, "NAVE ESPACIAL", cfg.LARGURA // 2, 80, cfg.CIANO)
    texto(tela, fontes.media, "Sobreviva ao máximo de níveis que conseguir!", cfg.LARGURA // 2, 130, cfg.BRANCO)
    _desenhar_nave_decorativa(tela, cfg.LARGURA // 2, 190)

    botoes = [
        Botao(cfg.LARGURA // 2 - 330, 235, 150, 40, "JOGAR (Enter)", "jogar", cfg.AMARELO),
        Botao(cfg.LARGURA // 2 - 165, 235, 150, 40, "LOJA (L)", "loja", cfg.LARANJA),
        Botao(cfg.LARGURA // 2 + 15, 235, 150, 40, "SOM (M)", "som", cfg.CIANO),
        Botao(cfg.LARGURA // 2 + 180, 235, 150, 40, "SAIR (Q)", "sair", cfg.VERMELHO),
    ]
    for botao in botoes:
        botao.desenhar(tela, fontes.pequena, mouse)

    desenhar_controles(tela, fontes, 305)
    if piscar:
        texto(tela, fontes.pequena, "Pressione ENTER ou clique em JOGAR", cfg.LARGURA // 2, cfg.ALTURA - 14, cfg.AMARELO)
    return botoes


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

def desenhar_pausa(tela, fontes, mouse, selecionada, som_ligado):
    escurecer(tela)
    texto(tela, fontes.titulo, "PAUSA", cfg.LARGURA // 2, 60, cfg.AMARELO)

    botoes = []
    y = 105
    for i, (nome, acao) in enumerate(OPCOES_PAUSA):
        if acao == "som":
            nome = f"Som: {'LIGADO' if som_ligado else 'DESLIGADO'}"
        botao = Botao(cfg.LARGURA // 2 - 160, y, 320, 34, nome, acao)
        botao.desenhar(tela, fontes.media, mouse, selecionado=(i == selecionada))
        botoes.append(botao)
        y += 40

    texto(tela, fontes.pequena, "Cima/Baixo + ENTER, clique, ou ESC para voltar", cfg.LARGURA // 2, y + 4, cfg.CINZA)
    desenhar_controles(tela, fontes, y + 26, titulo=False)
    return botoes


# ---------------------------------------------------------------------------
# Fim de jogo
# ---------------------------------------------------------------------------

def desenhar_fim(tela, fontes, mouse, jogo, piscar):
    escurecer(tela, 150)
    texto(tela, fontes.titulo, "GAME OVER", cfg.LARGURA // 2, 140, cfg.VERMELHO)
    texto(tela, fontes.media, f"Sua nave foi destruída no nível {jogo.nivel}.", cfg.LARGURA // 2, 200, cfg.BRANCO)

    texto(tela, fontes.grande, f"Pontuação: {jogo.pontos}", cfg.LARGURA // 2, 260, cfg.AMARELO)
    if jogo.pontos >= jogo.recorde and jogo.pontos > 0:
        texto(tela, fontes.media, "NOVO RECORDE!", cfg.LARGURA // 2, 300, cfg.VERDE)
    else:
        texto(tela, fontes.media, f"Recorde: {jogo.recorde}", cfg.LARGURA // 2, 300, cfg.CINZA)

    botoes = []
    y = 350
    if jogo.ressurgir > 0:
        botoes.append(Botao(cfg.LARGURA // 2 - 230, y, 460, 40, "RESSURGIR (R) - continuar de onde parou", "ressurgir", cfg.VERDE))
        y += 50
    botoes.append(Botao(cfg.LARGURA // 2 - 170, y, 340, 40, "JOGAR DE NOVO (Enter)", "jogar", cfg.CIANO))
    y += 50
    botoes.append(Botao(cfg.LARGURA // 2 - 170, y, 160, 36, "MENU (ESC)", "menu", cfg.AMARELO))
    botoes.append(Botao(cfg.LARGURA // 2 + 10, y, 160, 36, "SAIR (Q)", "sair", cfg.VERMELHO))
    for botao in botoes:
        botao.desenhar(tela, fontes.pequena, mouse)
    if jogo.ressurgir > 0 and piscar:
        texto(tela, fontes.pequena, "Você tem um Ressurgir guardado!", cfg.LARGURA // 2, 330, cfg.VERDE)
    return botoes


# ---------------------------------------------------------------------------
# Tela entre níveis
# ---------------------------------------------------------------------------

def desenhar_nivel(tela, fontes, mouse, jogo):
    """Aviso de "NÍVEL N" com o(s) poder(es) que vão cair dos inimigos."""
    escurecer(tela, 160)
    texto(tela, fontes.titulo, f"NÍVEL {jogo.nivel}", cfg.LARGURA // 2, 100, cfg.AMARELO)
    linha = jogo.descrever_inimigos() + "  -  vidas restauradas"
    if jogo.tem_chefe:
        qtd = sum(1 for i in jogo.inimigos if i.chefe)
        texto(tela, fontes.grande, "!!! CHEFE !!!" if qtd == 1 else f"!!! {qtd} CHEFES !!!", cfg.LARGURA // 2, 150, cfg.ROSA)
        texto(tela, fontes.media, linha, cfg.LARGURA // 2, 185, cfg.BRANCO)
    else:
        texto(tela, fontes.media, linha, cfg.LARGURA // 2, 160, cfg.BRANCO)

    # ícones dos poderes do nível, lado a lado
    n = len(jogo.poderes_nivel)
    espaco = 60
    x0 = cfg.LARGURA // 2 - (n - 1) * espaco // 2
    for i, tipo in enumerate(jogo.poderes_nivel):
        _icone_poder(tela, fontes.media, tipo, x0 + i * espaco, 240, 22)
    nomes = " + ".join(PODERES[t]["nome"] for t in jogo.poderes_nivel)
    rotulo = "Poder deste nível: " if n == 1 else "Poderes deste nível: "
    texto(tela, fontes.media, rotulo + nomes, cfg.LARGURA // 2, 285, PODERES[jogo.poderes_nivel[0]]["cor"])
    texto(tela, fontes.pequena, "Metade dos inimigos solta poder ao morrer - pegue encostando. Só nesta fase.",
          cfg.LARGURA // 2, 312, cfg.CINZA)

    # painel opaco embaixo (cobre o HUD) com a legenda de poderes e especiais
    pygame.draw.rect(tela, cfg.PRETO, (0, 330, cfg.LARGURA, cfg.ALTURA - 330))
    y = 346
    texto(tela, fontes.pequena, "PODERES", cfg.LARGURA // 2, y, cfg.AMARELO)
    y += 20
    for tipo in PODERES:
        p = PODERES[tipo]
        pygame.draw.circle(tela, p["cor"], (cfg.LARGURA // 2 - 250, y + 8), 8)
        texto(tela, fontes.pequena, f"{p['nome']}: {p['desc']}", cfg.LARGURA // 2 - 235, y, cfg.BRANCO, alinhar="esquerda")
        y += 19
    y += 10
    texto(tela, fontes.pequena, "ESPECIAIS (teclas 1/2/3, carregam com o tempo):", cfg.LARGURA // 2, y, cfg.AMARELO)
    y += 20
    texto(tela, fontes.pequena,
          "     ".join(f"[{i + 1}] {nome} {seg}s" for i, (_, nome, seg) in enumerate(cfg.ESPECIAIS)),
          cfg.LARGURA // 2, y, cfg.CIANO)

    botoes = [
        Botao(cfg.LARGURA // 2 - 250, cfg.ALTURA - 52, 300, 40, "COMEÇAR (Enter)", "comecar", cfg.AMARELO),
        Botao(cfg.LARGURA // 2 + 70, cfg.ALTURA - 52, 180, 40, f"LOJA (L)  {jogo.moedas} moedas", "loja", cfg.LARANJA),
    ]
    for botao in botoes:
        botao.desenhar(tela, fontes.pequena, mouse)
    return botoes


# ---------------------------------------------------------------------------
# Loja
# ---------------------------------------------------------------------------

def nivel_item(jogo, item):
    """Nível atual de um item da loja (upgrade da nave ou Ressurgir)."""
    if item == "ressurgir":
        return jogo.ressurgir
    return jogo.nave.upgrades[item]


def preco_item(jogo, item):
    """Preço do próximo nível do item, ou None se já está no máximo."""
    nivel = nivel_item(jogo, item)
    if nivel >= cfg.LOJA[item]["max"]:
        return None
    return cfg.LOJA[item]["precos"][nivel]


def desenhar_loja(tela, fontes, mouse, jogo, selecionada, so_ver):
    """Loja de upgrades. `so_ver` = aberta pelo menu inicial (não compra)."""
    escurecer(tela, 200)
    texto(tela, fontes.titulo, "LOJA", cfg.LARGURA // 2, 50, cfg.LARANJA)
    if so_ver:
        texto(tela, fontes.pequena, "Só para ver: as compras são feitas no fim de cada nível, com as moedas da partida.",
              cfg.LARGURA // 2, 92, cfg.CINZA)
    else:
        texto(tela, fontes.media, f"Moedas: {jogo.moedas}", cfg.LARGURA // 2, 92, cfg.AMARELO)
    texto(tela, fontes.pequena, f"Cada inimigo destruído = {cfg.PONTOS_INIMIGO} pontos = {cfg.PONTOS_INIMIGO * cfg.MOEDAS_POR_PONTO} moedas",
          cfg.LARGURA // 2, 114, cfg.CINZA)

    botoes = []
    y = 140
    for i, item in enumerate(ITENS_LOJA):
        info = cfg.LOJA[item]
        nivel = nivel_item(jogo, item)
        preco = preco_item(jogo, item)
        caixa = pygame.Rect(40, y, cfg.LARGURA - 80, 78)
        cor_caixa = (35, 35, 55) if i == selecionada else (22, 22, 36)
        pygame.draw.rect(tela, cor_caixa, caixa, border_radius=8)
        pygame.draw.rect(tela, cfg.LARANJA if i == selecionada else (70, 70, 90), caixa, 2, border_radius=8)

        texto(tela, fontes.media, info["nome"], 56, y + 8, cfg.BRANCO, alinhar="esquerda")
        texto(tela, fontes.pequena, info["desc"], 56, y + 40, cfg.CINZA, alinhar="esquerda")
        # bolinhas de nível: ●●○
        for k in range(info["max"]):
            cx = 440 + k * 22
            cor = cfg.VERDE if k < nivel else (60, 60, 75)
            pygame.draw.circle(tela, cor, (cx, y + 20), 8)
            pygame.draw.circle(tela, cfg.BRANCO, (cx, y + 20), 8, 1)
        texto(tela, fontes.pequena, f"{nivel}/{info['max']}", 444 + info["max"] * 22, y + 11, cfg.CINZA, alinhar="esquerda")

        if preco is None:
            rotulo, ativo, cor = "MÁXIMO", False, cfg.VERDE
        elif so_ver:
            rotulo, ativo, cor = f"{preco} moedas", False, cfg.AMARELO
        elif jogo.moedas >= preco:
            rotulo, ativo, cor = f"COMPRAR  {preco}", True, cfg.AMARELO
        else:
            rotulo, ativo, cor = f"faltam {preco - jogo.moedas}", False, cfg.VERMELHO
        botao = Botao(cfg.LARGURA - 220, y + 18, 160, 40, rotulo, f"comprar:{item}", cor, ativo)
        botao.desenhar(tela, fontes.pequena, mouse, selecionado=(i == selecionada and ativo))
        botoes.append(botao)
        y += 88

    voltar = Botao(cfg.LARGURA // 2 - 90, cfg.ALTURA - 50, 180, 38, "VOLTAR (ESC)", "voltar", cfg.CIANO)
    voltar.desenhar(tela, fontes.pequena, mouse)
    botoes.append(voltar)
    texto(tela, fontes.pequena, "Cima/Baixo escolhe, ENTER compra", cfg.LARGURA // 2, cfg.ALTURA - 62, cfg.CINZA)
    return botoes
