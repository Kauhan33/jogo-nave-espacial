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

    def __init__(self, x, y, dono, vel_x=0.0):
        self.dono = dono
        self.x = float(x)
        self.y = float(y)
        self.vel_x = vel_x
        if dono == "nave":
            self.vel_y = -cfg.TIRO_VEL_NAVE
            self.cor = cfg.CIANO
        else:
            self.vel_y = cfg.TIRO_VEL_INIMIGO
            self.cor = cfg.LARANJA
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
        pygame.draw.rect(tela, self.cor, self.rect, border_radius=2)
        # miolo branco para dar "brilho" ao tiro
        pygame.draw.rect(tela, cfg.BRANCO, self.rect.inflate(-2, -6), border_radius=2)


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

    @property
    def viva(self):
        return self.vidas > 0

    def mover(self, teclas):
        dx = dy = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= cfg.NAVE_VELOCIDADE
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += cfg.NAVE_VELOCIDADE
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= cfg.NAVE_VELOCIDADE
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += cfg.NAVE_VELOCIDADE
        self.rect.x += dx
        self.rect.y += dy
        # mantém a nave dentro da tela e na metade de baixo
        self.rect.clamp_ip(pygame.Rect(0, cfg.ALTURA // 2, cfg.LARGURA, cfg.ALTURA // 2))

    def atualizar(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invencivel > 0:
            self.invencivel -= 1
        self.chama = (self.chama + 1) % 6

    def atirar(self):
        """Devolve um Tiro novo se o cooldown permitir, senão None."""
        if self.cooldown > 0:
            return None
        self.cooldown = cfg.NAVE_INTERVALO_TIRO
        return Tiro(self.rect.centerx, self.rect.top, "nave")

    def receber_dano(self):
        """Tira uma vida. Devolve True se o dano foi aplicado."""
        if self.invencivel > 0:
            return False
        self.vidas -= 1
        self.invencivel = cfg.NAVE_INVENCIVEL
        return True

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

    def __init__(self, x, y, padrao="vaivem", cor=cfg.VERMELHO, nome="Inimigo"):
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
        self.velocidade = cfg.INIMIGO_VELOCIDADE
        self.tempo = random.uniform(0, math.pi * 2)   # fase da onda
        self.recarga = cfg.INIMIGO_INTERVALO_MIN
        self.piscar = 0                                 # frames de "flash" ao ser atingido

    @property
    def vivo(self):
        return self.vida > 0

    def atualizar(self):
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
        if self.piscar > 0:
            self.piscar -= 1

    def tentar_atirar(self, alvo_rect):
        """Com uma pequena chance por frame, dispara um tiro mirando na nave."""
        if self.recarga > 0 or random.random() > cfg.INIMIGO_CHANCE_TIRO:
            return None
        self.recarga = cfg.INIMIGO_INTERVALO_MIN
        # mira: desloca o tiro no eixo X na direção da nave
        dx = alvo_rect.centerx - self.rect.centerx
        dy = max(1, alvo_rect.centery - self.rect.centery)
        vel_x = (dx / dy) * cfg.TIRO_VEL_INIMIGO
        vel_x = max(-3.0, min(3.0, vel_x))
        return Tiro(self.rect.centerx, self.rect.bottom, "inimigo", vel_x)

    def receber_dano(self):
        """Perde 1 de vida e fica mais rápido. Devolve True se morreu."""
        self.vida -= 1
        self.piscar = 8
        self.velocidade += 0.6
        return self.vida <= 0

    def desenhar(self, tela):
        r = self.rect
        cor = cfg.BRANCO if self.piscar > 0 else self.cor
        corpo = [(r.left, r.top + 6), (r.centerx, r.bottom), (r.right, r.top + 6),
                 (r.centerx + 12, r.top), (r.centerx - 12, r.top)]
        pygame.draw.polygon(tela, cor, corpo)
        pygame.draw.polygon(tela, cfg.BRANCO, corpo, 2)
        pygame.draw.circle(tela, cfg.AMARELO, (r.centerx, r.centery), 5)
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
