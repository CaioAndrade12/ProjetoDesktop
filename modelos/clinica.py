"""
Clínica: a classe central do sistema (as telas só conversam com ela).

Conceitos de OO neste arquivo:
- COMPOSIÇÃO: a Clínica cria a sua Agenda no construtor; a agenda não vive sem ela.
- AGREGAÇÃO (um tipo de associação): a Clínica reúne Clientes, Profissionais e
  Serviços criados FORA dela; eles existem por conta própria.
- ASSOCIAÇÃO: a Clínica guarda uma referência ao BancoDeDados (opcional) e o
  usa para salvar tudo o que muda.
- DEPENDÊNCIA: notificar() recebe um Notificador como parâmetro, usa e não guarda.
- ENCAPSULAMENTO: as coleções são privadas; só se mexe nelas pelos métodos.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from .agenda import Agenda
from .agendamento import Agendamento, StatusAgendamento
from .excecoes import DadoInvalidoErro, OperacaoInvalidaErro, RegistroNaoEncontradoErro
from .notificador import Notificador
from .pessoa import Cliente, Profissional
from .servico import Servico
from .utilitarios import somente_digitos, texto_obrigatorio

if TYPE_CHECKING:
    from banco.banco_dados import BancoDeDados


class Clinica:
    def __init__(self, nome: str, banco: Optional["BancoDeDados"] = None) -> None:
        self.nome = texto_obrigatorio(nome, "Nome da clínica")
        self.__agenda = Agenda()                              # COMPOSIÇÃO
        self.__clientes: Dict[int, Cliente] = {}              # AGREGAÇÃO
        self.__profissionais: Dict[int, Profissional] = {}    # AGREGAÇÃO
        self.__servicos: Dict[int, Servico] = {}              # AGREGAÇÃO
        self.__banco = banco                                  # ASSOCIAÇÃO
        if self.__banco is not None:
            self.__carregar_do_banco()

    @property
    def agenda(self) -> Agenda:
        return self.__agenda

    @property
    def vazia(self) -> bool:
        return not (self.__clientes or self.__profissionais or self.__servicos)

    # ============================ CLIENTES ============================
    def cadastrar_cliente(self, cliente: Cliente) -> Cliente:
        self.__garantir_cpf_unico(cliente.cpf, ignorar=cliente)
        return self.__adicionar(self.__clientes, cliente)

    def editar_cliente(self, id: int, nome: str, telefone: str, cpf: str,
                       email: str = "") -> Cliente:
        cliente = self.buscar_cliente(id)
        self.__garantir_cpf_unico(cpf, ignorar=cliente)
        cliente.atualizar(nome, telefone, email, cpf=cpf)
        self.__salvar(cliente)
        return cliente

    def remover_cliente(self, id: int) -> Cliente:
        cliente = self.buscar_cliente(id)
        self.__garantir_sem_agendamentos(cliente.nome, cliente=cliente)
        return self.__remover(self.__clientes, cliente)

    def buscar_cliente(self, id: int) -> Cliente:
        return self.__buscar(self.__clientes, id, "Cliente")

    def listar_clientes(self, termo: str = "") -> List[Cliente]:
        """Todos os clientes em ordem alfabética, ou só os que batem com o termo."""
        termo = termo.strip().lower()
        digitos = somente_digitos(termo)
        encontrados = [c for c in self.__clientes.values()
                       if not termo or termo in c.nome.lower()
                       or (digitos and digitos in c.cpf)]
        return sorted(encontrados, key=lambda c: c.nome.lower())

    # ========================== PROFISSIONAIS ==========================
    def cadastrar_profissional(self, profissional: Profissional) -> Profissional:
        return self.__adicionar(self.__profissionais, profissional)

    def editar_profissional(self, id: int, nome: str, telefone: str, especialidade: str,
                            email: str = "") -> Profissional:
        profissional = self.buscar_profissional(id)
        profissional.atualizar(nome, telefone, email, especialidade=especialidade)
        self.__salvar(profissional)
        return profissional

    def remover_profissional(self, id: int) -> Profissional:
        profissional = self.buscar_profissional(id)
        self.__garantir_sem_agendamentos(profissional.nome, profissional=profissional)
        return self.__remover(self.__profissionais, profissional)

    def buscar_profissional(self, id: int) -> Profissional:
        return self.__buscar(self.__profissionais, id, "Profissional")

    def listar_profissionais(self, termo: str = "") -> List[Profissional]:
        termo = termo.strip().lower()
        encontrados = [p for p in self.__profissionais.values()
                       if not termo or termo in p.nome.lower()
                       or termo in p.especialidade.lower()]
        return sorted(encontrados, key=lambda p: p.nome.lower())

    # ============================ SERVIÇOS ============================
    def cadastrar_servico(self, servico: Servico) -> Servico:
        return self.__adicionar(self.__servicos, servico)

    def editar_servico(self, id: int, nome: str, preco_base, duracao_min,
                       taxa_material=None) -> Servico:
        servico = self.buscar_servico(id)
        # POLIMORFISMO: o Exame usa a taxa_material; os outros tipos a ignoram
        servico.atualizar(nome, preco_base, duracao_min, taxa_material=taxa_material)
        self.__salvar(servico)
        return servico

    def remover_servico(self, id: int) -> Servico:
        servico = self.buscar_servico(id)
        self.__garantir_sem_agendamentos(servico.nome, servico=servico)
        return self.__remover(self.__servicos, servico)

    def buscar_servico(self, id: int) -> Servico:
        return self.__buscar(self.__servicos, id, "Serviço")

    def listar_servicos(self, termo: str = "") -> List[Servico]:
        termo = termo.strip().lower()
        encontrados = [s for s in self.__servicos.values()
                       if not termo or termo in s.nome.lower() or termo in s.TIPO.lower()]
        return sorted(encontrados, key=lambda s: s.id)

    # ========================== AGENDAMENTOS ==========================
    def agendar(self, id_cliente: int, id_profissional: int, id_servico: int,
                data_hora: datetime, observacao: str = "") -> Agendamento:
        agendamento = self.__agenda.agendar(
            self.buscar_cliente(id_cliente), self.buscar_profissional(id_profissional),
            self.buscar_servico(id_servico), data_hora, observacao)
        self.__salvar(agendamento)
        return agendamento

    def confirmar_agendamento(self, id: int) -> Agendamento:
        agendamento = self.__agenda.buscar(id)
        agendamento.confirmar()
        self.__salvar(agendamento)
        return agendamento

    def concluir_agendamento(self, id: int) -> Agendamento:
        agendamento = self.__agenda.buscar(id)
        agendamento.concluir()
        self.__salvar(agendamento)
        return agendamento

    def cancelar_agendamento(self, id: int) -> Agendamento:
        agendamento = self.__agenda.buscar(id)
        agendamento.cancelar()
        self.__salvar(agendamento)
        return agendamento

    def remarcar_agendamento(self, id: int, nova_data_hora: datetime) -> Agendamento:
        agendamento = self.__agenda.remarcar(id, nova_data_hora)
        self.__salvar(agendamento)
        return agendamento

    def buscar_agendamento(self, id: int) -> Agendamento:
        return self.__agenda.buscar(id)

    def listar_agendamentos(self, dia: Optional[date] = None,
                            id_profissional: Optional[int] = None,
                            id_cliente: Optional[int] = None,
                            status: Optional[StatusAgendamento] = None) -> List[Agendamento]:
        profissional = (None if id_profissional is None
                        else self.buscar_profissional(id_profissional))
        cliente = None if id_cliente is None else self.buscar_cliente(id_cliente)
        return self.__agenda.listar(dia=dia, profissional=profissional,
                                    cliente=cliente, status=status)

    def horarios_livres(self, id_profissional: int, id_servico: int, dia: date,
                        id_cliente: Optional[int] = None) -> List[datetime]:
        cliente = None if id_cliente is None else self.buscar_cliente(id_cliente)
        return self.__agenda.horarios_livres(self.buscar_profissional(id_profissional),
                                             self.buscar_servico(id_servico), dia, cliente)

    def notificar(self, agendamento: Agendamento, notificador: Notificador) -> str:
        """DEPENDÊNCIA: usa o notificador recebido só aqui e não o guarda.
        POLIMORFISMO: funciona com WhatsApp, e-mail ou qualquer outro canal."""
        return notificador.enviar(agendamento)

    # ========================= MÉTODOS PRIVADOS =========================
    def __adicionar(self, colecao: dict, objeto):
        if objeto.id is None or colecao.get(objeto.id, objeto) is not objeto:
            objeto.id = max(colecao, default=0) + 1
        self.__salvar(objeto)
        colecao[objeto.id] = objeto
        return objeto

    def __remover(self, colecao: dict, objeto):
        if self.__banco is not None:
            self.__banco.excluir(objeto)
        del colecao[objeto.id]
        return objeto

    @staticmethod
    def __buscar(colecao: dict, id, nome: str):
        try:
            return colecao[int(id)]
        except (KeyError, ValueError, TypeError):
            raise RegistroNaoEncontradoErro(f"{nome} de código {id} não encontrado.") from None

    def __salvar(self, objeto) -> None:
        if self.__banco is not None:
            self.__banco.salvar(objeto)

    def __garantir_cpf_unico(self, cpf: str, ignorar: Cliente) -> None:
        digitos = somente_digitos(cpf)
        for cliente in self.__clientes.values():
            if cliente.cpf == digitos and cliente is not ignorar:
                raise DadoInvalidoErro(f"Já existe um cliente com este CPF ({cliente.nome}).")

    def __garantir_sem_agendamentos(self, nome: str, **filtro) -> None:
        if self.__agenda.listar(**filtro):
            raise OperacaoInvalidaErro(
                f"{nome} tem agendamentos no histórico e não pode ser removido(a).")

    def __carregar_do_banco(self) -> None:
        for cliente in self.__banco.carregar_clientes():
            self.__clientes[cliente.id] = cliente
        for profissional in self.__banco.carregar_profissionais():
            self.__profissionais[profissional.id] = profissional
        for servico in self.__banco.carregar_servicos():
            self.__servicos[servico.id] = servico
        for dados in self.__banco.carregar_agendamentos():
            self.__agenda.restaurar(
                dados["id"],
                self.__clientes[dados["cliente_id"]],
                self.__profissionais[dados["profissional_id"]],
                self.__servicos[dados["servico_id"]],
                datetime.fromisoformat(dados["data_hora"]),
                dados["observacao"] or "",
                StatusAgendamento[dados["status"]])
