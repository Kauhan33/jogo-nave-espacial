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
- **Pontos e moedas:** cada inimigo destruído vale **10 pontos** (chefe: 50 ×
  nº do chefe) e **cada ponto vira 1 moeda** para gastar na loja. O recorde
  da sessão aparece na tela de fim.
- Os menus funcionam por **teclado e mouse** (botões clicáveis). A **janela
  pode ser redimensionada**: o jogo é escalado mantendo a proporção 4:3.

### Níveis (infinitos, em ciclos de 10)

- **Níveis 1 a 4:** 2, 3, 4, 5 inimigos. **Nível 5:** só o chefe nº 1.
  **Níveis 6 a 9:** 7, 8, 9, 10 inimigos. **Nível 10:** só o chefe nº 2.
- **Nível 11 em diante (2º ciclo):** o chefe do nível 10 vira **permanente**
  e os inimigos comuns recomeçam em 2 (nível 11 = 1 chefe + 2 inimigos,
  nível 12 = 1 chefe + 3...), agora com **4 de vida**. Nos níveis 15 e 20
  entra o chefe novo junto com o permanente, sem inimigos comuns.
- **Nível 21 (3º ciclo):** 2 chefes permanentes (os dos níveis 10 e 20) +
  2 inimigos com 5 de vida, e assim sucessivamente.
- Ao terminar um nível aparece a tela "NÍVEL N"; a fase só começa com
  **ENTER** (ou clique em COMEÇAR). As vidas voltam para pelo menos 3;
  vidas extras acumuladas são mantidas até o **máximo de 5**.
- O jogo só termina quando as vidas acabam. O recorde da sessão aparece
  na tela de fim.

### Chefe

Nos níveis 5, 10, 15... aparece um **chefe** sozinho (por isso ele é ~50 %
mais forte que um inimigo de escolta permitiria). A cada chefe ele fica mais
forte: mais vida (22, 37, 52...), mais rápido, atira mais vezes e com **mais
tiros por rajada em leque** (3, 5, 7, até 9). Tem barra de vida grande no
topo da tela, vale 50 × nº do chefe em pontos/moedas.
**O chefe é imune à explosão** (tanto o poder quanto o especial).

### Poderes

**Metade dos inimigos** de cada fase (sorteados na montagem da fase; o chefe
sempre) solta poder ao morrer — não importa como morreu, congelado ou não.
Pegue encostando a nave.
**Os poderes valem só na fase em que foram pegos** — exceto a vida extra,
que acumula.

| Poder        | Efeito                                                     |
|--------------|------------------------------------------------------------|
| Tiro duplo   | Atira dois tiros de uma vez por 12 s                       |
| Explosão     | Destrói até 3 inimigos aleatórios na hora (não o chefe)    |
| Escudo       | Absorve o próximo tiro inimigo (círculo na nave)           |
| Vida extra   | +1 vida (máximo 5)                                          |
| Congelar     | Inimigos param de se mover e atirar por 5 s                |
| Tiro rápido  | Intervalo entre tiros cai pela metade por 12 s             |

- **Níveis 1 a 4:** um poder por nível, sem repetir (ordem sorteada).
- **Nível 5 em diante:** caem **duplas** de poderes, sorteadas sem repetir
  a mesma dupla. Quando todas as 15 duplas saem, passam a cair **trios**,
  depois quartetos, quintetos e os 6 juntos. Depois disso, qualquer
  combinação pode ser sorteada.
- A tela "NÍVEL N" e o rodapé do HUD mostram os poderes da fase; os poderes
  ativos e o tempo restante aparecem no canto inferior esquerdo.

### Especiais (carregam com o tempo)

Ficam no canto inferior direito com uma barra de carga. Quando a barra
enche toca um sino (um som diferente para cada especial); aperte a tecla
para usar e ela recarrega do zero.

| Tecla | Especial   | Carga | Efeito                                              |
|-------|------------|-------|-----------------------------------------------------|
| 1     | Vida extra | 30 s  | +1 vida (máx. 5; se já estiver no máximo, mantém a carga) |
| 2     | Explosão   | 60 s  | Destrói até 3 inimigos aleatórios (não afeta o chefe) |
| 3     | Tempestade | 90 s  | 1 de dano em **todos** os inimigos, chefe incluso   |

### Loja (fim de cada nível)

Na tela "NÍVEL N" aperte **L** ou clique em **LOJA** para gastar as moedas
da partida. No menu inicial a loja abre só para visualização. Tudo é
perdido ao começar uma nova partida.

| Item                    | Máx. | Preços (por nível)          | Efeito                                        |
|-------------------------|------|-----------------------------|-----------------------------------------------|
| Velocidade de movimento | 5    | 40 / 80 / 120 / 160 / 200   | +20 % de velocidade por nível (5 → 6, 7, 8, 9, 10) |
| Velocidade de tiro      | 5    | 50 / 100 / 150 / 200 / 250  | +20 % de cadência por nível (15 → 12, 10, 9, 8, 7 frames) |
| Potência do tiro        | 5    | 60 / 120 / 180 / 240 / 300  | +20 % de dano por nível (1,0 → 1,2 … 2,0)     |
| Ressurgir               | 1    | 150                         | Ao morrer, **R**/botão RESSURGIR continua de onde parou com 3 vidas |

## Controles

| Tecla              | Função                          |
|--------------------|---------------------------------|
| Setas / W A S D    | Mover a nave                    |
| Espaço             | Atirar (pode segurar)           |
| 1 / 2 / 3          | Usar especial (quando carregado) |
| L                  | Abrir a loja (fim de nível / menu) |
| Mouse              | Clicar nos botões dos menus     |
| ESC                | Pausar / abrir o menu de pausa  |
| Enter              | Confirmar / começar             |
| Setas Cima/Baixo   | Navegar no menu de pausa        |
| R                  | Reiniciar (pausa) / Ressurgir (fim) |
| M                  | Ligar / desligar o som          |
| Q                  | Sair do jogo                    |

Essa mesma tabela aparece **dentro do jogo**, na tela inicial e no menu de
pausa, e é impressa no terminal quando o jogo abre.

## Estrutura do código

| Arquivo                        | O que faz                                                          |
|--------------------------------|--------------------------------------------------------------------|
| [main.py](main.py)             | Laço principal (`while`), máquina de estados MENU/NIVEL/JOGANDO/PAUSA/LOJA/FIM, níveis, chefe, poderes, especiais, loja, colisões, escala da janela |
| [entidades.py](entidades.py)   | Classes `Nave`, `Inimigo` (com barra de vida), `Chefe`, `Tiro`, `Poder` (catálogo `PODERES`), `Explosao`, `Estrela` |
| [interface.py](interface.py)   | HUD, `Botao` (mouse), tela inicial, tela de nível, menu de pausa, loja, tela de fim e a lista de controles |
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
