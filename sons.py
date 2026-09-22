"""
Geração dos efeitos sonoros e da música de fundo.

O jogo não depende de arquivos .wav/.mp3 externos: cada som é sintetizado na
hora (ondas quadradas, senoidais, ruído...) e virado num `pygame.mixer.Sound`.
Assim o projeto roda em qualquer máquina só com o pygame instalado.
"""

from __future__ import annotations

import math
import random
from array import array

import pygame

TAXA = 22050  # amostras por segundo


def _onda(freq_inicio, freq_fim, duracao, tipo="quadrada", volume=0.5):
    """Gera uma lista de amostras (16 bits) de uma onda simples.

    A frequência desliza de `freq_inicio` até `freq_fim` ao longo da duração
    (isso dá o efeito "piu" de tiro de videogame) e o volume decai até zero.
    """
    total = int(TAXA * duracao)
    amostras = array("h")
    fase = 0.0
    for i in range(total):
        t = i / total                                   # 0.0 -> 1.0
        freq = freq_inicio + (freq_fim - freq_inicio) * t
        fase += 2 * math.pi * freq / TAXA
        if tipo == "quadrada":
            valor = 1.0 if math.sin(fase) > 0 else -1.0
        elif tipo == "seno":
            valor = math.sin(fase)
        elif tipo == "triangulo":
            valor = 2 * abs(2 * ((fase / (2 * math.pi)) % 1) - 1) - 1
        else:  # "ruido"
            valor = random.uniform(-1, 1)
        envelope = 1.0 - t                              # decaimento linear
        amostras.append(int(valor * envelope * volume * 32767))
    return amostras


def _nota(freq, duracao, volume=0.18):
    """Uma nota musical curta de onda triangular com ataque/decaimento suaves."""
    total = int(TAXA * duracao)
    amostras = array("h")
    fase = 0.0
    for i in range(total):
        t = i / total
        fase += 2 * math.pi * freq / TAXA
        valor = 2 * abs(2 * ((fase / (2 * math.pi)) % 1) - 1) - 1
        if t < 0.05:
            envelope = t / 0.05             # ataque
        else:
            envelope = 1.0 - (t - 0.05)     # decaimento
        amostras.append(int(valor * envelope * volume * 32767))
    return amostras


def _musica_fundo():
    """Um loop de ~8 s: baixo pulsante + arpejo, em Lá menor."""
    # frequências (Hz): A2, C3, E3, G3 ... e as oitavas acima para o arpejo
    baixo = [110.0, 110.0, 130.81, 130.81, 164.81, 164.81, 98.0, 98.0]
    arpejo = [220.0, 261.63, 329.63, 261.63, 220.0, 261.63, 329.63, 392.0]
    faixa = array("h")
    for compasso in range(2):
        for i in range(8):
            trecho_baixo = _nota(baixo[i], 0.5, volume=0.16)
            trecho_arpejo = _nota(arpejo[i] * (2 if compasso == 1 else 1), 0.25, volume=0.10)
            trecho_arpejo2 = _nota(arpejo[(i + 2) % 8], 0.25, volume=0.10)
            melodia = trecho_arpejo + trecho_arpejo2
            # mistura baixo + melodia amostra por amostra
            for j in range(len(trecho_baixo)):
                soma = trecho_baixo[j] + (melodia[j] if j < len(melodia) else 0)
                faixa.append(max(-32767, min(32767, soma)))
    return faixa


def _para_som(amostras):
    """Converte o array de amostras mono num Sound, respeitando o formato do mixer."""
    _, _, canais = pygame.mixer.get_init()
    if canais == 2:
        estereo = array("h")
        for a in amostras:
            estereo.append(a)
            estereo.append(a)
        amostras = estereo
    return pygame.mixer.Sound(buffer=amostras.tobytes())


def carregar_sons():
    """Cria e devolve um dicionário nome -> pygame.mixer.Sound."""
    print("[sons] sintetizando efeitos sonoros...")
    sons = {
        "tiro": _para_som(_onda(880, 220, 0.12, "quadrada", 0.25)),
        "tiro_inimigo": _para_som(_onda(300, 120, 0.18, "triangulo", 0.25)),
        "acerto": _para_som(_onda(500, 900, 0.10, "seno", 0.35)),
        "explosao": _para_som(_onda(200, 40, 0.55, "ruido", 0.45)),
        "dano": _para_som(_onda(180, 60, 0.35, "quadrada", 0.35)),
        "menu": _para_som(_onda(660, 990, 0.08, "seno", 0.25)),
        "vitoria": _para_som(_onda(440, 1320, 0.8, "triangulo", 0.35)),
        "poder": _para_som(_nota(523.25, 0.12, 0.3) + _nota(659.25, 0.12, 0.3) + _nota(783.99, 0.2, 0.3)),
        # cada especial tem um "sino" diferente quando termina de carregar
        "carga1": _para_som(_nota(659.25, 0.15, 0.3) + _nota(880.0, 0.3, 0.3)),
        "carga2": _para_som(_nota(587.33, 0.12, 0.3) + _nota(783.99, 0.12, 0.3) + _nota(1174.66, 0.35, 0.3)),
        "carga3": _para_som(_nota(523.25, 0.1, 0.3) + _nota(659.25, 0.1, 0.3) + _nota(783.99, 0.1, 0.3)
                            + _nota(1046.5, 0.4, 0.35)),
        "compra": _para_som(_nota(1046.5, 0.08, 0.3) + _nota(1318.5, 0.15, 0.3)),
        "erro": _para_som(_onda(220, 110, 0.25, "quadrada", 0.25)),
        "derrota": _para_som(_onda(330, 55, 1.2, "quadrada", 0.3)),
        "musica": _para_som(_musica_fundo()),
    }
    print(f"[sons] {len(sons)} sons prontos")
    return sons
