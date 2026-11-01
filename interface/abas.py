"""
Abas (telas) da interface gráfica.

OO na interface:
- HERANÇA: todas as abas herdam de ttk.Frame.
- CLASSE ABSTRATA: AbaCadastro é o "molde" das telas de cadastro (formulário +
  tabela + botões Salvar/Limpar/Excluir).
- POLIMORFISMO: AbaClientes, AbaProfissionais e AbaServicos implementam só o que
  muda (_listar, _criar, _editar...). A janela principal chama aba.atualizar()
  em todas as abas sem saber de que tipo cada uma é.
"""
from __future__ import annotations

import tkinter as tk
from abc import ABC, abstractmethod
from datetime import date, timedelta
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, Dict, Optional, Sequence, Tuple

from modelos import (TIPOS_DE_SERVICO, AgendaErro, Cliente, Profissional, Relatorio, Servico,
                     StatusAgendamento)
from modelos.utilitarios import moeda

from .componentes import CartaoIndicador, Tabela
from .estilos import Tema

if TYPE_CHECKING:
    from .janelas import JanelaPrincipal

DIAS_DA_SEMANA = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
                  "sexta-feira", "sábado", "domingo")


def data_por_extenso(dia: date) -> str:
    return f"{DIAS_DA_SEMANA[dia.weekday()].capitalize()}, {dia:%d/%m/%Y}"


# =====================================================================
#  MOLDE DAS TELAS DE CADASTRO (classe abstrata)
# =====================================================================
class AbaCadastro(ttk.Frame, ABC):
    TITULO = "Registro"                          # sobrescritos nas filhas
    CAMPOS: Sequence[Tuple[str, str]] = ()       # (chave, rótulo)
    COLUNAS: Sequence[Tuple[str, str, int]] = ()  # (chave, título, largura)

    def __init__(self, pai: tk.Misc, janela: "JanelaPrincipal") -> None:
        super().__init__(pai, padding=16)
        self._janela = janela
        self._clinica = janela.clinica
        self._id_em_edicao: Optional[int] = None
        self._variaveis: Dict[str, tk.StringVar] = {}
        self.__montar()
        self._limpar()

    def __montar(self) -> None:
        # ----- formulário (cartão branco à esquerda) -----
        formulario = ttk.Frame(self, style="Cartao.TFrame", padding=18)
        formulario.pack(side="left", fill="y", padx=(0, 16))
        self._titulo_formulario = ttk.Label(formulario, style="CartaoTitulo.TLabel")
        self._titulo_formulario.pack(anchor="w", pady=(0, 12))
        for chave, rotulo in self.CAMPOS:
            ttk.Label(formulario, text=rotulo, style="CartaoSuave.TLabel").pack(anchor="w")
            self._criar_campo(formulario, chave).pack(fill="x", pady=(2, 10))
        ttk.Button(formulario, text="Salvar", style="Primario.TButton",
                   command=self._salvar).pack(fill="x", pady=(8, 0))
        ttk.Button(formulario, text="Limpar / Novo", command=self._limpar).pack(fill="x", pady=6)
        self._botao_excluir = ttk.Button(formulario, text="Excluir", style="Perigo.TButton",
                                         command=self._excluir)
        self._botao_excluir.pack(fill="x")

        # ----- pesquisa + tabela (à direita) -----
        lista = ttk.Frame(self)
        lista.pack(side="left", fill="both", expand=True)
        barra = ttk.Frame(lista)
        barra.pack(fill="x", pady=(0, 10))
        ttk.Label(barra, text="Pesquisar:").pack(side="left")
        self._pesquisa = tk.StringVar()
        self._pesquisa.trace_add("write", lambda *_: self.atualizar())
        ttk.Entry(barra, textvariable=self._pesquisa, width=32).pack(side="left", padx=8)
        self._contador = ttk.Label(barra, style="Suave.TLabel")
        self._contador.pack(side="right")
        self._tabela = Tabela(lista, self.COLUNAS)
        self._tabela.pack(fill="both", expand=True)
        self._tabela.arvore.bind("<<TreeviewSelect>>", self._ao_selecionar)
        ttk.Label(lista, text="Clique numa linha para editar ou excluir.",
                  style="Suave.TLabel").pack(anchor="w", pady=(8, 0))

    def _criar_campo(self, pai: tk.Misc, chave: str) -> ttk.Widget:
        """Cria um campo de texto. As filhas podem sobrescrever (ex.: Combobox)."""
        variavel = tk.StringVar()
        self._variaveis[chave] = variavel
        return ttk.Entry(pai, textvariable=variavel, width=34)

    # ----- comportamento comum (o "molde") -----
    def atualizar(self) -> None:
        itens = self._listar(self._pesquisa.get())
        total = self._tabela.preencher((item.id, self._linha(item), None) for item in itens)
        self._contador.configure(text=f"{total} registro(s)")

    def _ao_selecionar(self, _evento=None) -> None:
        id_selecionado = self._tabela.selecionado()
        if id_selecionado is None:
            return
        item = self._buscar(id_selecionado)
        self._id_em_edicao = id_selecionado
        for chave, valor in self._valores_formulario(item).items():
            self._variaveis[chave].set(valor)
        self._titulo_formulario.configure(text=f"Editando {self.TITULO.lower()} #{item.id}")
        self._botao_excluir.state(["!disabled"])

    def _limpar(self) -> None:
        self._id_em_edicao = None
        for variavel in self._variaveis.values():
            variavel.set("")
        self._tabela.limpar_selecao()
        self._titulo_formulario.configure(text=f"Novo {self.TITULO.lower()}")
        self._botao_excluir.state(["disabled"])

    def _salvar(self) -> None:
        dados = {chave: variavel.get() for chave, variavel in self._variaveis.items()}
        try:
            if self._id_em_edicao is None:
                item = self._criar(dados)
                mensagem = f"{self.TITULO} cadastrado(a): {item.nome} (código {item.id})"
            else:
                item = self._editar(self._id_em_edicao, dados)
                mensagem = f"{self.TITULO} atualizado(a): {item.nome}"
        except AgendaErro as erro:  # qualquer erro de validação do sistema
            messagebox.showerror("Não foi possível salvar", str(erro), parent=self)
            return
        self._limpar()
        self._janela.atualizar_tudo(mensagem)
        self._tabela.rolar_ate(item.id)

    def _excluir(self) -> None:
        if self._id_em_edicao is None:
            return
        item = self._buscar(self._id_em_edicao)
        if not messagebox.askyesno("Confirmar exclusão", f"Excluir {item.nome}?", parent=self):
            return
        try:
            self._remover(item.id)
        except AgendaErro as erro:
            messagebox.showerror("Não foi possível excluir", str(erro), parent=self)
            return
        self._limpar()
        self._janela.atualizar_tudo(f"{self.TITULO} excluído(a): {item.nome}")

    # ----- o que cada filha DEVE implementar (POLIMORFISMO) -----
    @abstractmethod
    def _listar(self, termo: str) -> list: ...

    @abstractmethod
    def _linha(self, item) -> Sequence: ...

    @abstractmethod
    def _buscar(self, id: int): ...

    @abstractmethod
    def _valores_formulario(self, item) -> Dict[str, str]: ...

    @abstractmethod
    def _criar(self, dados: Dict[str, str]): ...

    @abstractmethod
    def _editar(self, id: int, dados: Dict[str, str]): ...

    @abstractmethod
    def _remover(self, id: int) -> None: ...


class AbaClientes(AbaCadastro):
    TITULO = "Cliente"
    CAMPOS = (("nome", "Nome completo"), ("cpf", "CPF"),
              ("telefone", "Telefone com DDD"), ("email", "E-mail (opcional)"))
    COLUNAS = (("id", "Cód.", 60), ("nome", "Nome", 220), ("cpf", "CPF", 130),
               ("telefone", "Telefone", 140), ("email", "E-mail", 230))

    def _listar(self, termo):
        return self._clinica.listar_clientes(termo)

    def _linha(self, c):
        return (c.id, c.nome, c.cpf_formatado, c.contato.telefone_formatado, c.contato.email or "-")

    def _buscar(self, id):
        return self._clinica.buscar_cliente(id)

    def _valores_formulario(self, c):
        return {"nome": c.nome, "cpf": c.cpf_formatado,
                "telefone": c.contato.telefone_formatado, "email": c.contato.email}

    def _criar(self, d):
        return self._clinica.cadastrar_cliente(Cliente(d["nome"], d["telefone"], d["cpf"], d["email"]))

    def _editar(self, id, d):
        return self._clinica.editar_cliente(id, d["nome"], d["telefone"], d["cpf"], d["email"])

    def _remover(self, id):
        self._clinica.remover_cliente(id)


class AbaProfissionais(AbaCadastro):
    TITULO = "Profissional"
    CAMPOS = (("nome", "Nome completo"), ("especialidade", "Especialidade"),
              ("telefone", "Telefone com DDD"), ("email", "E-mail (opcional)"))
    COLUNAS = (("id", "Cód.", 60), ("nome", "Nome", 220), ("especialidade", "Especialidade", 170),
               ("telefone", "Telefone", 140), ("email", "E-mail", 220))

    def _listar(self, termo):
        return self._clinica.listar_profissionais(termo)

    def _linha(self, p):
        return (p.id, p.nome, p.especialidade, p.contato.telefone_formatado, p.contato.email or "-")

    def _buscar(self, id):
        return self._clinica.buscar_profissional(id)

    def _valores_formulario(self, p):
        return {"nome": p.nome, "especialidade": p.especialidade,
                "telefone": p.contato.telefone_formatado, "email": p.contato.email}

    def _criar(self, d):
        return self._clinica.cadastrar_profissional(
            Profissional(d["nome"], d["telefone"], d["especialidade"], d["email"]))

    def _editar(self, id, d):
        return self._clinica.editar_profissional(id, d["nome"], d["telefone"],
                                                 d["especialidade"], d["email"])

    def _remover(self, id):
        self._clinica.remover_profissional(id)


class AbaServicos(AbaCadastro):
    TITULO = "Serviço"
    CAMPOS = (("tipo", "Tipo"), ("nome", "Nome do serviço"), ("preco_base", "Preço base (R$)"),
              ("duracao_min", "Duração (minutos)"), ("taxa_material", "Taxa de material (só Exame)"))
    COLUNAS = (("id", "Cód.", 60), ("tipo", "Tipo", 100), ("nome", "Nome", 210),
               ("preco", "Preço base", 110), ("valor", "Valor cobrado", 120),
               ("duracao", "Duração", 90))

    def _criar_campo(self, pai, chave):
        """Sobrescrita: 'tipo' vira uma lista de opções e a taxa só vale para Exame."""
        if chave != "tipo":
            campo = super()._criar_campo(pai, chave)
            if chave == "taxa_material":
                self._campo_taxa = campo
            return campo
        variavel = tk.StringVar()
        self._variaveis[chave] = variavel
        variavel.trace_add("write", lambda *_: self.__ajustar_taxa())
        self._campo_tipo = ttk.Combobox(pai, textvariable=variavel, values=TIPOS_DE_SERVICO,
                                        state="readonly", width=32)
        return self._campo_tipo

    def __ajustar_taxa(self) -> None:
        if hasattr(self, "_campo_taxa"):
            e_exame = self._variaveis["tipo"].get() == "Exame"
            self._campo_taxa.state(["!disabled"] if e_exame else ["disabled"])
            if not e_exame:
                self._variaveis["taxa_material"].set("0")

    def _limpar(self):
        super()._limpar()
        self._campo_tipo.configure(state="readonly")  # no cadastro pode escolher o tipo
        self._variaveis["tipo"].set("Consulta")

    def _ao_selecionar(self, _evento=None):
        super()._ao_selecionar(_evento)
        if self._id_em_edicao is not None:
            self._campo_tipo.configure(state="disabled")  # o tipo não muda depois de criado

    def _listar(self, termo):
        return self._clinica.listar_servicos(termo)

    def _linha(self, s):
        return (s.id, s.TIPO, s.nome, moeda(s.preco_base), moeda(s.calcular_valor()),
                f"{s.duracao_min} min")

    def _buscar(self, id):
        return self._clinica.buscar_servico(id)

    def _valores_formulario(self, s):
        taxa = getattr(s, "taxa_material", 0)  # só o Exame tem taxa
        return {"tipo": s.TIPO, "nome": s.nome, "preco_base": f"{s.preco_base:.2f}".replace(".", ","),
                "duracao_min": str(s.duracao_min), "taxa_material": f"{taxa:.2f}".replace(".", ",")}

    def _criar(self, d):
        servico = Servico.criar(d["tipo"], d["nome"], d["preco_base"], d["duracao_min"],
                                d["taxa_material"] or 0)  # FÁBRICA
        return self._clinica.cadastrar_servico(servico)

    def _editar(self, id, d):
        return self._clinica.editar_servico(id, d["nome"], d["preco_base"], d["duracao_min"],
                                            d["taxa_material"] or 0)

    def _remover(self, id):
        self._clinica.remover_servico(id)


# =====================================================================
#  AGENDA DO DIA
# =====================================================================
class AbaAgenda(ttk.Frame):
    COLUNAS = (("id", "Cód.", 55), ("horario", "Horário", 110), ("cliente", "Cliente", 170),
               ("profissional", "Profissional", 160), ("servico", "Serviço", 170),
               ("valor", "Valor", 100), ("status", "Status", 105), ("obs", "Observação", 170))
    TODOS = "Todos os profissionais"

    def __init__(self, pai: tk.Misc, janela: "JanelaPrincipal") -> None:
        super().__init__(pai, padding=16)
        self._janela = janela
        self._clinica = janela.clinica
        self.dia = date.today()
        self._profissionais: Dict[str, Profissional] = {}
        self.__montar()

    def __montar(self) -> None:
        topo = ttk.Frame(self)
        topo.pack(fill="x", pady=(0, 12))
        ttk.Button(topo, text="<", width=3, command=lambda: self.mudar_dia(-1)).pack(side="left")
        ttk.Button(topo, text="Hoje", command=self.ir_para_hoje).pack(side="left", padx=4)
        ttk.Button(topo, text=">", width=3, command=lambda: self.mudar_dia(1)).pack(side="left")
        self._rotulo_dia = ttk.Label(topo, style="Secao.TLabel")
        self._rotulo_dia.pack(side="left", padx=16)
        ttk.Button(topo, text="+  Novo agendamento", style="Primario.TButton",
                   command=lambda: self._janela.abrir_agendamento()).pack(side="right")
        self._filtro = tk.StringVar(value=self.TODOS)
        self._combo_filtro = ttk.Combobox(topo, textvariable=self._filtro, state="readonly", width=26)
        self._combo_filtro.pack(side="right", padx=12)
        self._combo_filtro.bind("<<ComboboxSelected>>", lambda _e: self.atualizar())

        self._tabela = Tabela(self, self.COLUNAS, altura=13)
        self._tabela.pack(fill="both", expand=True)
        self._tabela.arvore.bind("<Double-1>", self._mostrar_detalhes)

        rodape = ttk.Frame(self)
        rodape.pack(fill="x", pady=(12, 0))
        acoes = (("Confirmar", "Info", self._clinica.confirmar_agendamento),
                 ("Concluir", "Sucesso", self._clinica.concluir_agendamento),
                 ("Cancelar agendamento", "Perigo", self._clinica.cancelar_agendamento))
        for texto, estilo, metodo in acoes:
            ttk.Button(rodape, text=texto, style=f"{estilo}.TButton",
                       command=lambda m=metodo, t=texto: self._mudar_status(m, t)
                       ).pack(side="left", padx=(0, 8))
        ttk.Button(rodape, text="Remarcar", style="Aviso.TButton",
                   command=self._remarcar).pack(side="left")
        legenda = ttk.Frame(rodape)
        legenda.pack(side="right")
        for status in StatusAgendamento:  # legenda: uma etiqueta colorida por status
            ttk.Label(legenda, text=status.value,
                      style=f"{status.name}.Legenda.TLabel").pack(side="left", padx=3)
        self._resumo = ttk.Label(self, style="Suave.TLabel")
        self._resumo.pack(anchor="w", pady=(10, 0))

    # ----- navegação -----
    def mudar_dia(self, dias: int) -> None:
        self.dia += timedelta(days=dias)
        self.atualizar()

    def ir_para_hoje(self) -> None:
        self.dia = date.today()
        self.atualizar()

    def mostrar_dia(self, dia: date, selecionar: Optional[int] = None) -> None:
        self.dia = dia
        self.atualizar()
        if selecionar is not None:
            self._tabela.selecionar(selecionar)

    # ----- dados -----
    def atualizar(self) -> None:
        self._profissionais = {f"{p.nome} ({p.especialidade})": p
                               for p in self._clinica.listar_profissionais()}
        self._combo_filtro.configure(values=[self.TODOS] + list(self._profissionais))
        if self._filtro.get() not in self._profissionais:
            self._filtro.set(self.TODOS)
        profissional = self._profissionais.get(self._filtro.get())
        agendamentos = self._clinica.listar_agendamentos(
            dia=self.dia, id_profissional=profissional.id if profissional else None)
        self._tabela.preencher(
            (ag.id, (ag.id, f"{ag.data_hora:%H:%M} - {ag.fim:%H:%M}", ag.cliente.nome,
                     ag.profissional.nome, ag.servico.nome, moeda(ag.valor), ag.status.value,
                     ag.observacao or "-"), ag.status.name)
            for ag in agendamentos)
        hoje = "  (hoje)" if self.dia == date.today() else ""
        self._rotulo_dia.configure(text=data_por_extenso(self.dia) + hoje)
        previsto = Relatorio().faturamento_previsto(agendamentos)  # DEPENDÊNCIA
        self._resumo.configure(
            text=f"{len(agendamentos)} agendamento(s) neste dia  •  em aberto: {moeda(previsto)}"
                 f"  •  dê dois cliques numa linha para ver os detalhes")

    def _selecionado(self):
        id_agendamento = self._tabela.selecionado()
        if id_agendamento is None:
            messagebox.showinfo("Agenda", "Selecione um agendamento na tabela.", parent=self)
            return None
        return self._clinica.buscar_agendamento(id_agendamento)

    def _mudar_status(self, metodo, texto: str) -> None:
        agendamento = self._selecionado()
        if agendamento is None:
            return
        try:
            metodo(agendamento.id)
        except AgendaErro as erro:
            messagebox.showerror(texto, str(erro), parent=self)
            return
        self._janela.atualizar_tudo(f"Agendamento #{agendamento.id}: {agendamento.status.value}")
        self._tabela.selecionar(agendamento.id)

    def _remarcar(self) -> None:
        agendamento = self._selecionado()
        if agendamento is not None:
            self._janela.abrir_agendamento(agendamento)

    def _mostrar_detalhes(self, _evento=None) -> None:
        agendamento = self._selecionado()
        if agendamento is None:
            return
        messagebox.showinfo(
            f"Agendamento #{agendamento.id}",
            f"{agendamento.cliente.descricao()}\n\n{agendamento.profissional.descricao()}\n\n"
            f"{agendamento.servico}\n\nQuando: {agendamento.data_hora:%d/%m/%Y %H:%M} até "
            f"{agendamento.fim:%H:%M}\nStatus: {agendamento.status.value}\n"
            f"Observação: {agendamento.observacao or '-'}", parent=self)


# =====================================================================
#  RELATÓRIOS
# =====================================================================
class AbaRelatorios(ttk.Frame):
    def __init__(self, pai: tk.Misc, janela: "JanelaPrincipal") -> None:
        super().__init__(pai, padding=16)
        self._janela = janela
        self._clinica = janela.clinica
        self._relatorio = Relatorio("Relatório da agenda")
        self._cartoes: Dict[str, CartaoIndicador] = {}

        grade = ttk.Frame(self)
        grade.pack(fill="x")
        indicadores = (("Agendado", "Agendados", "#2563EB"), ("Confirmado", "Confirmados", "#16A34A"),
                       ("Concluído", "Concluídos", "#475569"), ("Cancelado", "Cancelados", "#DC2626"),
                       ("realizado", "Faturamento realizado", Tema.PRIMARIA),
                       ("previsto", "Faturamento previsto", "#D97706"),
                       ("clientes", "Clientes", "#7C3AED"), ("profissionais", "Profissionais", "#0891B2"))
        for posicao, (chave, titulo, cor) in enumerate(indicadores):
            cartao = CartaoIndicador(grade, titulo, cor)
            cartao.grid(row=posicao // 4, column=posicao % 4, sticky="nsew", padx=6, pady=6)
            self._cartoes[chave] = cartao
        for coluna in range(4):
            grade.columnconfigure(coluna, weight=1, uniform="cartoes")

        cabecalho = ttk.Frame(self)
        cabecalho.pack(fill="x", pady=(14, 8))
        ttk.Label(cabecalho, text="Desempenho por profissional", style="Secao.TLabel").pack(side="left")
        ttk.Button(cabecalho, text="Exportar relatório (.txt)", style="Primario.TButton",
                   command=self._exportar).pack(side="right")
        self._tabela = Tabela(self, (("profissional", "Profissional", 260),
                                     ("abertos", "Em aberto", 120),
                                     ("concluidos", "Concluídos", 120),
                                     ("faturado", "Faturado", 160)), altura=6)
        self._tabela.pack(fill="both", expand=True)

    def atualizar(self) -> None:
        agenda = self._clinica.agenda
        for status, quantidade in self._relatorio.total_por_status(agenda).items():
            self._cartoes[status].definir(quantidade)
        self._cartoes["realizado"].definir(moeda(self._relatorio.faturamento_realizado(agenda)))
        self._cartoes["previsto"].definir(moeda(self._relatorio.faturamento_previsto(agenda)))
        self._cartoes["clientes"].definir(len(self._clinica.listar_clientes()))
        self._cartoes["profissionais"].definir(len(self._clinica.listar_profissionais()))
        self._tabela.preencher(
            (posicao, (l["profissional"], l["em_aberto"], l["concluidos"], moeda(l["faturado"])), None)
            for posicao, l in enumerate(self._relatorio.por_profissional(agenda), start=1))

    def _exportar(self) -> None:
        caminho = filedialog.asksaveasfilename(
            parent=self, title="Salvar relatório", defaultextension=".txt",
            initialfile=f"relatorio_{date.today():%Y-%m-%d}.txt",
            filetypes=[("Arquivo de texto", "*.txt")])
        if not caminho:
            return
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(self._relatorio.gerar_texto(self._clinica.agenda))
        self._janela.atualizar_tudo(f"Relatório salvo em {caminho}")
