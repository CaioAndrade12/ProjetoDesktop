"""
Menu no TERMINAL (Níveis 2 e 3).

O MenuTerminal só conversa com a Clínica (ASSOCIAÇÃO); todas as regras de
negócio ficam nos modelos. Qualquer erro do sistema é tratado num único lugar
com `except AgendaErro` (POLIMORFISMO das exceções).
"""
from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from typing import Callable, List, Optional, Sequence, Tuple

from modelos import (TIPOS_DE_SERVICO, AgendaErro, Cliente, Clinica, Exame,
                     NotificadorEmail, NotificadorWhatsApp, Profissional, Relatorio,
                     Servico)
from modelos.utilitarios import moeda

LINHA = "=" * 64


class MenuTerminal:
    def __init__(self, clinica: Clinica, banco=None, entrada: Callable[[str], str] = input,
                 interativo: bool = True) -> None:
        self.__clinica = clinica          # ASSOCIAÇÃO
        self.__banco = banco
        self.__entrada = entrada          # função que lê o teclado (trocada nos testes)
        self.__interativo = interativo    # False nos testes: não limpa a tela nem pausa

    # =========================== MENUS ===========================
    def executar(self) -> None:
        self.__menu("MENU PRINCIPAL", [
            ("Clientes", self.__menu_clientes, True),
            ("Profissionais", self.__menu_profissionais, True),
            ("Serviços", self.__menu_servicos, True),
            ("Agendamentos", self.__menu_agendamentos, True),
            ("Relatório", self.__mostrar_relatorio, False),
            ("Banco de dados", self.__mostrar_banco, False),
        ], texto_sair="Sair")
        print("\nAté logo!")

    def __menu(self, titulo: str, opcoes: Sequence[Tuple[str, Callable, bool]],
               texto_sair: str = "Voltar") -> None:
        """Laço genérico: mostra as opções, executa a escolhida e trata os erros."""
        while True:
            self.__limpar_tela()
            print(LINHA)
            print(f"  {self.__clinica.nome.upper()}  >  {titulo}")
            print(LINHA)
            for numero, (rotulo, _, _) in enumerate(opcoes, start=1):
                print(f"  {numero}. {rotulo}")
            print(f"  0. {texto_sair}")
            escolha = self.__entrada("\nEscolha uma opção: ").strip()
            if escolha == "0":
                return
            if not (escolha.isdigit() and 1 <= int(escolha) <= len(opcoes)):
                print("Opção inválida.")
                self.__pausar()
                continue
            rotulo, acao, e_submenu = opcoes[int(escolha) - 1]
            if e_submenu:
                acao()
                continue
            print(f"\n--- {rotulo.upper()} ---")
            try:
                acao()
            except AgendaErro as erro:  # pega QUALQUER erro do sistema (polimorfismo)
                print(f"\n[ERRO] {erro}")
            self.__pausar()

    def __menu_clientes(self) -> None:
        self.__menu("CLIENTES", [
            ("Cadastrar cliente", self.__cadastrar_cliente, False),
            ("Listar clientes", self.__listar_clientes, False),
            ("Pesquisar por nome ou CPF", self.__pesquisar_clientes, False),
            ("Editar cliente", self.__editar_cliente, False),
            ("Remover cliente", self.__remover_cliente, False),
        ])

    def __menu_profissionais(self) -> None:
        self.__menu("PROFISSIONAIS", [
            ("Cadastrar profissional", self.__cadastrar_profissional, False),
            ("Listar profissionais", self.__listar_profissionais, False),
            ("Editar profissional", self.__editar_profissional, False),
            ("Remover profissional", self.__remover_profissional, False),
        ])

    def __menu_servicos(self) -> None:
        self.__menu("SERVIÇOS", [
            ("Cadastrar serviço", self.__cadastrar_servico, False),
            ("Listar serviços", self.__listar_servicos, False),
            ("Editar serviço", self.__editar_servico, False),
            ("Remover serviço", self.__remover_servico, False),
        ])

    def __menu_agendamentos(self) -> None:
        self.__menu("AGENDAMENTOS", [
            ("Novo agendamento", self.__novo_agendamento, False),
            ("Agenda do dia", self.__agenda_do_dia, False),
            ("Todos os agendamentos", self.__todos_agendamentos, False),
            ("Ver horários livres", self.__ver_horarios_livres, False),
            ("Confirmar agendamento", self.__confirmar_agendamento, False),
            ("Concluir atendimento", self.__concluir_agendamento, False),
            ("Cancelar agendamento", self.__cancelar_agendamento, False),
            ("Remarcar agendamento", self.__remarcar_agendamento, False),
        ])

    # =========================== CLIENTES ===========================
    def __cadastrar_cliente(self) -> None:
        cliente = Cliente(self.__ler("Nome: "), self.__ler("Telefone com DDD: "),
                          self.__ler("CPF: "), self.__ler("E-mail (opcional): ", obrigatorio=False))
        self.__clinica.cadastrar_cliente(cliente)  # AGREGAÇÃO: criado aqui, entregue à clínica
        print(f"\nCliente cadastrado com o código {cliente.id}.")

    def __listar_clientes(self, termo: str = "") -> None:
        self.__tabela(["Cód", "Nome", "CPF", "Telefone", "E-mail"],
                      [(c.id, c.nome, c.cpf_formatado, c.contato.telefone_formatado,
                        c.contato.email or "-") for c in self.__clinica.listar_clientes(termo)])

    def __pesquisar_clientes(self) -> None:
        self.__listar_clientes(self.__ler("Digite parte do nome ou do CPF: "))

    def __editar_cliente(self) -> None:
        cliente = self.__escolher_cliente()
        print("(Enter mantém o valor atual; '-' apaga o e-mail)")
        self.__clinica.editar_cliente(
            cliente.id,
            self.__ler(f"Nome [{cliente.nome}]: ", padrao=cliente.nome),
            self.__ler(f"Telefone [{cliente.contato.telefone_formatado}]: ",
                       padrao=cliente.contato.telefone),
            self.__ler(f"CPF [{cliente.cpf_formatado}]: ", padrao=cliente.cpf),
            self.__ler(f"E-mail [{cliente.contato.email or '-'}]: ",
                       obrigatorio=False, padrao=cliente.contato.email))
        print("\nCliente atualizado:", cliente)

    def __remover_cliente(self) -> None:
        cliente = self.__escolher_cliente()
        if self.__sim_ou_nao(f"Remover {cliente.nome}?"):
            self.__clinica.remover_cliente(cliente.id)
            print("Cliente removido.")

    # ========================= PROFISSIONAIS =========================
    def __cadastrar_profissional(self) -> None:
        profissional = Profissional(self.__ler("Nome: "), self.__ler("Telefone com DDD: "),
                                    self.__ler("Especialidade: "),
                                    self.__ler("E-mail (opcional): ", obrigatorio=False))
        self.__clinica.cadastrar_profissional(profissional)
        print(f"\nProfissional cadastrado com o código {profissional.id}.")

    def __listar_profissionais(self) -> None:
        self.__tabela(["Cód", "Nome", "Especialidade", "Telefone", "E-mail"],
                      [(p.id, p.nome, p.especialidade, p.contato.telefone_formatado,
                        p.contato.email or "-") for p in self.__clinica.listar_profissionais()])

    def __editar_profissional(self) -> None:
        profissional = self.__escolher_profissional()
        print("(Enter mantém o valor atual; '-' apaga o e-mail)")
        self.__clinica.editar_profissional(
            profissional.id,
            self.__ler(f"Nome [{profissional.nome}]: ", padrao=profissional.nome),
            self.__ler(f"Telefone [{profissional.contato.telefone_formatado}]: ",
                       padrao=profissional.contato.telefone),
            self.__ler(f"Especialidade [{profissional.especialidade}]: ",
                       padrao=profissional.especialidade),
            self.__ler(f"E-mail [{profissional.contato.email or '-'}]: ",
                       obrigatorio=False, padrao=profissional.contato.email))
        print("\nProfissional atualizado:", profissional)

    def __remover_profissional(self) -> None:
        profissional = self.__escolher_profissional()
        if self.__sim_ou_nao(f"Remover {profissional.nome}?"):
            self.__clinica.remover_profissional(profissional.id)
            print("Profissional removido.")

    # =========================== SERVIÇOS ===========================
    def __cadastrar_servico(self) -> None:
        print("Tipos: " + "  ".join(f"{i}. {t}" for i, t in enumerate(TIPOS_DE_SERVICO, 1))
              + "   (Exame soma taxa de material; Retorno tem 50% de desconto)")
        tipo = TIPOS_DE_SERVICO[self.__ler_opcao("Tipo: ", 1, len(TIPOS_DE_SERVICO)) - 1]
        nome = self.__ler("Nome do serviço: ")
        preco = self.__ler("Preço base (R$): ")
        duracao = self.__ler("Duração em minutos: ")
        taxa = self.__ler("Taxa de material (R$): ") if tipo == "Exame" else 0
        servico = Servico.criar(tipo, nome, preco, duracao, taxa)  # FÁBRICA
        self.__clinica.cadastrar_servico(servico)
        print(f"\n{servico.TIPO} cadastrado(a) com o código {servico.id}. "
              f"Valor cobrado: {moeda(servico.calcular_valor())}")  # POLIMORFISMO

    def __listar_servicos(self) -> None:
        self.__tabela(["Cód", "Tipo", "Nome", "Preço base", "Valor cobrado", "Duração"],
                      [(s.id, s.TIPO, s.nome, moeda(s.preco_base), moeda(s.calcular_valor()),
                        f"{s.duracao_min} min") for s in self.__clinica.listar_servicos()])

    def __editar_servico(self) -> None:
        servico = self.__escolher_servico()
        print("(Enter mantém o valor atual)")
        nome = self.__ler(f"Nome [{servico.nome}]: ", padrao=servico.nome)
        preco = self.__ler(f"Preço base [{servico.preco_base:.2f}]: ", padrao=servico.preco_base)
        duracao = self.__ler(f"Duração [{servico.duracao_min}]: ", padrao=servico.duracao_min)
        taxa = None
        if isinstance(servico, Exame):
            taxa = self.__ler(f"Taxa de material [{servico.taxa_material:.2f}]: ",
                              padrao=servico.taxa_material)
        self.__clinica.editar_servico(servico.id, nome, preco, duracao, taxa)
        print("\nServiço atualizado:", servico)

    def __remover_servico(self) -> None:
        servico = self.__escolher_servico()
        if self.__sim_ou_nao(f"Remover {servico.nome}?"):
            self.__clinica.remover_servico(servico.id)
            print("Serviço removido.")

    # ========================= AGENDAMENTOS =========================
    def __novo_agendamento(self) -> None:
        cliente = self.__escolher_cliente()
        profissional = self.__escolher_profissional()
        servico = self.__escolher_servico()
        amanha = date.today() + timedelta(days=1)
        dia = self.__ler_data(f"Data (dd/mm/aaaa) [Enter = amanhã, {amanha:%d/%m/%Y}]: ", amanha)
        livres = self.__clinica.horarios_livres(profissional.id, servico.id, dia, cliente.id)
        if not livres:
            print("Não há horários livres nesse dia para esse profissional.")
            return
        print("Horários livres: " + "  ".join(h.strftime("%H:%M") for h in livres))
        hora = self.__ler_hora("Horário (HH:MM): ")
        observacao = self.__ler("Observação (opcional): ", obrigatorio=False)
        agendamento = self.__clinica.agendar(cliente.id, profissional.id, servico.id,
                                             datetime.combine(dia, hora), observacao)
        print(f"\nAgendamento criado!\n{agendamento}")
        self.__oferecer_aviso(agendamento)

    def __oferecer_aviso(self, agendamento) -> None:
        print("\nEnviar aviso ao cliente?  1. WhatsApp  2. E-mail  0. Não enviar")
        escolha = self.__ler_opcao("Opção: ", 0, 2)
        canais = {1: NotificadorWhatsApp(), 2: NotificadorEmail()}
        if escolha in canais:
            # POLIMORFISMO + DEPENDÊNCIA: a clínica usa o canal escolhido sem saber qual é
            print(self.__clinica.notificar(agendamento, canais[escolha]))

    def __agenda_do_dia(self) -> None:
        dia = self.__ler_data(f"Data (dd/mm/aaaa) [Enter = hoje, {date.today():%d/%m/%Y}]: ",
                              date.today())
        print(f"\nAgenda de {dia:%d/%m/%Y}:")
        self.__tabela_agendamentos(self.__clinica.listar_agendamentos(dia=dia), com_data=False)

    def __todos_agendamentos(self) -> None:
        self.__tabela_agendamentos(list(self.__clinica.agenda))

    def __ver_horarios_livres(self) -> None:
        profissional = self.__escolher_profissional()
        servico = self.__escolher_servico()
        amanha = date.today() + timedelta(days=1)
        dia = self.__ler_data(f"Data (dd/mm/aaaa) [Enter = amanhã, {amanha:%d/%m/%Y}]: ", amanha)
        livres = self.__clinica.horarios_livres(profissional.id, servico.id, dia)
        print(f"\nLivres para {profissional.nome} em {dia:%d/%m/%Y}: "
              + ("  ".join(h.strftime("%H:%M") for h in livres) or "nenhum"))

    def __confirmar_agendamento(self) -> None:
        agendamento = self.__clinica.confirmar_agendamento(self.__escolher_agendamento_ativo())
        print("\nConfirmado:", agendamento)

    def __concluir_agendamento(self) -> None:
        agendamento = self.__clinica.concluir_agendamento(self.__escolher_agendamento_ativo())
        print("\nConcluído:", agendamento)

    def __cancelar_agendamento(self) -> None:
        agendamento = self.__clinica.cancelar_agendamento(self.__escolher_agendamento_ativo())
        print("\nCancelado:", agendamento)

    def __remarcar_agendamento(self) -> None:
        agendamento = self.__clinica.buscar_agendamento(self.__escolher_agendamento_ativo())
        dia = self.__ler_data("Nova data (dd/mm/aaaa): ", None)
        livres = self.__clinica.horarios_livres(agendamento.profissional.id,
                                                agendamento.servico.id, dia)
        print("Horários livres: " + ("  ".join(h.strftime("%H:%M") for h in livres) or "nenhum"))
        hora = self.__ler_hora("Novo horário (HH:MM): ")
        self.__clinica.remarcar_agendamento(agendamento.id, datetime.combine(dia, hora))
        print("\nRemarcado:", agendamento)
        self.__oferecer_aviso(agendamento)

    # ====================== RELATÓRIO E BANCO ======================
    def __mostrar_relatorio(self) -> None:
        relatorio = Relatorio(f"Relatório - {self.__clinica.nome}")
        print(relatorio.gerar_texto(self.__clinica.agenda))  # DEPENDÊNCIA: agenda como parâmetro

    def __mostrar_banco(self) -> None:
        if self.__banco is None:
            print("Rodando sem banco de dados (os dados ficam só na memória).")
            return
        print(f"Arquivo SQLite: {self.__banco.caminho}")
        for tabela in self.__banco.nomes_tabelas():
            colunas, linhas = self.__banco.consultar_tabela(tabela)
            print(f"\nSELECT * FROM {tabela};  ->  {len(linhas)} registro(s)")
            self.__tabela(colunas, linhas, mostrar_total=False)

    # ===================== escolhas reaproveitadas =====================
    def __escolher_cliente(self) -> Cliente:
        self.__listar_clientes()
        return self.__clinica.buscar_cliente(self.__ler_inteiro("\nCódigo do cliente: "))

    def __escolher_profissional(self) -> Profissional:
        self.__listar_profissionais()
        return self.__clinica.buscar_profissional(self.__ler_inteiro("\nCódigo do profissional: "))

    def __escolher_servico(self) -> Servico:
        self.__listar_servicos()
        return self.__clinica.buscar_servico(self.__ler_inteiro("\nCódigo do serviço: "))

    def __escolher_agendamento_ativo(self) -> int:
        ativos = [ag for ag in self.__clinica.agenda if ag.ativo]
        self.__tabela_agendamentos(ativos)
        return self.__ler_inteiro("\nCódigo do agendamento: ")

    def __tabela_agendamentos(self, agendamentos, com_data: bool = True) -> None:
        cabecalho = ["Cód"] + (["Data"] if com_data else []) + [
            "Horário", "Cliente", "Profissional", "Serviço", "Valor", "Status"]
        linhas = []
        for ag in agendamentos:
            linha = [ag.id] + ([f"{ag.data_hora:%d/%m/%Y}"] if com_data else [])
            linha += [f"{ag.data_hora:%H:%M}-{ag.fim:%H:%M}", ag.cliente.nome,
                      ag.profissional.nome, ag.servico.nome, moeda(ag.valor), ag.status.value]
            linhas.append(linha)
        self.__tabela(cabecalho, linhas)

    # ======================= leitura do teclado =======================
    def __ler(self, rotulo: str, obrigatorio: bool = True, padrao=None):
        while True:
            valor = self.__entrada(rotulo).strip()
            if valor == "-" and not obrigatorio:
                return ""
            if not valor and padrao is not None:
                return padrao
            if valor or not obrigatorio:
                return valor
            print("  Campo obrigatório.")

    def __ler_inteiro(self, rotulo: str) -> int:
        while True:
            valor = self.__entrada(rotulo).strip()
            if valor.isdigit():
                return int(valor)
            print("  Digite um número.")

    def __ler_opcao(self, rotulo: str, minimo: int, maximo: int) -> int:
        while True:
            valor = self.__entrada(rotulo).strip()
            if valor.isdigit() and minimo <= int(valor) <= maximo:
                return int(valor)
            print(f"  Escolha um número de {minimo} a {maximo}.")

    def __ler_data(self, rotulo: str, padrao: Optional[date]) -> date:
        while True:
            valor = self.__entrada(rotulo).strip()
            if not valor and padrao is not None:
                return padrao
            try:
                return datetime.strptime(valor, "%d/%m/%Y").date()
            except ValueError:
                print("  Use o formato dd/mm/aaaa (ex.: 25/12/2026).")

    def __ler_hora(self, rotulo: str) -> time:
        while True:
            valor = self.__entrada(rotulo).strip()
            try:
                return datetime.strptime(valor, "%H:%M").time()
            except ValueError:
                print("  Use o formato HH:MM (ex.: 14:30).")

    def __sim_ou_nao(self, pergunta: str) -> bool:
        return self.__entrada(f"{pergunta} (s/n): ").strip().lower().startswith("s")

    # ============================ saída ============================
    @staticmethod
    def __tabela(cabecalhos: Sequence, linhas: List[Sequence], mostrar_total: bool = True) -> None:
        if not linhas:
            print("(nenhum registro)")
            return
        textos = [["-" if celula is None else str(celula) for celula in linha] for linha in linhas]
        larguras = [max([len(str(cab))] + [len(linha[i]) for linha in textos])
                    for i, cab in enumerate(cabecalhos)]

        def formatar(celulas) -> str:
            return " | ".join(str(c).ljust(larguras[i]) for i, c in enumerate(celulas))

        print(formatar(cabecalhos))
        print("-+-".join("-" * largura for largura in larguras))
        for linha in textos:
            print(formatar(linha))
        if mostrar_total:
            print(f"Total: {len(linhas)} registro(s)")

    def __limpar_tela(self) -> None:
        if self.__interativo:
            os.system("cls" if os.name == "nt" else "clear")

    def __pausar(self) -> None:
        if self.__interativo:
            self.__entrada("\nPressione ENTER para continuar...")
