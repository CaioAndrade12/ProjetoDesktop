"""
Agendamento (um horário marcado).

Conceitos de OO neste arquivo:
- ASSOCIAÇÃO: o Agendamento liga um Cliente, um Profissional e um Servico que
  já existem; ele só guarda a referência a esses objetos.
- ENCAPSULAMENTO: o status só muda pelos métodos confirmar/concluir/cancelar/
  remarcar, que aplicam as regras de negócio.
- ENUM: StatusAgendamento.
- SOBRECARGA DE OPERADORES: __lt__ (permite ordenar com sorted) e __str__.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from .excecoes import OperacaoInvalidaErro
from .utilitarios import moeda

if TYPE_CHECKING:  # usado só nas dicas de tipo
    from .pessoa import Cliente, Profissional
    from .servico import Servico


class StatusAgendamento(Enum):
    AGENDADO = "Agendado"
    CONFIRMADO = "Confirmado"
    CONCLUIDO = "Concluído"
    CANCELADO = "Cancelado"


class Agendamento:
    """Um atendimento marcado na agenda.

    ASSOCIAÇÃO: Cliente, Profissional e Servico são criados fora daqui e
    continuam existindo mesmo se o agendamento for cancelado.
    Quem cria agendamentos é a Agenda (COMPOSIÇÃO), nunca as telas.
    """

    def __init__(self, id: int, cliente: "Cliente", profissional: "Profissional",
                 servico: "Servico", data_hora: datetime, observacao: str = "",
                 status: StatusAgendamento = StatusAgendamento.AGENDADO) -> None:
        self.__id = id
        self.__cliente = cliente            # ASSOCIAÇÃO
        self.__profissional = profissional  # ASSOCIAÇÃO
        self.__servico = servico            # ASSOCIAÇÃO
        self.__data_hora = data_hora.replace(second=0, microsecond=0)
        self.__status = status
        self.observacao = observacao

    # ---------- somente leitura (sem setter = ninguém altera por fora) ----------
    @property
    def id(self) -> int:
        return self.__id

    @property
    def cliente(self) -> "Cliente":
        return self.__cliente

    @property
    def profissional(self) -> "Profissional":
        return self.__profissional

    @property
    def servico(self) -> "Servico":
        return self.__servico

    @property
    def data_hora(self) -> datetime:
        return self.__data_hora

    @property
    def status(self) -> StatusAgendamento:
        return self.__status

    @property
    def observacao(self) -> str:
        return self.__observacao

    @observacao.setter
    def observacao(self, valor: str) -> None:
        self.__observacao = " ".join(str(valor or "").split())

    @property
    def fim(self) -> datetime:
        return self.__data_hora + timedelta(minutes=self.__servico.duracao_min)

    @property
    def valor(self) -> float:
        """POLIMORFISMO: funciona para Consulta, Exame ou Retorno sem saber o tipo."""
        return self.__servico.calcular_valor()

    @property
    def ativo(self) -> bool:
        return self.__status in (StatusAgendamento.AGENDADO, StatusAgendamento.CONFIRMADO)

    def conflita_com(self, inicio: datetime, fim: datetime) -> bool:
        """True se este agendamento (ativo) ocupa parte do intervalo [inicio, fim)."""
        return self.ativo and inicio < self.fim and fim > self.__data_hora

    # ---------- mudanças de status (regras de negócio) ----------
    def confirmar(self) -> None:
        self.__exigir_status("confirmar", StatusAgendamento.AGENDADO)
        self.__status = StatusAgendamento.CONFIRMADO

    def concluir(self) -> None:
        self.__exigir_status("concluir", StatusAgendamento.AGENDADO,
                             StatusAgendamento.CONFIRMADO)
        self.__status = StatusAgendamento.CONCLUIDO

    def cancelar(self) -> None:
        self.__exigir_status("cancelar", StatusAgendamento.AGENDADO,
                             StatusAgendamento.CONFIRMADO)
        self.__status = StatusAgendamento.CANCELADO

    def remarcar(self, nova_data_hora: datetime) -> None:
        """Muda o horário. A Agenda confere antes se o novo horário está livre."""
        self.__exigir_status("remarcar", StatusAgendamento.AGENDADO,
                             StatusAgendamento.CONFIRMADO)
        self.__data_hora = nova_data_hora.replace(second=0, microsecond=0)
        self.__status = StatusAgendamento.AGENDADO  # precisa ser confirmado de novo

    def __exigir_status(self, acao: str, *permitidos: StatusAgendamento) -> None:
        """Método PRIVADO: só a própria classe usa."""
        if self.__status not in permitidos:
            raise OperacaoInvalidaErro(
                f"Não é possível {acao}: o agendamento #{self.__id} "
                f"está '{self.__status.value}'.")

    def para_dict(self) -> dict:
        return {"id": self.__id,
                "cliente_id": self.__cliente.id,
                "profissional_id": self.__profissional.id,
                "servico_id": self.__servico.id,
                "data_hora": self.__data_hora.isoformat(sep=" ", timespec="minutes"),
                "status": self.__status.name,
                "observacao": self.__observacao}

    # ---------- SOBRECARGA DE OPERADORES ----------
    def __lt__(self, outro: "Agendamento") -> bool:
        """Permite sorted(lista_de_agendamentos): ordena por data e hora."""
        return (self.__data_hora, self.__id) < (outro.data_hora, outro.id)

    def __str__(self) -> str:
        return (f"#{self.__id} {self.__data_hora:%d/%m/%Y %H:%M}-{self.fim:%H:%M} | "
                f"{self.__cliente.nome} com {self.__profissional.nome} | "
                f"{self.__servico.nome} | {moeda(self.valor)} | {self.__status.value}")
