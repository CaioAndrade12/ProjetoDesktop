"""
Estilos PERSONALIZADOS da interface gráfica (cores, fontes, botões e tabelas).

A classe Tema concentra a identidade visual do sistema:
- ATRIBUTOS DE CLASSE guardam a paleta de cores;
- o MÉTODO DE CLASSE aplicar() configura o ttk.Style da janela.
"""
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


class Tema:
    PRIMARIA = "#0F766E"          # verde-petróleo (cor da marca)
    PRIMARIA_ESCURA = "#115E59"
    PRIMARIA_CLARA = "#CCFBF1"
    FUNDO = "#F1F5F9"
    CARTAO = "#FFFFFF"
    LINHA_ALTERNADA = "#F8FAFC"
    BORDA = "#E2E8F0"
    TEXTO = "#0F172A"
    TEXTO_SUAVE = "#64748B"

    # (nome do estilo, cor, cor ao passar o mouse)
    BOTOES_COLORIDOS = (
        ("Primario", "#0F766E", "#115E59"),
        ("Sucesso", "#16A34A", "#15803D"),
        ("Info", "#2563EB", "#1D4ED8"),
        ("Aviso", "#D97706", "#B45309"),
        ("Perigo", "#DC2626", "#B91C1C"),
    )

    # fundo e cor do texto de cada status na tabela da agenda
    CORES_STATUS = {
        "AGENDADO": ("#EFF6FF", "#1E3A8A"),
        "CONFIRMADO": ("#ECFDF5", "#065F46"),
        "CONCLUIDO": ("#F1F5F9", "#475569"),
        "CANCELADO": ("#FEF2F2", "#991B1B"),
    }

    FAMILIA = "Segoe UI"  # fonte padrão do Windows

    @classmethod
    def fonte(cls, tamanho: int = 10, peso: str = "normal") -> tuple:
        return (cls.FAMILIA, tamanho, peso)

    @classmethod
    def aplicar(cls, raiz: tk.Misc) -> None:
        disponiveis = {familia.lower() for familia in tkfont.families(raiz)}
        for familia in ("Segoe UI", "Inter", "DejaVu Sans", "Helvetica"):
            if familia.lower() in disponiveis:
                cls.FAMILIA = familia
                break
        for nome in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.Font(root=raiz, name=nome, exists=True).configure(family=cls.FAMILIA, size=10)

        raiz.configure(background=cls.FUNDO)
        estilo = ttk.Style(raiz)
        estilo.theme_use("clam")  # tema base que aceita cores personalizadas

        estilo.configure(".", background=cls.FUNDO, foreground=cls.TEXTO, font=cls.fonte(),
                         bordercolor=cls.BORDA, focuscolor=cls.PRIMARIA)
        cls.__estilos_de_texto(estilo)
        cls.__estilos_de_botoes(estilo)
        cls.__estilos_de_campos(estilo)
        cls.__estilos_de_tabela(estilo, raiz)

    @classmethod
    def __estilos_de_texto(cls, estilo: ttk.Style) -> None:
        estilo.configure("TFrame", background=cls.FUNDO)
        estilo.configure("Cartao.TFrame", background=cls.CARTAO, relief="solid", borderwidth=1)
        estilo.configure("Cabecalho.TFrame", background=cls.PRIMARIA)
        estilo.configure("TLabel", background=cls.FUNDO, foreground=cls.TEXTO)
        estilo.configure("Suave.TLabel", foreground=cls.TEXTO_SUAVE)
        estilo.configure("Secao.TLabel", foreground=cls.PRIMARIA_ESCURA, font=cls.fonte(14, "bold"))
        estilo.configure("Titulo.TLabel", background=cls.PRIMARIA, foreground="white",
                         font=cls.fonte(20, "bold"))
        estilo.configure("Subtitulo.TLabel", background=cls.PRIMARIA,
                         foreground=cls.PRIMARIA_CLARA, font=cls.fonte(11))
        estilo.configure("Cartao.TLabel", background=cls.CARTAO)
        estilo.configure("CartaoSuave.TLabel", background=cls.CARTAO, foreground=cls.TEXTO_SUAVE)
        estilo.configure("CartaoTitulo.TLabel", background=cls.CARTAO,
                         foreground=cls.PRIMARIA_ESCURA, font=cls.fonte(14, "bold"))
        estilo.configure("CartaoNumero.TLabel", background=cls.CARTAO,
                         foreground=cls.TEXTO, font=cls.fonte(20, "bold"))
        estilo.configure("Destaque.TLabel", background=cls.CARTAO,
                         foreground=cls.PRIMARIA, font=cls.fonte(11, "bold"))
        estilo.configure("Status.TLabel", background=cls.BORDA, foreground=cls.TEXTO_SUAVE,
                         padding=(14, 6))
        for status, (fundo, texto) in cls.CORES_STATUS.items():
            estilo.configure(f"{status}.Legenda.TLabel", background=fundo, foreground=texto,
                             font=cls.fonte(9, "bold"), padding=(10, 4))
        estilo.configure("Cartao.TRadiobutton", background=cls.CARTAO)
        estilo.map("Cartao.TRadiobutton", background=[("active", cls.CARTAO)],
                   indicatorcolor=[("selected", cls.PRIMARIA), ("!selected", "white")])
        estilo.configure("TNotebook", background=cls.FUNDO, borderwidth=0, tabmargins=(0, 4, 0, 0))
        estilo.configure("TNotebook.Tab", padding=(20, 9), font=cls.fonte(10, "bold"),
                         background=cls.BORDA, foreground=cls.TEXTO_SUAVE,
                         bordercolor=cls.BORDA, lightcolor=cls.BORDA)
        estilo.map("TNotebook.Tab",
                   background=[("selected", cls.CARTAO), ("active", "#EEF2F6")],
                   foreground=[("selected", cls.PRIMARIA)],
                   lightcolor=[("selected", cls.PRIMARIA)])

    @classmethod
    def __estilos_de_botoes(cls, estilo: ttk.Style) -> None:
        estilo.configure("TButton", padding=(14, 7), font=cls.fonte(10, "bold"),
                         background=cls.BORDA, foreground=cls.TEXTO, bordercolor=cls.BORDA,
                         lightcolor=cls.BORDA, darkcolor=cls.BORDA, relief="flat")
        estilo.map("TButton",
                   background=[("disabled", cls.FUNDO), ("pressed", "#CBD5E1"), ("active", "#CBD5E1")],
                   bordercolor=[("active", "#CBD5E1")], lightcolor=[("active", "#CBD5E1")],
                   darkcolor=[("active", "#CBD5E1")], foreground=[("disabled", "#94A3B8")])
        for nome, cor, escura in cls.BOTOES_COLORIDOS:
            estilo.configure(f"{nome}.TButton", background=cor, foreground="white",
                             bordercolor=cor, lightcolor=cor, darkcolor=cor)
            estilo.map(f"{nome}.TButton",
                       background=[("disabled", "#CBD5E1"), ("pressed", escura), ("active", escura)],
                       foreground=[("disabled", "#F8FAFC")],
                       bordercolor=[("disabled", "#CBD5E1"), ("active", escura)],
                       lightcolor=[("disabled", "#CBD5E1"), ("active", escura)],
                       darkcolor=[("disabled", "#CBD5E1"), ("active", escura)])

    @classmethod
    def __estilos_de_campos(cls, estilo: ttk.Style) -> None:
        estilo.configure("TEntry", fieldbackground="white", bordercolor="#CBD5E1",
                         lightcolor="white", darkcolor="white", padding=6)
        estilo.map("TEntry", bordercolor=[("focus", cls.PRIMARIA)],
                   lightcolor=[("focus", cls.PRIMARIA)])
        estilo.configure("TCombobox", fieldbackground="white", background=cls.CARTAO,
                         bordercolor="#CBD5E1", lightcolor="white", darkcolor="white",
                         arrowcolor=cls.PRIMARIA, padding=5)
        estilo.map("TCombobox",
                   fieldbackground=[("disabled", cls.FUNDO), ("readonly", "white")],
                   foreground=[("disabled", cls.TEXTO_SUAVE)],
                   bordercolor=[("focus", cls.PRIMARIA)],
                   selectbackground=[("readonly", "white")],
                   selectforeground=[("readonly", cls.TEXTO)])
        estilo.configure("Vertical.TScrollbar", background=cls.BORDA, troughcolor=cls.CARTAO,
                         bordercolor=cls.CARTAO, arrowcolor=cls.TEXTO_SUAVE,
                         lightcolor=cls.BORDA, darkcolor=cls.BORDA)

    @classmethod
    def __estilos_de_tabela(cls, estilo: ttk.Style, raiz: tk.Misc) -> None:
        altura_linha = tkfont.Font(root=raiz, font=cls.fonte()).metrics("linespace") + 14
        estilo.configure("Treeview", background=cls.CARTAO, fieldbackground=cls.CARTAO,
                         foreground=cls.TEXTO, rowheight=altura_linha, borderwidth=0,
                         font=cls.fonte())
        # mapa explícito: linha selecionada fica na cor da marca (e evita bug de cores do Tk)
        estilo.map("Treeview", background=[("selected", cls.PRIMARIA)],
                   foreground=[("selected", "white")])
        estilo.configure("Treeview.Heading", background=cls.PRIMARIA_ESCURA, foreground="white",
                         font=cls.fonte(10, "bold"), relief="flat", padding=(8, 7),
                         bordercolor=cls.PRIMARIA_ESCURA, lightcolor=cls.PRIMARIA_ESCURA,
                         darkcolor=cls.PRIMARIA_ESCURA)
        estilo.map("Treeview.Heading", background=[("active", cls.PRIMARIA)])
