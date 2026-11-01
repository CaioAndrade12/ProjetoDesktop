"""
Janelas da interface gráfica (Nível 4).

- HERANÇA: JanelaPrincipal herda de tk.Tk e JanelaAgendamento herda de tk.Toplevel.
- POLIMORFISMO: atualizar_tudo() chama aba.atualizar() em todas as abas.
- ASSOCIAÇÃO: as janelas guardam a Clínica e só conversam com ela.
"""
from __future__ import annotations

import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk
from typing import Dict, Optional

from modelos import (AgendaErro, Agendamento, Clinica, DadoInvalidoErro, NotificadorEmail,
                     NotificadorWhatsApp)
from modelos.utilitarios import moeda

from .abas import (AbaAgenda, AbaClientes, AbaProfissionais, AbaRelatorios, AbaServicos,
                   data_por_extenso)
from .estilos import Tema


class JanelaPrincipal(tk.Tk):
    """Janela principal: cabeçalho, abas e barra de status."""

    def __init__(self, clinica: Clinica, info_banco: str = "memória") -> None:
        super().__init__()
        self.clinica = clinica                 # ASSOCIAÇÃO
        self.__info_banco = info_banco
        self.title(f"{clinica.nome} - Agenda de atendimentos")
        Tema.aplicar(self)                     # estilos personalizados
        self.__posicionar()
        self.__montar_cabecalho()
        self.__status = ttk.Label(self, style="Status.TLabel", anchor="w")
        self.__status.pack(side="bottom", fill="x")

        self.__notebook = ttk.Notebook(self)
        self.__notebook.pack(fill="both", expand=True, padx=16, pady=(12, 12))
        self.aba_agenda = AbaAgenda(self.__notebook, self)
        self.__abas = [
            ("Agenda", self.aba_agenda),
            ("Clientes", AbaClientes(self.__notebook, self)),
            ("Profissionais", AbaProfissionais(self.__notebook, self)),
            ("Serviços", AbaServicos(self.__notebook, self)),
            ("Relatórios", AbaRelatorios(self.__notebook, self)),
        ]
        for titulo, aba in self.__abas:
            self.__notebook.add(aba, text=f"  {titulo}  ")
        self.bind("<Control-n>", lambda _e: self.abrir_agendamento())
        self.atualizar_tudo("Bem-vindo(a)! Dica: Ctrl+N abre um novo agendamento.")

    @property
    def abas(self) -> list:
        return [aba for _, aba in self.__abas]

    def __posicionar(self) -> None:
        largura = min(1280, int(self.winfo_screenwidth() * 0.9))
        altura = min(780, int(self.winfo_screenheight() * 0.85))
        x = (self.winfo_screenwidth() - largura) // 2
        y = max(0, (self.winfo_screenheight() - altura) // 2 - 20)
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.minsize(1040, 640)

    def __montar_cabecalho(self) -> None:
        cabecalho = ttk.Frame(self, style="Cabecalho.TFrame", padding=(24, 14))
        cabecalho.pack(fill="x")
        textos = ttk.Frame(cabecalho, style="Cabecalho.TFrame")
        textos.pack(side="left")
        ttk.Label(textos, text=self.clinica.nome, style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(textos, text="Agenda de atendimentos de clientes e pacientes",
                  style="Subtitulo.TLabel").pack(anchor="w")
        ttk.Label(cabecalho, text=data_por_extenso(date.today()),
                  style="Subtitulo.TLabel").pack(side="right")

    # ---------- usados pelas abas ----------
    def atualizar_tudo(self, mensagem: str = "") -> None:
        for aba in self.abas:
            aba.atualizar()  # POLIMORFISMO: cada aba sabe se atualizar
        self.__status.configure(
            text=f"{mensagem}    |    Banco de dados: {self.__info_banco}    |    "
                 f"atualizado às {datetime.now():%H:%M:%S}")

    def abrir_agendamento(self, agendamento: Optional[Agendamento] = None) -> "JanelaAgendamento":
        dia = max(self.aba_agenda.dia, date.today())
        return JanelaAgendamento(self, dia, agendamento)

    def mostrar_agendamento(self, agendamento: Agendamento) -> None:
        self.__notebook.select(self.aba_agenda)
        self.aba_agenda.mostrar_dia(agendamento.data_hora.date(), selecionar=agendamento.id)


class JanelaAgendamento(tk.Toplevel):
    """Janela (diálogo) para criar um agendamento ou remarcar um existente."""

    SEM_AVISO, WHATSAPP, EMAIL = "nenhum", "whatsapp", "email"

    def __init__(self, principal: JanelaPrincipal, dia: date,
                 agendamento: Optional[Agendamento] = None) -> None:
        super().__init__(principal)
        self.__principal = principal
        self.__clinica = principal.clinica
        self.__agendamento = agendamento
        self.remarcando = agendamento is not None
        self.title("Remarcar agendamento" if self.remarcando else "Novo agendamento")
        self.configure(background=Tema.FUNDO)
        self.resizable(False, False)
        self.transient(principal)

        self.__clientes = {f"{c.id} - {c.nome}": c for c in self.__clinica.listar_clientes()}
        self.__profissionais = {f"{p.id} - {p.nome} ({p.especialidade})": p
                                for p in self.__clinica.listar_profissionais()}
        self.__servicos = {f"{s.id} - {s.nome} ({moeda(s.calcular_valor())})": s
                           for s in self.__clinica.listar_servicos()}
        self.var_cliente = tk.StringVar()
        self.var_profissional = tk.StringVar()
        self.var_servico = tk.StringVar()
        self.var_data = tk.StringVar(value=f"{dia:%d/%m/%Y}")
        self.var_hora = tk.StringVar()
        self.var_observacao = tk.StringVar()
        self.var_aviso = tk.StringVar(value=self.SEM_AVISO)

        self.__montar()
        if self.remarcando:
            self.__preencher_para_remarcar()
        for variavel in (self.var_cliente, self.var_profissional, self.var_servico, self.var_data):
            variavel.trace_add("write", lambda *_: self.__atualizar_horarios())
        self.__atualizar_horarios()

        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", lambda _e: self.salvar())
        self.__centralizar()
        try:
            self.grab_set()  # janela modal: bloqueia a principal até fechar
        except tk.TclError:
            pass

    def __montar(self) -> None:
        corpo = ttk.Frame(self, style="Cartao.TFrame", padding=24)
        corpo.pack(fill="both", expand=True, padx=16, pady=16)
        ttk.Label(corpo, text=self.title(), style="CartaoTitulo.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        def rotulo(texto: str, linha: int) -> None:
            ttk.Label(corpo, text=texto, style="CartaoSuave.TLabel").grid(
                row=linha, column=0, sticky="w", padx=(0, 14), pady=6)

        rotulo("Cliente", 1)
        self.combo_cliente = ttk.Combobox(corpo, textvariable=self.var_cliente, state="readonly",
                                          values=list(self.__clientes), width=44)
        self.combo_cliente.grid(row=1, column=1, sticky="ew", pady=6)
        rotulo("Profissional", 2)
        self.combo_profissional = ttk.Combobox(corpo, textvariable=self.var_profissional,
                                               state="readonly", values=list(self.__profissionais),
                                               width=44)
        self.combo_profissional.grid(row=2, column=1, sticky="ew", pady=6)
        rotulo("Serviço", 3)
        self.combo_servico = ttk.Combobox(corpo, textvariable=self.var_servico, state="readonly",
                                          values=list(self.__servicos), width=44)
        self.combo_servico.grid(row=3, column=1, sticky="ew", pady=6)

        rotulo("Data", 4)
        linha_data = ttk.Frame(corpo, style="Cartao.TFrame")
        linha_data.configure(borderwidth=0)
        linha_data.grid(row=4, column=1, sticky="w", pady=6)
        ttk.Button(linha_data, text="<", width=3, command=lambda: self.__mudar_dia(-1)).pack(side="left")
        ttk.Entry(linha_data, textvariable=self.var_data, width=12, justify="center").pack(side="left", padx=4)
        ttk.Button(linha_data, text=">", width=3, command=lambda: self.__mudar_dia(1)).pack(side="left")
        ttk.Label(linha_data, text="   Horário", style="CartaoSuave.TLabel").pack(side="left", padx=(8, 6))
        self.combo_hora = ttk.Combobox(linha_data, textvariable=self.var_hora, state="readonly", width=8)
        self.combo_hora.pack(side="left")
        self.rotulo_livres = ttk.Label(corpo, style="CartaoSuave.TLabel")
        self.rotulo_livres.grid(row=5, column=1, sticky="w")

        rotulo("Observação", 6)
        self.campo_observacao = ttk.Entry(corpo, textvariable=self.var_observacao, width=46)
        self.campo_observacao.grid(row=6, column=1, sticky="ew", pady=6)

        rotulo("Avisar cliente", 7)
        avisos = ttk.Frame(corpo, style="Cartao.TFrame")
        avisos.configure(borderwidth=0)
        avisos.grid(row=7, column=1, sticky="w", pady=6)
        for texto, valor in (("Não avisar", self.SEM_AVISO), ("WhatsApp", self.WHATSAPP),
                             ("E-mail", self.EMAIL)):
            ttk.Radiobutton(avisos, text=texto, value=valor, variable=self.var_aviso,
                            style="Cartao.TRadiobutton").pack(side="left", padx=(0, 14))

        self.rotulo_resumo = ttk.Label(corpo, style="Destaque.TLabel")
        self.rotulo_resumo.grid(row=8, column=0, columnspan=2, sticky="w", pady=(12, 4))

        botoes = ttk.Frame(corpo, style="Cartao.TFrame")
        botoes.configure(borderwidth=0)
        botoes.grid(row=9, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Remarcar" if self.remarcando else "Agendar",
                   style="Primario.TButton", command=self.salvar).pack(side="left")

    def __preencher_para_remarcar(self) -> None:
        ag = self.__agendamento
        self.var_cliente.set(self.__chave_de(self.__clientes, ag.cliente))
        self.var_profissional.set(self.__chave_de(self.__profissionais, ag.profissional))
        self.var_servico.set(self.__chave_de(self.__servicos, ag.servico))
        self.var_observacao.set(ag.observacao)
        for widget in (self.combo_cliente, self.combo_profissional, self.combo_servico,
                       self.campo_observacao):
            widget.configure(state="disabled")

    @staticmethod
    def __chave_de(opcoes: Dict[str, object], objeto) -> str:
        return next((texto for texto, item in opcoes.items() if item is objeto), "")

    def __mudar_dia(self, dias: int) -> None:
        dia = self.__ler_data() or date.today()
        self.var_data.set(f"{dia + timedelta(days=dias):%d/%m/%Y}")

    def __ler_data(self) -> Optional[date]:
        try:
            return datetime.strptime(self.var_data.get().strip(), "%d/%m/%Y").date()
        except ValueError:
            return None

    def __atualizar_horarios(self) -> None:
        cliente = self.__clientes.get(self.var_cliente.get())
        profissional = self.__profissionais.get(self.var_profissional.get())
        servico = self.__servicos.get(self.var_servico.get())
        dia = self.__ler_data()
        if servico is not None:
            self.rotulo_resumo.configure(
                text=f"{servico.TIPO}  •  valor {moeda(servico.calcular_valor())}  •  "
                     f"duração {servico.duracao_min} min")
        if dia is None:
            self.__definir_horarios([], "Data inválida: use dd/mm/aaaa.")
            return
        if profissional is None or servico is None:
            self.__definir_horarios([], "Escolha o profissional e o serviço para ver os horários.")
            return
        livres = self.__clinica.horarios_livres(profissional.id, servico.id, dia,
                                                None if cliente is None else cliente.id)
        texto = (f"{len(livres)} horário(s) livre(s) em {data_por_extenso(dia)}" if livres
                 else f"Nenhum horário livre em {data_por_extenso(dia)}. Tente outro dia.")
        self.__definir_horarios([h.strftime("%H:%M") for h in livres], texto)

    def __definir_horarios(self, horarios: list, texto: str) -> None:
        self.combo_hora.configure(values=horarios)
        if self.var_hora.get() not in horarios:
            self.var_hora.set(horarios[0] if horarios else "")
        self.rotulo_livres.configure(text=texto)

    def salvar(self) -> Optional[Agendamento]:
        try:
            agendamento = self.__gravar()
        except AgendaErro as erro:
            messagebox.showerror(self.title(), str(erro), parent=self)
            return None
        mensagem = str(agendamento)
        canal = {self.WHATSAPP: NotificadorWhatsApp(),
                 self.EMAIL: NotificadorEmail()}.get(self.var_aviso.get())
        if canal is not None:  # POLIMORFISMO: qualquer Notificador serve
            mensagem += "\n\nAviso enviado (simulação):\n" + self.__clinica.notificar(agendamento, canal)
        acao = "remarcado" if self.remarcando else "criado"
        self.destroy()
        self.__principal.atualizar_tudo(f"Agendamento #{agendamento.id} {acao}.")
        self.__principal.mostrar_agendamento(agendamento)
        messagebox.showinfo(f"Agendamento {acao}", mensagem, parent=self.__principal)
        return agendamento

    def __gravar(self) -> Agendamento:
        cliente = self.__clientes.get(self.var_cliente.get())
        profissional = self.__profissionais.get(self.var_profissional.get())
        servico = self.__servicos.get(self.var_servico.get())
        dia = self.__ler_data()
        if cliente is None or profissional is None or servico is None:
            raise DadoInvalidoErro("Escolha o cliente, o profissional e o serviço.")
        if dia is None or not self.var_hora.get():
            raise DadoInvalidoErro("Escolha uma data válida e um horário livre.")
        hora = datetime.strptime(self.var_hora.get(), "%H:%M").time()
        data_hora = datetime.combine(dia, hora)
        if self.remarcando:
            return self.__clinica.remarcar_agendamento(self.__agendamento.id, data_hora)
        return self.__clinica.agendar(cliente.id, profissional.id, servico.id, data_hora,
                                      self.var_observacao.get())

    def __centralizar(self) -> None:
        self.update_idletasks()
        principal = self.__principal
        x = principal.winfo_rootx() + (principal.winfo_width() - self.winfo_reqwidth()) // 2
        y = principal.winfo_rooty() + (principal.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
