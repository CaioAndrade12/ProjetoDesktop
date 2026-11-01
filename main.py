"""
Agenda da clínica - INTERFACE GRÁFICA (Nível 4).

Como rodar:
    python main.py
"""
import sys
from pathlib import Path

from banco import BancoDeDados, popular_dados_exemplo
from interface.janelas import JanelaPrincipal
from modelos import Clinica

NOME_CLINICA = "Clínica Bem-Estar"
CAMINHO_BANCO = Path(__file__).resolve().parent / "agenda.db"


def ativar_nitidez_no_windows() -> None:
    """Evita letras borradas em telas com zoom (125%, 150%...) no Windows."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def main() -> None:
    ativar_nitidez_no_windows()
    banco = BancoDeDados(CAMINHO_BANCO)
    clinica = Clinica(NOME_CLINICA, banco)
    if clinica.vazia:
        popular_dados_exemplo(clinica)
    janela = JanelaPrincipal(clinica, info_banco=f"SQLite ({CAMINHO_BANCO.name})")
    janela.mainloop()
    banco.fechar()


if __name__ == "__main__":
    main()
