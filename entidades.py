"""
Entidades do jogo: a nave do jogador, os inimigos, os tiros, as explosões e
as estrelas do fundo.

Cada classe sabe se atualizar (mover) e se desenhar. Nenhuma imagem externa é
usada: tudo é desenhado com polígonos/círculos do pygame.
"""

from __future__ import annotations

import math
import random

import pygame

import config as cfg


class Tiro:
    """Um projétil. `dono` é "nave" (sobe) ou "inimigo" (desce)."""

    def __init__(self, x, y, dono, vel_x=0.0, vel_y=None, cor=None, dano=1):
        self.dono = dono
        self.dano = dano
        self.x = float(x)
        self.y = float(y)
        self.vel_x = vel_x
        if dono == "nave":
            self.vel_y = -cfg.TIRO_VEL_NAVE
            self.cor = cfg.CIANO
        else:
            self.vel_y = cfg.TIRO_VEL_INIMIGO
            self.cor = cfg.LARANJA
        if vel_y is not None:
            self.vel_y = vel_y
        if cor is not None:
            self.cor = cor
        self.rect = pygame.Rect(0, 0, cfg.TIRO_LARGURA, cfg.TIRO_ALTURA)
        self.rect.center = (int(self.x), int(self.y))

    def atualizar(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.center = (int(self.x), int(self.y))

    def fora_da_tela(self):
        return (self.rect.bottom < 0 or self.rect.top > cfg.ALTURA
                or self.rect.right < 0 or self.rect.left > cfg.LARGURA)

    def desenhar(self, tela):
        # tiros mais fortes (upgrade de potência) são desenhados mais largos
        r = self.rect.inflate(2 * (self.dano - 1), 0)
        pygame.draw.rect(tela, self.cor, r, border_radius=2)
        # miolo branco para dar "brilho" ao tiro
        pygame.draw.rect(tela, cfg.BRANCO, r.inflate(-2, -6), border_radius=2)


class Nave:
    """A nave controlada pelo jogador."""

    def __init__(self):
        self.largura = cfg.NAVE_LARGURA
        self.altura = cfg.NAVE_ALTURA
        self.rect = pygame.Rect(0, 0, self.largura, self.altura)
        self.rect.center = (cfg.LARGURA // 2, cfg.ALTURA - 70)
        self.vidas = cfg.NAVE_VIDAS
        self.cooldown = 0          # frames até poder atirar de novo
        self.invencivel = 0        # frames restantes de invencibilidade
        self.chama = 0             # animação do fogo do motor
        # poderes ativos
        self.escudo = False        # absorve o próximo dano
        self.tiro_duplo = 0        # frames restantes de tiro duplo
        self.tiro_rapido = 0       # frames restantes de tiro rápido
        # upgrades comprados na loja (nível 0 a 3)
        self.upgrades = {"movimento": 0, "cadencia": 0, "potencia": 0}

    @property
    def velocidade(self):
        return cfg.NAVE_VELOCIDADE + cfg.UPGRADE_MOVIMENTO * self.upgrades["movimento"]

    @property
    def intervalo_tiro(self):
        return max(3, cfg.NAVE_INTERVALO_TIRO - cfg.UPGRADE_CADENCIA * self.upgrades["cadencia"])

    @property
    def dano(self):
        return 1 + cfg.UPGRADE_POTENCIA * self.upgrades["potencia"]

    @property
    def viva(self):
        return self.vidas > 0

    def mover(self, teclas):
        dx = dy = 0
        vel = self.velocidade
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= vel
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += vel
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= vel
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += vel
        self.rect.x += dx
        self.rect.y += dy
        # mantém a nave dentro da tela e na metade de baixo
        self.rect.clamp_ip(pygame.Rect(0, cfg.ALTURA // 2, cfg.LARGURA, cfg.ALTURA // 2))

    def atualizar(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invencivel > 0:
            self.invencivel -= 1
        if self.tiro_duplo > 0:
            self.tiro_duplo -= 1
        if self.tiro_rapido > 0:
            self.tiro_rapido -= 1
        self.chama = (self.chama + 1) % 6

    def atirar(self):
        """Devolve uma lista de Tiros (vazia se o cooldown não permitir).

        Com "tiro duplo" saem dois tiros lado a lado; com "tiro rápido" o
        intervalo entre tiros cai pela metade.
        """
        if self.cooldown > 0:
            return []
        self.cooldown = self.intervalo_tiro
        if self.tiro_rapido > 0:
            self.cooldown //= 2
        if self.tiro_duplo > 0:
            return [Tiro(self.rect.centerx - 10, self.rect.top + 6, "nave", dano=self.dano),
                    Tiro(self.rect.centerx + 10, self.rect.top + 6, "nave", dano=self.dano)]
        return [Tiro(self.rect.centerx, self.rect.top, "nave", dano=self.dano)]

    def receber_dano(self):
        """Aplica um dano. Devolve "nada" (estava invencível), "escudo"
        (o escudo absorveu) ou "vida" (perdeu uma vida)."""
        if self.invencivel > 0:
            return "nada"
        self.invencivel = cfg.NAVE_INVENCIVEL
        if self.escudo:
            self.escudo = False
            return "escudo"
        self.vidas -= 1
        return "vida"

    def aplicar_poder(self, tipo, teto_vidas=cfg.VIDAS_TETO_MIN):
        """Ativa um poder na nave (os que afetam só a nave).

        `teto_vidas` é o máximo de vidas permitido no nível atual.
        Devolve False se o poder não teve efeito (ex.: vidas já no teto).
        """
        if tipo == "tiro_duplo":
            self.tiro_duplo = cfg.PODER_DURACAO
        elif tipo == "tiro_rapido":
            self.tiro_rapido = cfg.PODER_DURACAO
        elif tipo == "escudo":
            self.escudo = True
        elif tipo == "vida":
            if self.vidas >= teto_vidas:
                return False
            self.vidas += 1
        return True

    def limpar_poderes(self):
        """Fim de nível: os poderes coletados valem só na fase em que caíram."""
        self.tiro_duplo = 0
        self.tiro_rapido = 0
        self.escudo = False

    def desenhar(self, tela):
        # pisca enquanto está invencível
        if self.invencivel > 0 and (self.invencivel // 5) % 2 == 0:
            return
        r = self.rect
        corpo = [(r.centerx, r.top), (r.right, r.bottom - 6),
                 (r.centerx, r.bottom - 14), (r.left, r.bottom - 6)]
        pygame.draw.polygon(tela, cfg.AZUL, corpo)
        pygame.draw.polygon(tela, cfg.BRANCO, corpo, 2)
        # cabine
        pygame.draw.circle(tela, cfg.CIANO, (r.centerx, r.centery - 2), 6)
        # fogo do motor (animado)
        tamanho = 8 + (4 if self.chama < 3 else 0)
        fogo = [(r.centerx - 6, r.bottom - 12), (r.centerx + 6, r.bottom - 12),
                (r.centerx, r.bottom - 12 + tamanho)]
        pygame.draw.polygon(tela, cfg.LARANJA, fogo)
        pygame.draw.polygon(tela, cfg.AMARELO, fogo, 1)
        # escudo: círculo em volta da nave
        if self.escudo:
            pygame.draw.circle(tela, cfg.CIANO, r.center, r.width // 2 + 10, 2)

    def desenhar_icone(self, tela, x, y, escala=0.5):
        """Versão pequena da nave, usada no HUD para mostrar as vidas."""
        w = int(self.largura * escala)
        h = int(self.altura * escala)
        pts = [(x + w // 2, y), (x + w, y + h - 3), (x + w // 2, y + h - 7), (x, y + h - 3)]
        pygame.draw.polygon(tela, cfg.AZUL, pts)
        pygame.draw.polygon(tela, cfg.BRANCO, pts, 1)


class Inimigo:
    """Nave inimiga. Tem barra de vida e atira contra o jogador.

    `padrao` define o movimento: "vaivem" (anda de um lado para o outro e
    rebate na borda) ou "onda" (movimento senoidal, sobe e desce).
    """

    def __init__(self, x, y, padrao="vaivem", cor=cfg.VERMELHO, nome="Inimigo", nivel=1):
        self.nome = nome
        self.cor = cor
        self.padrao = padrao
        self.rect = pygame.Rect(0, 0, cfg.INIMIGO_LARGURA, cfg.INIMIGO_ALTURA)
        self.rect.center = (x, y)
        self.x = float(x)
        self.y_base = float(y)
        self.vida_max = cfg.INIMIGO_VIDA
        self.vida = self.vida_max
        self.direcao = random.choice([-1, 1])
        # cada nível deixa os inimigos um pouco mais rápidos e mais atiradores
        self.velocidade = cfg.INIMIGO_VELOCIDADE + cfg.NIVEL_VEL_EXTRA * (nivel - 1)
        self.chance_tiro = cfg.INIMIGO_CHANCE_TIRO * (1 + cfg.NIVEL_TIRO_EXTRA * (nivel - 1))
        self.tempo = random.uniform(0, math.pi * 2)   # fase da onda
        self.recarga = cfg.INIMIGO_INTERVALO_MIN
        self.piscar = 0                                 # frames de "flash" ao ser atingido
        self.congelado = 0                              # frames parado (poder "congelar")
        self.chefe = False
        self.pontos_morte = cfg.PONTOS_INIMIGO
        self.solta_poder = False                        # decidido pelo Jogo ao montar a fase

    @property
    def vivo(self):
        return self.vida > 0

    def atualizar(self):
        if self.piscar > 0:
            self.piscar -= 1
        if self.congelado > 0:
            self.congelado -= 1
            return                                      # congelado: não se move nem recarrega
        self.tempo += 0.03
        meia_largura = self.rect.width // 2
        if self.padrao == "vaivem":
            self.x += self.velocidade * self.direcao
            y = self.y_base + math.sin(self.tempo * 2) * 12
        else:  # "onda"
            self.x += self.velocidade * 0.8 * self.direcao
            y = self.y_base + math.sin(self.tempo * 3) * 40
        # rebate nas bordas laterais
        if self.x < meia_largura or self.x > cfg.LARGURA - meia_largura:
            self.direcao *= -1
            self.x = max(meia_largura, min(cfg.LARGURA - meia_largura, self.x))
        self.rect.center = (int(self.x), int(y))

        if self.recarga > 0:
            self.recarga -= 1

    def tentar_atirar(self, alvo_rect):
        """Com uma pequena chance por frame, dispara um tiro mirando na nave."""
        if self.congelado > 0 or self.recarga > 0 or random.random() > self.chance_tiro:
            return None
        self.recarga = cfg.INIMIGO_INTERVALO_MIN
        # mira: desloca o tiro no eixo X na direção da nave
        dx = alvo_rect.centerx - self.rect.centerx
        dy = max(1, alvo_rect.centery - self.rect.centery)
        vel_x = (dx / dy) * cfg.TIRO_VEL_INIMIGO
        vel_x = max(-3.0, min(3.0, vel_x))
        return Tiro(self.rect.centerx, self.rect.bottom, "inimigo", vel_x)

    def receber_dano(self, dano=1):
        """Perde `dano` de vida e fica mais rápido. Devolve True se morreu."""
        self.vida -= dano
        self.piscar = 8
        self.velocidade += 0.6
        return self.vida <= 0

    def desenhar(self, tela):
        r = self.rect
        if self.piscar > 0:
            cor = cfg.BRANCO
        elif self.congelado > 0:
            cor = cfg.GELO
        else:
            cor = self.cor
        corpo = [(r.left, r.top + 6), (r.centerx, r.bottom), (r.right, r.top + 6),
                 (r.centerx + 12, r.top), (r.centerx - 12, r.top)]
        pygame.draw.polygon(tela, cor, corpo)
        pygame.draw.polygon(tela, cfg.BRANCO, corpo, 2)
        pygame.draw.circle(tela, cfg.AMARELO, (r.centerx, r.centery), 5)
        if self.congelado > 0:
            pygame.draw.circle(tela, cfg.CIANO, r.center, r.width // 2 + 6, 1)
        self._desenhar_barra_vida(tela)

    def _desenhar_barra_vida(self, tela):
        """Barra de vida logo acima do inimigo: verde -> amarelo -> vermelho."""
        largura = self.rect.width
        altura = 6
        x = self.rect.left
        y = self.rect.top - 12
        proporcao = self.vida / self.vida_max
        if proporcao > 0.66:
            cor = cfg.VERDE
        elif proporcao > 0.33:
            cor = cfg.AMARELO
        else:
            cor = cfg.VERMELHO
        pygame.draw.rect(tela, cfg.CINZA, (x, y, largura, altura), border_radius=3)
        pygame.draw.rect(tela, cor, (x, y, int(largura * proporcao), altura), border_radius=3)
        pygame.draw.rect(tela, cfg.BRANCO, (x, y, largura, altura), 1, border_radius=3)
        # divisórias: uma marca para cada ponto de vida
        for i in range(1, self.vida_max):
            mx = x + int(largura * i / self.vida_max)
            pygame.draw.line(tela, cfg.PRETO, (mx, y), (mx, y + altura))


class Chefe(Inimigo):
    """Inimigo grande que aparece a cada CHEFE_A_CADA níveis.

    `tier` é o número do chefe (1 no nível 5, 2 no nível 10...): cada chefe
    tem mais vida, é mais rápido, atira mais vezes e com mais tiros por
    rajada (em leque). É imune à explosão.
    """

    def __init__(self, x, y, tier, nivel):
        super().__init__(x, y, padrao="vaivem", cor=(200, 40, 70), nome=f"CHEFE {tier}", nivel=nivel)
        self.chefe = True
        self.tier = tier
        self.rect = pygame.Rect(0, 0, cfg.CHEFE_LARGURA, cfg.CHEFE_ALTURA)
        self.rect.center = (x, y)
        self.vida_max = cfg.CHEFE_VIDA_BASE + cfg.CHEFE_VIDA_EXTRA * (tier - 1)
        self.vida = self.vida_max
        self.velocidade = cfg.CHEFE_VELOCIDADE + cfg.CHEFE_VEL_EXTRA * (tier - 1)
        self.chance_tiro = cfg.CHEFE_CHANCE_TIRO + cfg.CHEFE_CHANCE_EXTRA * (tier - 1)
        self.tiros_por_rajada = min(cfg.CHEFE_TIROS_MAX, cfg.CHEFE_TIROS_BASE + cfg.CHEFE_TIROS_EXTRA * (tier - 1))
        self.vel_tiro = cfg.TIRO_VEL_INIMIGO + 0.5 * (tier - 1)
        self.pontos_morte = cfg.PONTOS_CHEFE * tier
        self.solta_poder = True                         # o chefe sempre solta poder

    def tentar_atirar(self, alvo_rect):
        """Rajada em leque: vários tiros abrindo a partir do centro do chefe."""
        if self.congelado > 0 or self.recarga > 0 or random.random() > self.chance_tiro:
            return None
        self.recarga = cfg.INIMIGO_INTERVALO_MIN
        tiros = []
        n = self.tiros_por_rajada
        for i in range(n):
            # espalha de -2.5 a +2.5 no eixo X (mais tiros = leque mais fechado)
            vel_x = -2.5 + 5.0 * i / max(1, n - 1)
            tiros.append(Tiro(self.rect.centerx, self.rect.bottom, "inimigo",
                              vel_x, self.vel_tiro, cfg.ROSA))
        return tiros

    def receber_dano(self, dano=1):
        """O chefe não acelera a cada acerto como os inimigos comuns."""
        self.vida -= dano
        self.piscar = 6
        return self.vida <= 0

    def desenhar(self, tela):
        r = self.rect
        if self.piscar > 0:
            cor = cfg.BRANCO
        elif self.congelado > 0:
            cor = cfg.GELO
        else:
            cor = self.cor
        corpo = [(r.left, r.top + 20), (r.left + 30, r.top), (r.right - 30, r.top),
                 (r.right, r.top + 20), (r.right - 20, r.bottom - 10), (r.centerx, r.bottom),
                 (r.left + 20, r.bottom - 10)]
        pygame.draw.polygon(tela, cor, corpo)
        pygame.draw.polygon(tela, cfg.BRANCO, corpo, 3)
        # "olhos" e canhão central
        for dx in (-28, 28):
            pygame.draw.circle(tela, cfg.AMARELO, (r.centerx + dx, r.centery - 6), 8)
            pygame.draw.circle(tela, cfg.PRETO, (r.centerx + dx, r.centery - 6), 3)
        pygame.draw.rect(tela, cfg.CINZA, (r.centerx - 8, r.bottom - 22, 16, 22), border_radius=3)
        if self.congelado > 0:
            pygame.draw.ellipse(tela, cfg.CIANO, r.inflate(16, 16), 2)
        # a barra de vida do chefe é desenhada pelo HUD (grande, no topo)


# Catálogo de poderes: tipo -> nome, cor, letra do ícone e descrição
PODERES = {
    "tiro_duplo":  {"nome": "Tiro duplo",  "cor": cfg.CIANO,   "letra": "D",
                    "desc": "Atira dois tiros de uma vez por 12 s"},
    "explosao":    {"nome": "Explosão",    "cor": cfg.LARANJA, "letra": "X",
                    "desc": f"Destrói até {cfg.EXPLOSAO_ALVOS} inimigos aleatórios (não afeta o chefe)"},
    "escudo":      {"nome": "Escudo",      "cor": cfg.AZUL,    "letra": "E",
                    "desc": "Absorve o próximo tiro inimigo"},
    "vida":        {"nome": "Vida extra",  "cor": cfg.VERDE,   "letra": "+",
                    "desc": "Ganha 1 vida (acumula entre os níveis)"},
    "congelar":    {"nome": "Congelar",    "cor": cfg.GELO,    "letra": "C",
                    "desc": "Inimigos param de se mover e atirar por 5 s"},
    "tiro_rapido": {"nome": "Tiro rápido", "cor": cfg.AMARELO, "letra": "R",
                    "desc": "Atira duas vezes mais rápido por 12 s"},
}


class Poder:
    """Item que cai de um inimigo destruído; a nave pega encostando nele."""

    RAIO = 14

    def __init__(self, x, y, tipo):
        self.tipo = tipo
        self.info = PODERES[tipo]
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(0, 0, self.RAIO * 2, self.RAIO * 2)
        self.rect.center = (int(x), int(y))
        self.tempo = 0

    def atualizar(self):
        self.y += cfg.PODER_VEL_QUEDA
        self.tempo += 1
        self.rect.center = (int(self.x), int(self.y))

    def fora_da_tela(self):
        return self.rect.top > cfg.ALTURA

    def desenhar(self, tela, fonte):
        # "pulsa" para chamar atenção
        raio = self.RAIO + (2 if (self.tempo // 10) % 2 == 0 else 0)
        pygame.draw.circle(tela, self.info["cor"], self.rect.center, raio)
        pygame.draw.circle(tela, cfg.BRANCO, self.rect.center, raio, 2)
        letra = fonte.render(self.info["letra"], True, cfg.PRETO)
        tela.blit(letra, letra.get_rect(center=self.rect.center))


class Explosao:
    """Partículas que se espalham a partir de um ponto e somem."""

    def __init__(self, x, y, cor, quantidade=24):
        self.particulas = []
        for _ in range(quantidade):
            angulo = random.uniform(0, math.pi * 2)
            vel = random.uniform(1.5, 5)
            self.particulas.append({
                "x": float(x), "y": float(y),
                "vx": math.cos(angulo) * vel, "vy": math.sin(angulo) * vel,
                "vida": random.randint(20, 40),
                "cor": random.choice([cor, cfg.AMARELO, cfg.LARANJA, cfg.BRANCO]),
            })

    @property
    def terminou(self):
        return len(self.particulas) == 0

    def atualizar(self):
        vivas = []
        for p in self.particulas:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.96
            p["vy"] *= 0.96
            p["vida"] -= 1
            if p["vida"] > 0:
                vivas.append(p)
        self.particulas = vivas

    def desenhar(self, tela):
        for p in self.particulas:
            raio = max(1, p["vida"] // 8)
            pygame.draw.circle(tela, p["cor"], (int(p["x"]), int(p["y"])), raio)


class Estrela:
    """Uma estrela do fundo que desce lentamente, dando sensação de movimento."""

    def __init__(self):
        self.x = random.randint(0, cfg.LARGURA)
        self.y = random.randint(0, cfg.ALTURA)
        self.vel = random.uniform(0.3, 1.8)
        self.tam = 1 if self.vel < 1.0 else 2

    def atualizar(self):
        self.y += self.vel
        if self.y > cfg.ALTURA:
            self.y = 0
            self.x = random.randint(0, cfg.LARGURA)

    def desenhar(self, tela):
        brilho = int(120 + self.vel * 60)
        pygame.draw.circle(tela, (brilho, brilho, brilho), (int(self.x), int(self.y)), self.tam)
