"""Componentes visuais reaproveitados nas telas (COMPOSIÇÃO de widgets)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Iterable, Optional, Sequence, Tuple

from .estilos import Tema


class Tabela(ttk.Frame):
    """Tabela = Treeview + barra de rolagem, com linhas zebradas e cores por status."""

    def __init__(self, pai: tk.Misc, colunas: Sequence[Tuple[str, str, int]],
                 altura: int = 14) -> None:
        super().__init__(pai, style="Cartao.TFrame")
        self.arvore = ttk.Treeview(self, columns=[c[0] for c in colunas], show="headings",
                                   height=altura, selectmode="browse")
        for chave, titulo, largura in colunas:
            self.arvore.heading(chave, text=titulo, anchor="w")
            self.arvore.column(chave, width=largura, minwidth=40, anchor="w", stretch=True)
        rolagem = ttk.Scrollbar(self, orient="vertical", command=self.arvore.yview)
        self.arvore.configure(yscrollcommand=rolagem.set)
        rolagem.pack(side="right", fill="y")
        self.arvore.pack(side="left", fill="both", expand=True)

        self.arvore.tag_configure("par", background=Tema.CARTAO)
        self.arvore.tag_configure("impar", background=Tema.LINHA_ALTERNADA)
        for status, (fundo, texto) in Tema.CORES_STATUS.items():
            self.arvore.tag_configure(status, background=fundo, foreground=texto)

    def preencher(self, linhas: Iterable[Tuple[int, Sequence, Optional[str]]]) -> int:
        """Recebe (id, valores, tag) por linha. Sem tag, usa linhas zebradas."""
        self.arvore.delete(*self.arvore.get_children())
        total = 0
        for posicao, (iid, valores, tag) in enumerate(linhas):
            tag = tag or ("impar" if posicao % 2 else "par")
            self.arvore.insert("", "end", iid=str(iid), values=list(valores), tags=(tag,))
            total += 1
        return total

    def selecionado(self) -> Optional[int]:
        selecao = self.arvore.selection()
        return int(selecao[0]) if selecao else None

    def selecionar(self, iid: int) -> None:
        if self.arvore.exists(str(iid)):
            self.arvore.selection_set(str(iid))
            self.arvore.see(str(iid))

    def rolar_ate(self, iid: int) -> None:
        if self.arvore.exists(str(iid)):
            self.arvore.see(str(iid))

    def limpar_selecao(self) -> None:
        self.arvore.selection_remove(self.arvore.selection())


class CartaoIndicador(ttk.Frame):
    """Cartão de indicador (título + número grande) com uma faixa colorida."""

    def __init__(self, pai: tk.Misc, titulo: str, cor: str = Tema.PRIMARIA) -> None:
        super().__init__(pai, style="Cartao.TFrame")
        tk.Frame(self, background=cor, width=6).pack(side="left", fill="y")
        conteudo = ttk.Frame(self, style="Cartao.TFrame", padding=(14, 10))
        conteudo.configure(borderwidth=0)
        conteudo.pack(side="left", fill="both", expand=True)
        ttk.Label(conteudo, text=titulo, style="CartaoSuave.TLabel").pack(anchor="w")
        self.__valor = ttk.Label(conteudo, text="-", style="CartaoNumero.TLabel")
        self.__valor.pack(anchor="w", pady=(2, 0))

    @property
    def valor(self) -> str:
        return self.__valor.cget("text")

    def definir(self, valor) -> None:
        self.__valor.configure(text=str(valor))
