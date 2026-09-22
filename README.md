# Nave Espacial — Space Shooter em Python

**Repositório:** https://github.com/Kauhan33/jogo-nave-espacial
**Download do jogo (.exe):** https://github.com/Kauhan33/jogo-nave-espacial/releases/latest

Jogo estilo *space shooter* feito em Python com **pygame**. Você controla uma
nave e precisa destruir duas naves inimigas que se movem e atiram contra você.

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

### Executável (Windows)

```bash
pip install pyinstaller
python build_exe.py
```

Gera `dist/NaveEspacial.exe`, um arquivo único que roda sem Python instalado
(ver [build_exe.py](build_exe.py)).

Não precisa de nenhum arquivo de imagem ou som: os gráficos são desenhados com
polígonos do pygame e os efeitos sonoros/música são sintetizados na hora
(ver [sons.py](sons.py)).

## Regras

- A **nave** (azul, embaixo) tem **3 vidas**, mostradas como ícones no HUD.
  Ao ser atingida ela pisca por alguns instantes e fica invencível.
- Os **inimigos** (em cima) têm **3 pontos de vida** cada, mostrados numa
  **barra de vida** acima deles (verde → amarelo → vermelho). A cada acerto
  eles ficam mais rápidos. Metade se move de um lado para o outro
  ("vaivém"), a outra metade faz um movimento de onda. Todos atiram mirando
  na nave. Bater num inimigo também tira uma vida.
- Pontos: 100 por acerto, +500 por inimigo destruído. O recorde da sessão
  aparece na tela de fim.

### Níveis (infinitos)

- O **nível 1 tem 2 inimigos** e **cada nível novo adiciona mais um**
  (nível N = N + 1 inimigos), um pouco mais rápidos e atirando mais.
- Ao destruir todos os inimigos aparece a tela "NÍVEL N" e as **3 vidas
  são restauradas**.
- O jogo só termina quando as 3 vidas acabam — o objetivo é chegar o mais
  longe possível.

### Poderes

Quando um inimigo é destruído pode cair um poder (o primeiro do nível
sempre cai; os demais têm 40% de chance). Pegue encostando a nave nele.

| Poder        | Efeito                                              |
|--------------|-----------------------------------------------------|
| Tiro duplo   | Atira dois tiros de uma vez por 12 s                |
| Explosão     | Destrói até 3 inimigos aleatórios na hora           |
| Escudo       | Absorve o próximo tiro inimigo (círculo na nave)    |
| Vida extra   | +1 vida (máximo 5)                                  |
| Congelar     | Inimigos param de se mover e atirar por 5 s         |
| Tiro rápido  | Intervalo entre tiros cai pela metade por 12 s      |

Cada nível tem **um** poder, mostrado na tela "NÍVEL N" e no rodapé do HUD.
Do nível 1 ao 4 os poderes **não se repetem** (ordem sorteada a cada
partida); a partir do nível 5 qualquer um pode ser sorteado de novo.
Os poderes ativos e o tempo restante aparecem no canto inferior esquerdo.

## Controles

| Tecla              | Função                          |
|--------------------|---------------------------------|
| Setas / W A S D    | Mover a nave                    |
| Espaço             | Atirar (pode segurar)           |
| ESC                | Pausar / abrir o menu de pausa  |
| Enter              | Confirmar / começar             |
| Setas Cima/Baixo   | Navegar no menu de pausa        |
| R                  | Reiniciar (na pausa ou no fim)  |
| M                  | Ligar / desligar o som          |
| Q                  | Sair do jogo                    |

Essa mesma tabela aparece **dentro do jogo**, na tela inicial e no menu de
pausa, e é impressa no terminal quando o jogo abre.

## Estrutura do código

| Arquivo                        | O que faz                                                          |
|--------------------------------|--------------------------------------------------------------------|
| [main.py](main.py)             | Laço principal (`while`), máquina de estados MENU/NIVEL/JOGANDO/PAUSA/FIM, níveis, poderes, colisões |
| [entidades.py](entidades.py)   | Classes `Nave`, `Inimigo` (com barra de vida), `Tiro`, `Poder` (catálogo `PODERES`), `Explosao`, `Estrela` |
| [interface.py](interface.py)   | HUD, tela inicial, tela de nível, menu de pausa, tela de fim e a lista de controles |
| [sons.py](sons.py)             | Síntese dos efeitos sonoros e da música de fundo                   |
| [config.py](config.py)         | Constantes: tamanho da tela, cores, velocidades, vidas, pontos     |

## Conceitos de Python usados

- **`while`** — o laço principal do jogo em `Jogo.executar()` roda enquanto
  `self.rodando` for verdadeiro (um frame por volta, 60 por segundo).
- **`for`** — percorre inimigos, tiros, explosões, estrelas e a lista de
  controles (ex.: `for inimigo in self.inimigos:` em `atualizar_jogo`).
- **`if` / `elif` / `else`** — decide o estado atual, qual tecla foi
  apertada, se houve colisão, qual cor a barra de vida deve ter, etc.
- **`print`** — registra no terminal os acontecimentos da partida (início,
  pausa, acertos, vidas perdidas, vitória/derrota) e imprime os controles.
- Também: classes, listas, dicionários (sons), funções com valor de retorno,
  `@property`, operadores `%` e `//`, `random` e `math`.
