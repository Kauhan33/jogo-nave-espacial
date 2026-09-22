"""
Nave Espacial — space shooter em Python/pygame. Ponto de entrada do jogo.

Uso:
    python main.py

Como funciona:
- Você controla a nave azul (embaixo) e precisa destruir as naves inimigas
  (em cima), que se movem e atiram contra você.
- O jogo tem níveis infinitos: o nível 1 tem 2 inimigos e cada nível novo
  adiciona mais um. A cada nível as 3 vidas da nave são restauradas; o jogo
  acaba quando as 3 vidas se esgotam.
- Cada inimigo tem 3 pontos de vida, mostrados numa barra em cima dele.
- Quando um inimigo é destruído pode cair um PODER (tiro duplo, escudo,
  explosão, vida extra, congelar, tiro rápido). Cada nível tem um poder;
  até o nível 4 eles não se repetem, do 5 em diante é sorteado.
- ESC abre o menu de pausa. Os controles completos aparecem na tela inicial
  e no menu de pausa (e também são impressos no terminal ao iniciar).

O jogo é uma máquina de estados: MENU -> NIVEL -> JOGANDO <-> PAUSA -> FIM.
"""

from __future__ import annotations

import random
import sys

import pygame

import config as cfg
import interface as ui
from entidades import PODERES, Estrela, Explosao, Inimigo, Nave, Poder
from sons import carregar_sons

# Estados possíveis do jogo
MENU = "menu"
NIVEL = "nivel"        # tela "NÍVEL N" entre uma fase e outra
JOGANDO = "jogando"
PAUSA = "pausa"
FIM = "fim"

CORES_INIMIGOS = [cfg.VERMELHO, cfg.ROXO, cfg.LARANJA, cfg.ROSA, cfg.VERDE, cfg.AMARELO]


class Jogo:
    def __init__(self):
        # o mixer é configurado ANTES do pygame.init() para casar com o
        # formato dos sons sintetizados (22050 Hz, 16 bits)
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.tela = pygame.display.set_mode((cfg.LARGURA, cfg.ALTURA))
        pygame.display.set_caption(cfg.TITULO)
        self.relogio = pygame.time.Clock()
        self.fontes = ui.Fontes()

        self.sons = carregar_sons()
        self.som_ligado = True
        pygame.mixer.set_reserved(1)               # canal 0 fica só para a música
        self.canal_musica = pygame.mixer.Channel(0)
        self.sons["musica"].set_volume(0.5)

        self.estrelas = [Estrela() for _ in range(cfg.QTD_ESTRELAS)]
        self.estado = MENU
        self.rodando = True
        self.frame = 0
        self.opcao_pausa = 0
        self.recorde = 0

        self.nova_partida()
        self.estado = MENU
        self.tocar_musica()

    # ------------------------------------------------------------------
    # Preparação
    # ------------------------------------------------------------------

    def nova_partida(self):
        """Zera pontuação, sorteia a ordem dos poderes e monta o nível 1."""
        self.nave = Nave()
        self.pontos = 0
        self.nivel = 0
        # ordem dos poderes dos primeiros níveis (sem repetir)
        self.ordem_poderes = list(PODERES)
        random.shuffle(self.ordem_poderes)
        print("[jogo] nova partida")
        self.proximo_nivel()

    def proximo_nivel(self):
        """Avança de nível: mais um inimigo, vidas restauradas, novo poder."""
        self.nivel += 1
        self.nave.vidas = cfg.NAVE_VIDAS
        self.nave.invencivel = cfg.NAVE_INVENCIVEL // 2
        self.tiros_nave = []
        self.tiros_inimigos = []
        self.explosoes = []
        self.poderes = []
        self.primeira_morte = True          # o 1º inimigo do nível sempre solta poder

        # até NIVEIS_SEM_REPETIR o poder é diferente a cada nível; depois sorteia
        if self.nivel <= cfg.NIVEIS_SEM_REPETIR:
            self.poder_nivel = self.ordem_poderes[(self.nivel - 1) % len(self.ordem_poderes)]
        else:
            self.poder_nivel = random.choice(self.ordem_poderes)

        self.inimigos = self.criar_inimigos(cfg.INIMIGOS_NIVEL_1 + self.nivel - 1)
        self.timer_nivel = cfg.NIVEL_TELA_FRAMES
        self.estado = NIVEL
        print(f"[nível {self.nivel}] {len(self.inimigos)} inimigos | poder: {PODERES[self.poder_nivel]['nome']}"
              f" | vidas: {self.nave.vidas}")

    def criar_inimigos(self, quantidade):
        """Distribui `quantidade` inimigos em linhas de até 4 no topo da tela."""
        inimigos = []
        por_linha = 4
        for i in range(quantidade):
            linha = i // por_linha
            coluna = i % por_linha
            nesta_linha = min(por_linha, quantidade - linha * por_linha)
            x = cfg.LARGURA * (coluna + 1) / (nesta_linha + 1)
            y = 110 + linha * 70
            padrao = "vaivem" if i % 2 == 0 else "onda"
            cor = CORES_INIMIGOS[i % len(CORES_INIMIGOS)]
            inimigos.append(Inimigo(x, y, padrao=padrao, cor=cor, nome=f"Inimigo {i + 1}", nivel=self.nivel))
        return inimigos

    # ------------------------------------------------------------------
    # Som
    # ------------------------------------------------------------------

    def tocar(self, nome):
        if self.som_ligado:
            self.sons[nome].play()

    def tocar_musica(self):
        if self.som_ligado and not self.canal_musica.get_busy():
            self.canal_musica.play(self.sons["musica"], loops=-1)

    def alternar_som(self):
        self.som_ligado = not self.som_ligado
        if self.som_ligado:
            self.tocar_musica()
            self.tocar("menu")
        else:
            self.canal_musica.stop()
        print("[som]", "ligado" if self.som_ligado else "desligado")

    # ------------------------------------------------------------------
    # Eventos (teclado / fechar janela)
    # ------------------------------------------------------------------

    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            elif evento.type == pygame.KEYDOWN:
                if self.estado == MENU:
                    self.teclas_menu(evento.key)
                elif self.estado == NIVEL:
                    self.teclas_nivel(evento.key)
                elif self.estado == JOGANDO:
                    self.teclas_jogando(evento.key)
                elif self.estado == PAUSA:
                    self.teclas_pausa(evento.key)
                elif self.estado == FIM:
                    self.teclas_fim(evento.key)

    def teclas_menu(self, tecla):
        if tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.tocar("menu")
            self.nova_partida()
        elif tecla == pygame.K_m:
            self.alternar_som()
        elif tecla in (pygame.K_q, pygame.K_ESCAPE):
            self.rodando = False

    def teclas_nivel(self, tecla):
        if tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.timer_nivel = 0            # pula a espera
        elif tecla == pygame.K_ESCAPE:
            self.estado = PAUSA
            self.opcao_pausa = 0
        elif tecla == pygame.K_m:
            self.alternar_som()

    def teclas_jogando(self, tecla):
        if tecla == pygame.K_ESCAPE:
            self.estado = PAUSA
            self.opcao_pausa = 0
            self.tocar("menu")
            print("[jogo] pausado")
        elif tecla == pygame.K_m:
            self.alternar_som()
        # o tiro (ESPAÇO) é tratado em `atualizar_jogo` com get_pressed(),
        # para poder segurar a tecla e atirar continuamente

    def teclas_pausa(self, tecla):
        if tecla == pygame.K_UP:
            self.opcao_pausa = (self.opcao_pausa - 1) % len(ui.OPCOES_PAUSA)
            self.tocar("menu")
        elif tecla == pygame.K_DOWN:
            self.opcao_pausa = (self.opcao_pausa + 1) % len(ui.OPCOES_PAUSA)
            self.tocar("menu")
        elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.executar_opcao_pausa(ui.OPCOES_PAUSA[self.opcao_pausa][1])
        elif tecla == pygame.K_ESCAPE:
            self.executar_opcao_pausa("continuar")
        elif tecla == pygame.K_r:
            self.executar_opcao_pausa("reiniciar")
        elif tecla == pygame.K_m:
            self.executar_opcao_pausa("som")
        elif tecla == pygame.K_q:
            self.executar_opcao_pausa("sair")

    def executar_opcao_pausa(self, acao):
        if acao == "continuar":
            self.estado = JOGANDO
            print("[jogo] continuando")
        elif acao == "reiniciar":
            self.nova_partida()
        elif acao == "som":
            self.alternar_som()
        elif acao == "menu":
            self.estado = MENU
            print("[jogo] voltou ao menu inicial")
        elif acao == "sair":
            self.rodando = False

    def teclas_fim(self, tecla):
        if tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_r):
            self.tocar("menu")
            self.nova_partida()
        elif tecla == pygame.K_m:
            self.estado = MENU
        elif tecla in (pygame.K_q, pygame.K_ESCAPE):
            self.rodando = False

    # ------------------------------------------------------------------
    # Lógica de uma rodada (só roda no estado JOGANDO)
    # ------------------------------------------------------------------

    def atualizar_jogo(self):
        teclas = pygame.key.get_pressed()
        self.nave.mover(teclas)
        self.nave.atualizar()

        # tiro do jogador (segurar ESPAÇO atira repetidamente)
        if teclas[pygame.K_SPACE]:
            novos = self.nave.atirar()
            if novos:
                self.tiros_nave.extend(novos)
                self.tocar("tiro")

        # inimigos: movem e talvez atirem
        for inimigo in self.inimigos:
            if not inimigo.vivo:
                continue
            inimigo.atualizar()
            tiro = inimigo.tentar_atirar(self.nave.rect)
            if tiro is not None:
                self.tiros_inimigos.append(tiro)
                self.tocar("tiro_inimigo")

        # move os tiros e descarta os que saíram da tela
        for lista in (self.tiros_nave, self.tiros_inimigos):
            for tiro in lista:
                tiro.atualizar()
            lista[:] = [t for t in lista if not t.fora_da_tela()]

        # poderes caindo
        for poder in self.poderes:
            poder.atualizar()
        self.poderes = [p for p in self.poderes if not p.fora_da_tela()]

        self.verificar_colisoes()

        for explosao in self.explosoes:
            explosao.atualizar()
        self.explosoes = [e for e in self.explosoes if not e.terminou]

        # condições de fim de nível / de jogo
        if not self.nave.viva:
            self.terminar()
        elif all(not inimigo.vivo for inimigo in self.inimigos):
            print(f"[nível {self.nivel}] concluído! pontos: {self.pontos}")
            self.tocar("vitoria")
            self.proximo_nivel()

    def verificar_colisoes(self):
        # tiros da nave x inimigos
        for tiro in self.tiros_nave[:]:
            for inimigo in self.inimigos:
                if inimigo.vivo and tiro.rect.colliderect(inimigo.rect):
                    self.tiros_nave.remove(tiro)
                    morreu = inimigo.receber_dano()
                    self.pontos += cfg.PONTOS_ACERTO
                    if morreu:
                        self.destruir_inimigo(inimigo, solta_poder=True)
                    else:
                        self.explosoes.append(Explosao(tiro.rect.centerx, tiro.rect.centery, inimigo.cor, 8))
                        self.tocar("acerto")
                        print(f"[jogo] {inimigo.nome} atingido: vida {inimigo.vida}/{inimigo.vida_max}")
                    break

        # tiros dos inimigos x nave
        for tiro in self.tiros_inimigos[:]:
            if tiro.rect.colliderect(self.nave.rect):
                self.tiros_inimigos.remove(tiro)
                self.nave_atingida("tiro inimigo")

        # nave x inimigo (trombada) também tira vida
        for inimigo in self.inimigos:
            if inimigo.vivo and inimigo.rect.colliderect(self.nave.rect):
                self.nave_atingida(f"colisão com {inimigo.nome}")

        # nave x poder caindo
        for poder in self.poderes[:]:
            if poder.rect.colliderect(self.nave.rect):
                self.poderes.remove(poder)
                self.pegar_poder(poder.tipo)

    def destruir_inimigo(self, inimigo, solta_poder):
        """Explosão, pontos e (talvez) um poder caindo do lugar do inimigo."""
        self.pontos += cfg.PONTOS_DESTRUIR
        self.explosoes.append(Explosao(inimigo.rect.centerx, inimigo.rect.centery, inimigo.cor, 40))
        self.tocar("explosao")
        print(f"[jogo] {inimigo.nome} destruído! +{cfg.PONTOS_DESTRUIR} pontos")
        # o primeiro inimigo do nível sempre solta o poder; os outros têm uma chance
        if solta_poder and (self.primeira_morte or random.random() < cfg.PODER_CHANCE):
            self.primeira_morte = False
            self.poderes.append(Poder(inimigo.rect.centerx, inimigo.rect.centery, self.poder_nivel))
            print(f"[jogo] caiu um poder: {PODERES[self.poder_nivel]['nome']}")

    def nave_atingida(self, causa):
        resultado = self.nave.receber_dano()
        if resultado == "nada":
            return
        self.explosoes.append(Explosao(self.nave.rect.centerx, self.nave.rect.centery, cfg.AZUL, 20))
        self.tocar("dano")
        if resultado == "escudo":
            print(f"[jogo] {causa}: o escudo absorveu o dano!")
        else:
            print(f"[jogo] {causa}! vidas restantes: {self.nave.vidas}")

    def pegar_poder(self, tipo):
        """Aplica o poder pego. Os que mexem nos inimigos são tratados aqui."""
        self.tocar("poder")
        print(f"[poder] {PODERES[tipo]['nome']} ativado")
        if tipo == "explosao":
            vivos = [ini for ini in self.inimigos if ini.vivo]
            alvos = random.sample(vivos, min(cfg.EXPLOSAO_ALVOS, len(vivos)))
            for inimigo in alvos:
                inimigo.vida = 0
                self.destruir_inimigo(inimigo, solta_poder=False)
        elif tipo == "congelar":
            for inimigo in self.inimigos:
                if inimigo.vivo:
                    inimigo.congelado = cfg.CONGELAR_DURACAO
        else:
            self.nave.aplicar_poder(tipo)

    def terminar(self):
        self.estado = FIM
        self.tiros_inimigos.clear()
        self.explosoes.append(Explosao(self.nave.rect.centerx, self.nave.rect.centery, cfg.AZUL, 50))
        self.tocar("derrota")
        if self.pontos > self.recorde:
            self.recorde = self.pontos
            print(f"[jogo] GAME OVER no nível {self.nivel}. NOVO RECORDE: {self.pontos}")
        else:
            print(f"[jogo] GAME OVER no nível {self.nivel}. Pontuação: {self.pontos} (recorde: {self.recorde})")

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------

    def desenhar_cenario(self):
        self.tela.fill(cfg.PRETO)
        for estrela in self.estrelas:
            if self.estado != PAUSA:
                estrela.atualizar()
            estrela.desenhar(self.tela)

    def desenhar_partida(self):
        for inimigo in self.inimigos:
            if inimigo.vivo:
                inimigo.desenhar(self.tela)
        for tiro in self.tiros_nave + self.tiros_inimigos:
            tiro.desenhar(self.tela)
        for poder in self.poderes:
            poder.desenhar(self.tela, self.fontes.pequena)
        if self.nave.viva:
            self.nave.desenhar(self.tela)
        for explosao in self.explosoes:
            explosao.desenhar(self.tela)
        ui.desenhar_hud(self.tela, self.fontes, self.nave, self.inimigos, self.pontos,
                        self.som_ligado, self.nivel, self.poder_nivel)

    def desenhar(self):
        self.desenhar_cenario()
        piscar = (self.frame // 30) % 2 == 0   # texto piscando a cada meio segundo

        if self.estado == MENU:
            ui.desenhar_menu_inicial(self.tela, self.fontes, piscar)
        elif self.estado == NIVEL:
            self.desenhar_partida()
            ui.desenhar_nivel(self.tela, self.fontes, self.nivel, len(self.inimigos), self.poder_nivel)
        elif self.estado == JOGANDO:
            self.desenhar_partida()
        elif self.estado == PAUSA:
            self.desenhar_partida()
            ui.desenhar_pausa(self.tela, self.fontes, self.opcao_pausa, self.som_ligado)
        elif self.estado == FIM:
            self.desenhar_partida()
            ui.desenhar_fim(self.tela, self.fontes, self.nivel, self.pontos, self.recorde, piscar)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Laço principal
    # ------------------------------------------------------------------

    def executar(self):
        while self.rodando:
            self.processar_eventos()
            if self.estado == JOGANDO:
                self.atualizar_jogo()
            elif self.estado == NIVEL:
                self.timer_nivel -= 1
                if self.timer_nivel <= 0:
                    self.estado = JOGANDO
            elif self.estado == FIM:
                # deixa as explosões terminarem de animar na tela de fim
                for explosao in self.explosoes:
                    explosao.atualizar()
            self.desenhar()
            self.frame += 1
            self.relogio.tick(cfg.FPS)

        print("[jogo] até a próxima!")
        pygame.quit()


def imprimir_controles():
    print("=" * 46)
    print(f"  {cfg.TITULO}")
    print("=" * 46)
    print("Controles:")
    for tecla, funcao in ui.CONTROLES:
        print(f"  {tecla:<18} {funcao}")
    print("Poderes:")
    for info in PODERES.values():
        print(f"  {info['nome']:<18} {info['desc']}")
    print("=" * 46)


if __name__ == "__main__":
    imprimir_controles()
    Jogo().executar()
    sys.exit(0)
