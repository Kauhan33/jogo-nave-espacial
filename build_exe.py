"""
Gera o executável Windows (um único .exe) do jogo.

    python build_exe.py

Requer o PyInstaller (pip install pyinstaller) e o pygame instalados no mesmo
Python que roda este script. O resultado fica em dist/NaveEspacial.exe.
As pastas build/ e dist/ e o arquivo .spec são gerados a cada execução e não
entram no repositório.

Opções usadas:
- --onefile: um arquivo só, fácil de distribuir (na primeira execução o
  Windows descompacta o conteúdo numa pasta temporária, por isso demora
  alguns segundos para abrir).
- --windowed: sem janela de console atrás do jogo. Os `print` continuam no
  código, mas só aparecem quando o jogo é rodado com `python main.py`.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

NOME = "NaveEspacial"
PONTO_DE_ENTRADA = "main.py"

AQUI = Path(__file__).resolve().parent


def main() -> int:
    for pasta in ("build", "dist"):
        shutil.rmtree(AQUI / pasta, ignore_errors=True)
    (AQUI / f"{NOME}.spec").unlink(missing_ok=True)

    comando = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", NOME,
        PONTO_DE_ENTRADA,
    ]
    print("Gerando", NOME + ".exe ...")
    resultado = subprocess.run(comando, cwd=AQUI)
    if resultado.returncode != 0:
        print("Falhou. Veja as mensagens acima.")
        return resultado.returncode

    exe = AQUI / "dist" / f"{NOME}.exe"
    print(f"\nPronto: {exe} ({exe.stat().st_size / 1_000_000:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
