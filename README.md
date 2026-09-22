# Nave Espacial — Space Shooter em Python

Jogo estilo *space shooter* feito em Python com **pygame**. Você controla uma
nave e precisa destruir duas naves inimigas que se movem e atiram contra você.

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

Não precisa de nenhum arquivo de imagem ou som: os gráficos são desenhados com
polígonos do pygame e os efeitos sonoros/música são sintetizados na hora
(ver [sons.py](sons.py)).

## Regras

- A **nave** (azul, embaixo) tem **3 vidas**, mostradas como ícones no HUD.
  Ao ser atingida ela pisca por alguns instantes e fica invencível.
- Os **2 inimigos** (em cima) têm **3 pontos de vida** cada, mostrados numa
  **barra de vida** acima deles (verde → amarelo → vermelho). A cada acerto
  eles ficam mais rápidos.
- Um inimigo se move de um lado para o outro ("vaivém"); o outro faz um
  movimento de onda. Os dois atiram mirando na nave.
- Bater num inimigo também tira uma vida.
- **Vitória:** destruir os dois inimigos. **Derrota:** perder as 3 vidas.
- Pontos: 100 por acerto, +500 por inimigo destruído.

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
| [main.py](main.py)             | Laço principal (`while`), máquina de estados MENU/JOGANDO/PAUSA/FIM, eventos de teclado, colisões |
| [entidades.py](entidades.py)   | Classes `Nave`, `Inimigo` (com barra de vida), `Tiro`, `Explosao`, `Estrela` |
| [interface.py](interface.py)   | HUD, tela inicial, menu de pausa, tela de fim e a lista de controles |
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
