"""
Nave Espacial — space shooter em Python/pygame. Ponto de entrada do jogo.

Uso:
    python main.py

Como funciona:
- Você controla a nave azul (embaixo) e precisa destruir as naves inimigas
  (em cima), que se movem e atiram contra você.
- O jogo tem níveis infinitos: o nível 1 tem 2 inimigos e cada nível novo
  adiciona mais um. A cada nível as vidas voltam para pelo menos 3 (vidas
  extras acumuladas são mantidas); o jogo acaba quando as vidas se esgotam.
- A cada 5 níveis aparece um CHEFE, cada vez mais forte.
- Cada inimigo tem 3 pontos de vida, mostrados numa barra em cima dele.
- Metade dos inimigos de cada fase solta um PODER ao morrer (tiro duplo,
  escudo, explosão, vida extra, congelar, tiro rápido). Até o nível 4 cai um
  poder por nível, sem repetir; do 5 em diante caem combinações (duplas,
  depois trios...). Os poderes valem só na fase em que foram pegos.
- Há ESPECIAIS que carregam com o tempo e são usados com as teclas 1/2/3.
- Cada inimigo destruído vale 10 pontos, e cada ponto vira 1 moeda para a
  LOJA (fim de cada nível): upgrades de movimento, cadência e potência do
  tiro (nível máximo 3) e o Ressurgir (continua de onde parou ao morrer).
- Os menus funcionam por teclado e por mouse; a janela pode ser
  redimensionada e o jogo é escalado mantendo a proporção.

O jogo é uma máquina de estados: MENU -> NIVEL -> JOGANDO <-> PAUSA -> FIM,
com a LOJA acessível a partir de MENU (só para ver) e de NIVEL.
"""

from __future__ import annotations

import itertools
import math
import random
import sys

import pygame

import config as cfg
import interface as ui
from entidades import PODERES, Chefe, Estrela, Explosao, Inimigo, Nave, Poder
from sons import carregar_sons

# Estados possíveis do jogo
MENU = "menu"
NIVEL = "nivel"        # tela "NÍVEL N" entre uma fase e outra
JOGANDO = "jogando"
PAUSA = "pausa"
LOJA = "loja"
FIM = "fim"

CORES_INIMIGOS = [cfg.VERMELHO, cfg.ROXO, cfg.LARANJA, cfg.ROSA, cfg.VERDE, cfg.AMARELO]


class Jogo:
    def __init__(self):
        # o mixer é configurado ANTES do pygame.init() para casar com o
        # formato dos sons sintetizados (22050 Hz, 16 bits)
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        # `janela` é o que o usuário vê (redimensionável); `tela` é a superfície
        # fixa de 800x600 onde tudo é desenhado e depois escalada para a janela
        self.janela = pygame.display.set_mode((cfg.LARGURA, cfg.ALTURA), pygame.RESIZABLE)
        self.tela = pygame.Surface((cfg.LARGURA, cfg.ALTURA))
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
        self.estado_antes_pausa = JOGANDO
        self.estado_antes_loja = MENU
        self.rodando = True
        self.frame = 0
        self.opcao_pausa = 0
        self.opcao_loja = 0
        self.recorde = 0
        self.botoes = []                            # botões da tela atual (para o mouse)

        self.nova_partida()
        self.estado = MENU
        self.tocar_musica()

    # ------------------------------------------------------------------
    # Preparação
    # ------------------------------------------------------------------

    def nova_partida(self):
        """Zera pontuação, moedas e upgrades, sorteia os poderes e monta o nível 1."""
        self.nave = Nave()
        self.pontos = 0
        self.moedas = 0
        self.ressurgir = 0
        self.nivel = 0
        # ordem dos poderes dos primeiros níveis (sem repetir)
        self.ordem_poderes = list(PODERES)
        random.shuffle(self.ordem_poderes)
        # combinações já usadas a partir do nível 5 (duplas, trios...)
        self.combos_usados = set()
        self.tamanho_combo = 2
        # especiais: cada um tem uma carga em frames que enche com o tempo
        self.especiais = [{"tipo": tipo, "nome": nome, "carga": 0, "total": seg * cfg.FPS}
                          for tipo, nome, seg in cfg.ESPECIAIS]
        print("[jogo] nova partida")
        self.proximo_nivel()

    def proximo_nivel(self):
        """Avança de nível: mais um inimigo, vidas restauradas, novos poderes."""
        self.nivel += 1
        # vidas voltam a pelo menos 3; vidas extras acumuladas são mantidas
        self.nave.vidas = max(cfg.NAVE_VIDAS, self.nave.vidas)
        self.nave.invencivel = cfg.NAVE_INVENCIVEL // 2
        self.nave.limpar_poderes()          # poderes valem só na fase em que caíram
        self.tiros_nave = []
        self.tiros_inimigos = []
        self.explosoes = []
        self.poderes = []

        self.poderes_nivel = self.sortear_poderes()
        self.tem_chefe = self.nivel % cfg.CHEFE_A_CADA == 0
        self.inimigos = self.criar_inimigos(cfg.INIMIGOS_NIVEL_1 + self.nivel - 1)
        self.marcar_quem_solta_poder()
        # teto de vidas: 5 ou metade dos inimigos na tela, o que for maior
        self.teto_vidas = max(cfg.VIDAS_TETO_MIN, len(self.inimigos) // 2)
        self.estado = NIVEL
        nomes = " + ".join(PODERES[t]["nome"] for t in self.poderes_nivel)
        print(f"[nível {self.nivel}] {len(self.inimigos)} inimigos{' (com CHEFE)' if self.tem_chefe else ''}"
              f" | poderes: {nomes} | vidas: {self.nave.vidas}/{self.teto_vidas} | moedas: {self.moedas}")

    def sortear_poderes(self):
        """Decide quais poderes caem neste nível.

        - Níveis 1 a NIVEIS_SEM_REPETIR: um poder por nível, sem repetir.
        - Depois: combinações de `tamanho_combo` poderes sorteadas sem repetir;
          quando todas as duplas acabam passa para trios, depois quartetos...
          até todos os poderes juntos. Aí volta a sortear qualquer combinação.
        """
        if self.nivel <= cfg.NIVEIS_SEM_REPETIR:
            return [self.ordem_poderes[(self.nivel - 1) % len(self.ordem_poderes)]]

        todos = list(PODERES)
        while True:
            if self.tamanho_combo > len(todos):
                # já saíram todas as combinações possíveis: sorteia qualquer uma
                tamanho = random.randint(2, len(todos))
                return random.sample(todos, tamanho)
            possiveis = [c for c in itertools.combinations(todos, self.tamanho_combo)
                         if c not in self.combos_usados]
            if possiveis:
                combo = random.choice(possiveis)
                self.combos_usados.add(combo)
                return list(combo)
            self.tamanho_combo += 1            # acabaram as duplas -> trios, etc.

    def criar_inimigos(self, quantidade):
        """Distribui os inimigos em linhas no topo da tela.

        Em nível de chefe, o chefe fica no centro e só metade dos inimigos
        normais aparece, como escolta.
        """
        inimigos = []
        if self.tem_chefe:
            tier = self.nivel // cfg.CHEFE_A_CADA
            inimigos.append(Chefe(cfg.LARGURA // 2, 130, tier, self.nivel))
            quantidade = math.ceil(quantidade * cfg.CHEFE_ESCOLTA)
            y_inicial = 250
        else:
            y_inicial = 110

        # linhas mais cheias quando há muitos inimigos, para não descerem demais
        if quantidade <= 8:
            por_linha = 4
        elif quantidade <= 18:
            por_linha = 6
        else:
            por_linha = 8
        for i in range(quantidade):
            linha = i // por_linha
            coluna = i % por_linha
            nesta_linha = min(por_linha, quantidade - linha * por_linha)
            x = cfg.LARGURA * (coluna + 1) / (nesta_linha + 1)
            y = y_inicial + linha * 70
            padrao = "vaivem" if i % 2 == 0 else "onda"
            cor = CORES_INIMIGOS[i % len(CORES_INIMIGOS)]
            inimigos.append(Inimigo(x, y, padrao=padrao, cor=cor, nome=f"Inimigo {i + 1}", nivel=self.nivel))
        return inimigos

    def marcar_quem_solta_poder(self):
        """Sorteia metade dos inimigos comuns para carregar poder (o chefe sempre carrega).

        Decidir isso na montagem da fase (e não na hora da morte) garante que
        exatamente PODER_FRACAO dos inimigos soltam poder, não importa como
        morreram (congelados, pela explosão, pela tempestade...).
        """
        comuns = [ini for ini in self.inimigos if not ini.chefe]
        quantos = max(1, math.ceil(len(comuns) * cfg.PODER_FRACAO))
        for ini in random.sample(comuns, min(quantos, len(comuns))):
            ini.solta_poder = True

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
    # Janela redimensionável: escala e posição da tela 800x600 na janela
    # ------------------------------------------------------------------

    def escala_janela(self):
        """Devolve (escala, deslocamento_x, deslocamento_y) para caber na janela
        mantendo a proporção 4:3 (sobra vira barras pretas)."""
        lj, aj = self.janela.get_size()
        escala = min(lj / cfg.LARGURA, aj / cfg.ALTURA)
        largura = int(cfg.LARGURA * escala)
        altura = int(cfg.ALTURA * escala)
        return escala, (lj - largura) // 2, (aj - altura) // 2

    def pos_mouse(self, pos=None):
        """Converte uma posição na janela para coordenadas da tela 800x600."""
        if pos is None:
            pos = pygame.mouse.get_pos()
        escala, dx, dy = self.escala_janela()
        return ((pos[0] - dx) / escala, (pos[1] - dy) / escala)

    # ------------------------------------------------------------------
    # Eventos (teclado / mouse / janela)
    # ------------------------------------------------------------------

    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            elif evento.type == pygame.VIDEORESIZE:
                self.janela = pygame.display.set_mode(evento.size, pygame.RESIZABLE)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self.clique(self.pos_mouse(evento.pos))
            elif evento.type == pygame.KEYDOWN:
                if self.estado == MENU:
                    self.teclas_menu(evento.key)
                elif self.estado == NIVEL:
                    self.teclas_nivel(evento.key)
                elif self.estado == JOGANDO:
                    self.teclas_jogando(evento.key)
                elif self.estado == PAUSA:
                    self.teclas_pausa(evento.key)
                elif self.estado == LOJA:
                    self.teclas_loja(evento.key)
                elif self.estado == FIM:
                    self.teclas_fim(evento.key)

    def clique(self, pos):
        """Clique do mouse: executa a ação do botão que estiver sob o cursor."""
        for botao in self.botoes:
            if botao.contem(pos):
                self.tocar("menu")
                self.executar_acao(botao.acao)
                return

    def executar_acao(self, acao):
        """Ações dos menus. Teclas e botões do mouse chegam aqui do mesmo jeito."""
        if acao == "jogar":
            self.nova_partida()
        elif acao == "comecar":
            self.estado = JOGANDO
            print(f"[nível {self.nivel}] começou!")
        elif acao == "loja":
            self.abrir_loja()
        elif acao == "voltar":
            self.estado = self.estado_antes_loja
        elif acao == "som":
            self.alternar_som()
        elif acao == "sair":
            self.rodando = False
        elif acao == "continuar":
            self.estado = self.estado_antes_pausa
            print("[jogo] continuando")
        elif acao == "reiniciar":
            self.nova_partida()
        elif acao == "menu":
            self.estado = MENU
            print("[jogo] voltou ao menu inicial")
        elif acao == "ressurgir":
            self.usar_ressurgir()
        elif acao.startswith("comprar:"):
            self.comprar(acao.split(":", 1)[1])

    def teclas_menu(self, tecla):
        if tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.tocar("menu")
            self.executar_acao("jogar")
        elif tecla == pygame.K_l:
            self.executar_acao("loja")
        elif tecla == pygame.K_m:
            self.alternar_som()
        elif tecla in (pygame.K_q, pygame.K_ESCAPE):
            self.rodando = False

    def teclas_nivel(self, tecla):
        # a fase só começa quando o jogador aperta uma tecla (ou clica em COMEÇAR)
        if tecla == pygame.K_ESCAPE:
            self.pausar(vindo_de=NIVEL)
        elif tecla == pygame.K_l:
            self.executar_acao("loja")
        elif tecla == pygame.K_m:
            self.alternar_som()
        else:
            self.tocar("menu")
            self.executar_acao("comecar")

    def teclas_jogando(self, tecla):
        if tecla == pygame.K_ESCAPE:
            self.pausar(vindo_de=JOGANDO)
        elif tecla == pygame.K_m:
            self.alternar_som()
        elif tecla in (pygame.K_1, pygame.K_KP1):
            self.usar_especial(0)
        elif tecla in (pygame.K_2, pygame.K_KP2):
            self.usar_especial(1)
        elif tecla in (pygame.K_3, pygame.K_KP3):
            self.usar_especial(2)
        # o tiro (ESPAÇO) é tratado em `atualizar_jogo` com get_pressed(),
        # para poder segurar a tecla e atirar continuamente

    def pausar(self, vindo_de):
        self.estado_antes_pausa = vindo_de
        self.estado = PAUSA
        self.opcao_pausa = 0
        self.tocar("menu")
        print("[jogo] pausado")

    def teclas_pausa(self, tecla):
        if tecla == pygame.K_UP:
            self.opcao_pausa = (self.opcao_pausa - 1) % len(ui.OPCOES_PAUSA)
            self.tocar("menu")
        elif tecla == pygame.K_DOWN:
            self.opcao_pausa = (self.opcao_pausa + 1) % len(ui.OPCOES_PAUSA)
            self.tocar("menu")
        elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.executar_acao(ui.OPCOES_PAUSA[self.opcao_pausa][1])
        elif tecla == pygame.K_ESCAPE:
            self.executar_acao("continuar")
        elif tecla == pygame.K_r:
            self.executar_acao("reiniciar")
        elif tecla == pygame.K_m:
            self.executar_acao("som")
        elif tecla == pygame.K_q:
            self.executar_acao("sair")

    def teclas_loja(self, tecla):
        if tecla == pygame.K_UP:
            self.opcao_loja = (self.opcao_loja - 1) % len(ui.ITENS_LOJA)
            self.tocar("menu")
        elif tecla == pygame.K_DOWN:
            self.opcao_loja = (self.opcao_loja + 1) % len(ui.ITENS_LOJA)
            self.tocar("menu")
        elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.executar_acao("comprar:" + ui.ITENS_LOJA[self.opcao_loja])
        elif tecla in (pygame.K_ESCAPE, pygame.K_l):
            self.executar_acao("voltar")
        elif tecla == pygame.K_m:
            self.alternar_som()

    def teclas_fim(self, tecla):
        if tecla in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.tocar("menu")
            self.executar_acao("jogar")
        elif tecla == pygame.K_r:
            self.executar_acao("ressurgir")
        elif tecla in (pygame.K_m, pygame.K_ESCAPE):
            self.executar_acao("menu")
        elif tecla == pygame.K_q:
            self.rodando = False

    # ------------------------------------------------------------------
    # Loja e Ressurgir
    # ------------------------------------------------------------------

    def abrir_loja(self):
        """Abre a loja. No menu inicial é só para ver; no fim de nível compra."""
        self.estado_antes_loja = self.estado
        self.estado = LOJA
        self.opcao_loja = 0
        print("[loja] aberta" + (" (só para ver)" if self.estado_antes_loja == MENU else f" com {self.moedas} moedas"))

    def comprar(self, item):
        """Compra o próximo nível de `item`, se puder pagar."""
        if self.estado_antes_loja == MENU:
            self.tocar("erro")
            print("[loja] compras só no fim de cada nível")
            return
        preco = ui.preco_item(self, item)
        nome = cfg.LOJA[item]["nome"]
        if preco is None:
            self.tocar("erro")
            print(f"[loja] {nome} já está no máximo")
            return
        if self.moedas < preco:
            self.tocar("erro")
            print(f"[loja] moedas insuficientes para {nome}: faltam {preco - self.moedas}")
            return
        self.moedas -= preco
        if item == "ressurgir":
            self.ressurgir += 1
        else:
            self.nave.upgrades[item] += 1
        self.tocar("compra")
        print(f"[loja] comprou {nome} (nível {ui.nivel_item(self, item)}) por {preco}; restam {self.moedas} moedas")

    def usar_ressurgir(self):
        """Volta à partida de onde parou, com 3 vidas, gastando o Ressurgir."""
        if self.estado != FIM or self.ressurgir <= 0:
            self.tocar("erro")
            return
        self.ressurgir -= 1
        self.nave.vidas = cfg.NAVE_VIDAS
        self.nave.invencivel = cfg.NAVE_INVENCIVEL * 2
        self.nave.rect.center = (cfg.LARGURA // 2, cfg.ALTURA - 70)
        self.tiros_inimigos.clear()
        self.estado = JOGANDO
        self.tocar("poder")
        print(f"[jogo] RESSURGIU no nível {self.nivel} com {self.nave.vidas} vidas!")

    # ------------------------------------------------------------------
    # Lógica de uma rodada (só roda no estado JOGANDO)
    # ------------------------------------------------------------------

    def atualizar_jogo(self):
        teclas = pygame.key.get_pressed()
        self.nave.mover(teclas)
        self.nave.atualizar()

        # especiais carregam com o tempo; ao completar, cada um toca o seu sino
        for i, especial in enumerate(self.especiais):
            if especial["carga"] < especial["total"]:
                especial["carga"] += 1
                if especial["carga"] == especial["total"]:
                    self.tocar(f"carga{i + 1}")
                    print(f"[especial] {especial['nome']} carregado! (tecla {i + 1})")

        # tiro do jogador (segurar ESPAÇO atira repetidamente)
        if teclas[pygame.K_SPACE]:
            novos = self.nave.atirar()
            if novos:
                self.tiros_nave.extend(novos)
                self.tocar("tiro")

        # inimigos: movem e talvez atirem (o chefe atira uma rajada)
        for inimigo in self.inimigos:
            if not inimigo.vivo:
                continue
            inimigo.atualizar()
            tiro = inimigo.tentar_atirar(self.nave.rect)
            if tiro is not None:
                if isinstance(tiro, list):
                    self.tiros_inimigos.extend(tiro)
                else:
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
            print(f"[nível {self.nivel}] concluído! pontos: {self.pontos} | moedas: {self.moedas}")
            self.tocar("vitoria")
            self.proximo_nivel()

    def verificar_colisoes(self):
        # tiros da nave x inimigos
        for tiro in self.tiros_nave[:]:
            for inimigo in self.inimigos:
                if inimigo.vivo and tiro.rect.colliderect(inimigo.rect):
                    self.tiros_nave.remove(tiro)
                    if inimigo.receber_dano(tiro.dano):
                        self.destruir_inimigo(inimigo)
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

    def destruir_inimigo(self, inimigo):
        """Explosão, pontos/moedas e, se o inimigo carregava, os poderes do nível."""
        self.pontos += inimigo.pontos_morte
        self.moedas += inimigo.pontos_morte * cfg.MOEDAS_POR_PONTO
        tamanho = 90 if inimigo.chefe else 40
        self.explosoes.append(Explosao(inimigo.rect.centerx, inimigo.rect.centery, inimigo.cor, tamanho))
        self.tocar("explosao")
        print(f"[jogo] {inimigo.nome} destruído! +{inimigo.pontos_morte} pontos/moedas")
        if inimigo.solta_poder:
            inimigo.solta_poder = False
            # um item para cada poder do nível, lado a lado
            n = len(self.poderes_nivel)
            for i, tipo in enumerate(self.poderes_nivel):
                x = inimigo.rect.centerx + (i - (n - 1) / 2) * 34
                x = max(Poder.RAIO, min(cfg.LARGURA - Poder.RAIO, x))
                self.poderes.append(Poder(x, inimigo.rect.centery, tipo))
            print("[jogo] caiu: " + " + ".join(PODERES[t]["nome"] for t in self.poderes_nivel))

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
        if tipo == "explosao":
            self.explodir_inimigos()
        elif tipo == "congelar":
            for inimigo in self.inimigos:
                if inimigo.vivo:
                    inimigo.congelado = cfg.CONGELAR_DURACAO
        else:
            if not self.nave.aplicar_poder(tipo, self.teto_vidas):
                print(f"[poder] {PODERES[tipo]['nome']}: vidas já no teto ({self.teto_vidas})")
                return
        print(f"[poder] {PODERES[tipo]['nome']} ativado")

    def explodir_inimigos(self):
        """Destrói até EXPLOSAO_ALVOS inimigos comuns; o chefe é imune."""
        vivos = [ini for ini in self.inimigos if ini.vivo and not ini.chefe]
        alvos = random.sample(vivos, min(cfg.EXPLOSAO_ALVOS, len(vivos)))
        for inimigo in alvos:
            inimigo.vida = 0
            self.destruir_inimigo(inimigo)
        if not alvos:
            print("[jogo] explosão sem alvos (o chefe é imune)")

    def usar_especial(self, indice):
        """Tecla 1/2/3: usa o especial se a carga estiver completa."""
        if indice >= len(self.especiais):
            return
        especial = self.especiais[indice]
        if especial["carga"] < especial["total"]:
            self.tocar("erro")
            print(f"[especial] {especial['nome']} ainda carregando "
                  f"({(especial['total'] - especial['carga']) // cfg.FPS + 1}s)")
            return
        tipo = especial["tipo"]
        if tipo == "vida":
            if not self.nave.aplicar_poder("vida", self.teto_vidas):
                self.tocar("erro")
                print(f"[especial] Vida extra: vidas já no teto ({self.teto_vidas}) - carga mantida")
                return
        elif tipo == "explosao":
            self.explodir_inimigos()
        elif tipo == "tempestade":
            # 1 de dano em TODOS os inimigos vivos, chefe incluso
            for inimigo in self.inimigos:
                if inimigo.vivo:
                    if inimigo.receber_dano(1):
                        self.destruir_inimigo(inimigo)
                    else:
                        self.explosoes.append(Explosao(inimigo.rect.centerx, inimigo.rect.centery, cfg.AMARELO, 10))
            self.tocar("acerto")
        especial["carga"] = 0
        self.tocar("poder")
        print(f"[especial] {especial['nome']} usado! recarregando...")

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
        if self.ressurgir > 0:
            print("[jogo] você tem um Ressurgir: aperte R ou clique em RESSURGIR")

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------

    def desenhar_cenario(self):
        self.tela.fill(cfg.PRETO)
        for estrela in self.estrelas:
            if self.estado not in (PAUSA, LOJA):
                estrela.atualizar()
            estrela.desenhar(self.tela)

    def desenhar_partida(self, piscar):
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
        ui.desenhar_hud(self.tela, self.fontes, self, piscar)

    def desenhar(self):
        self.desenhar_cenario()
        piscar = (self.frame // 30) % 2 == 0   # texto piscando a cada meio segundo
        mouse = self.pos_mouse()
        self.botoes = []

        if self.estado == MENU:
            self.botoes = ui.desenhar_menu_inicial(self.tela, self.fontes, mouse, piscar)
        elif self.estado == NIVEL:
            self.desenhar_partida(piscar)
            self.botoes = ui.desenhar_nivel(self.tela, self.fontes, mouse, self)
        elif self.estado == JOGANDO:
            self.desenhar_partida(piscar)
        elif self.estado == PAUSA:
            self.desenhar_partida(piscar)
            self.botoes = ui.desenhar_pausa(self.tela, self.fontes, mouse, self.opcao_pausa, self.som_ligado)
        elif self.estado == LOJA:
            self.botoes = ui.desenhar_loja(self.tela, self.fontes, mouse, self, self.opcao_loja,
                                           so_ver=(self.estado_antes_loja == MENU))
        elif self.estado == FIM:
            self.desenhar_partida(piscar)
            self.botoes = ui.desenhar_fim(self.tela, self.fontes, mouse, self, piscar)

        # escala a tela 800x600 para a janela, mantendo a proporção
        escala, dx, dy = self.escala_janela()
        if escala == 1.0:
            self.janela.blit(self.tela, (dx, dy))
        else:
            tamanho = (int(cfg.LARGURA * escala), int(cfg.ALTURA * escala))
            self.janela.fill(cfg.PRETO)
            self.janela.blit(pygame.transform.smoothscale(self.tela, tamanho), (dx, dy))
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
    print("Poderes (caem de metade dos inimigos):")
    for info in PODERES.values():
        print(f"  {info['nome']:<18} {info['desc']}")
    print("Especiais (carregam com o tempo):")
    for i, (_, nome, seg) in enumerate(cfg.ESPECIAIS):
        print(f"  [{i + 1}] {nome:<14} a cada {seg}s")
    print("Loja (fim de cada nível):")
    for item in cfg.LOJA.values():
        print(f"  {item['nome']:<24} máx. {item['max']}  preços: {item['precos']}")
    print("=" * 46)


if __name__ == "__main__":
    imprimir_controles()
    Jogo().executar()
    sys.exit(0)
