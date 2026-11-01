"""
Agenda da clínica - versão TERMINAL (Níveis 2 e 3).

Como rodar:
    python main_terminal.py              -> salva tudo no banco SQLite (agenda.db)
    python main_terminal.py --sem-banco  -> roda só na memória
"""
import sys
from pathlib import Path

from banco import BancoDeDados, popular_dados_exemplo
from interface.menu_terminal import MenuTerminal
from modelos import Clinica

NOME_CLINICA = "Clínica Bem-Estar"
CAMINHO_BANCO = Path(__file__).resolve().parent / "agenda.db"


def main() -> None:
    banco = None if "--sem-banco" in sys.argv else BancoDeDados(CAMINHO_BANCO)
    clinica = Clinica(NOME_CLINICA, banco)
    if clinica.vazia:  # primeira execução: grava alguns dados de exemplo
        popular_dados_exemplo(clinica)
    try:
        MenuTerminal(clinica, banco).executar()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma encerrado.")
    finally:
        if banco is not None:
            banco.fechar()


if __name__ == "__main__":
    main()
