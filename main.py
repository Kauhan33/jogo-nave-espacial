"""
Nave Espacial — space shooter em Python/pygame. Ponto de entrada do jogo.

Uso:
    python main.py

Como funciona:
- Você controla a nave azul (embaixo) e precisa destruir as duas naves
  inimigas (em cima), que se movem e atiram contra você.
- A nave tem 3 vidas; cada inimigo também tem 3 pontos de vida, mostrados
  numa barra em cima dele.
- ESC abre o menu de pausa. Os controles completos aparecem na tela inicial
  e no menu de pausa (e também são impressos no terminal ao iniciar).

O jogo é uma máquina de estados simples: MENU -> JOGANDO <-> PAUSA -> FIM.
"""

from __future__ import annotations

import sys

import pygame

import config as cfg
import interface as ui
from entidades import Estrela, Explosao, Inimigo, Nave
from sons import carregar_sons

# Estados possíveis do jogo
MENU = "menu"
JOGANDO = "jogando"
PAUSA = "pausa"
FIM = "fim"


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
        self.venceu = False

        self.nova_partida()
        self.tocar_musica()

    # ------------------------------------------------------------------
    # Preparação
    # ------------------------------------------------------------------

    def nova_partida(self):
        """Recria nave, inimigos e listas de tiros para começar do zero."""
        self.nave = Nave()
        self.inimigos = [
            Inimigo(cfg.LARGURA * 0.3, 110, padrao="vaivem", cor=cfg.VERMELHO, nome="Inimigo 1"),
            Inimigo(cfg.LARGURA * 0.7, 150, padrao="onda", cor=cfg.ROXO, nome="Inimigo 2"),
        ]
        self.tiros_nave = []
        self.tiros_inimigos = []
        self.explosoes = []
        self.pontos = 0
        self.venceu = False
        print("[jogo] nova partida: nave com", self.nave.vidas, "vidas e", len(self.inimigos), "inimigos")

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
            self.estado = JOGANDO
            print("[jogo] começou! Boa sorte.")
        elif tecla == pygame.K_m:
            self.alternar_som()
        elif tecla in (pygame.K_q, pygame.K_ESCAPE):
            self.rodando = False

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
            self.estado = JOGANDO
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
            self.estado = JOGANDO
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
            tiro = self.nave.atirar()
            if tiro is not None:
                self.tiros_nave.append(tiro)
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

        self.verificar_colisoes()

        for explosao in self.explosoes:
            explosao.atualizar()
        self.explosoes = [e for e in self.explosoes if not e.terminou]

        # condições de fim
        if not self.nave.viva:
            self.terminar(venceu=False)
        elif all(not inimigo.vivo for inimigo in self.inimigos):
            self.terminar(venceu=True)

    def verificar_colisoes(self):
        # tiros da nave x inimigos
        for tiro in self.tiros_nave[:]:
            for inimigo in self.inimigos:
                if inimigo.vivo and tiro.rect.colliderect(inimigo.rect):
                    self.tiros_nave.remove(tiro)
                    morreu = inimigo.receber_dano()
                    self.pontos += cfg.PONTOS_ACERTO
                    if morreu:
                        self.pontos += cfg.PONTOS_DESTRUIR
                        self.explosoes.append(Explosao(inimigo.rect.centerx, inimigo.rect.centery, inimigo.cor, 40))
                        self.tocar("explosao")
                        print(f"[jogo] {inimigo.nome} destruído! +{cfg.PONTOS_DESTRUIR} pontos")
                    else:
                        self.explosoes.append(Explosao(tiro.rect.centerx, tiro.rect.centery, inimigo.cor, 8))
                        self.tocar("acerto")
                        print(f"[jogo] {inimigo.nome} atingido: vida {inimigo.vida}/{inimigo.vida_max}")
                    break

        # tiros dos inimigos x nave
        for tiro in self.tiros_inimigos[:]:
            if tiro.rect.colliderect(self.nave.rect):
                self.tiros_inimigos.remove(tiro)
                if self.nave.receber_dano():
                    self.explosoes.append(Explosao(self.nave.rect.centerx, self.nave.rect.centery, cfg.AZUL, 20))
                    self.tocar("dano")
                    print(f"[jogo] nave atingida! vidas restantes: {self.nave.vidas}")

        # nave x inimigo (trombada) também tira vida
        for inimigo in self.inimigos:
            if inimigo.vivo and inimigo.rect.colliderect(self.nave.rect):
                if self.nave.receber_dano():
                    self.explosoes.append(Explosao(self.nave.rect.centerx, self.nave.rect.top, cfg.AZUL, 20))
                    self.tocar("dano")
                    print(f"[jogo] colisão com {inimigo.nome}! vidas restantes: {self.nave.vidas}")

    def terminar(self, venceu):
        self.venceu = venceu
        self.estado = FIM
        self.tiros_inimigos.clear()
        if venceu:
            self.tocar("vitoria")
            print(f"[jogo] VITÓRIA! Pontuação final: {self.pontos}")
        else:
            self.explosoes.append(Explosao(self.nave.rect.centerx, self.nave.rect.centery, cfg.AZUL, 50))
            self.tocar("derrota")
            print(f"[jogo] GAME OVER. Pontuação final: {self.pontos}")

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
        if self.nave.viva:
            self.nave.desenhar(self.tela)
        for explosao in self.explosoes:
            explosao.desenhar(self.tela)
        ui.desenhar_hud(self.tela, self.fontes, self.nave, self.inimigos, self.pontos, self.som_ligado)

    def desenhar(self):
        self.desenhar_cenario()
        piscar = (self.frame // 30) % 2 == 0   # texto piscando a cada meio segundo

        if self.estado == MENU:
            ui.desenhar_menu_inicial(self.tela, self.fontes, piscar)
        elif self.estado == JOGANDO:
            self.desenhar_partida()
        elif self.estado == PAUSA:
            self.desenhar_partida()
            ui.desenhar_pausa(self.tela, self.fontes, self.opcao_pausa, self.som_ligado)
        elif self.estado == FIM:
            self.desenhar_partida()
            ui.desenhar_fim(self.tela, self.fontes, self.venceu, self.pontos, piscar)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Laço principal
    # ------------------------------------------------------------------

    def executar(self):
        while self.rodando:
            self.processar_eventos()
            if self.estado == JOGANDO:
                self.atualizar_jogo()
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
    print("=" * 46)


if __name__ == "__main__":
    imprimir_controles()
    Jogo().executar()
    sys.exit(0)
