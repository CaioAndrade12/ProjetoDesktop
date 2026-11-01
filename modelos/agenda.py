"""
Agenda: onde ficam os agendamentos e as regras de horário.

Conceitos de OO neste arquivo:
- COMPOSIÇÃO: a Agenda CRIA e GUARDA os Agendamentos. Eles nascem dentro de
  agendar() e não existem fora da agenda.
- ATRIBUTOS DE CLASSE: horário de funcionamento (iguais para todas as agendas).
- MÉTODOS PRIVADOS: regras internas (__validar_horario, __verificar_conflitos).
- SOBRECARGA DE OPERADORES: __len__ e __iter__ (len(agenda) e for ag in agenda).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Dict, Iterator, List, Optional

from .agendamento import Agendamento, StatusAgendamento
from .excecoes import HorarioIndisponivelErro, RegistroNaoEncontradoErro


class Agenda:
    ABERTURA = time(8, 0)     # ATRIBUTOS DE CLASSE
    FECHAMENTO = time(18, 0)
    INTERVALO_MIN = 30        # horários sugeridos de 30 em 30 minutos

    def __init__(self) -> None:
        self.__agendamentos: Dict[int, Agendamento] = {}

    # ---------------- criação (COMPOSIÇÃO) ----------------
    def agendar(self, cliente, profissional, servico, data_hora: datetime,
                observacao: str = "") -> Agendamento:
        inicio = data_hora.replace(second=0, microsecond=0)
        self.__validar_horario(inicio, servico.duracao_min)
        self.__verificar_conflitos(cliente, profissional, inicio, servico.duracao_min)
        novo_id = max(self.__agendamentos, default=0) + 1
        agendamento = Agendamento(novo_id, cliente, profissional, servico,
                                  inicio, observacao)  # o agendamento nasce AQUI
        self.__agendamentos[novo_id] = agendamento
        return agendamento

    def restaurar(self, id: int, cliente, profissional, servico, data_hora: datetime,
                  observacao: str, status: StatusAgendamento) -> Agendamento:
        """Recria um agendamento lido do banco (já foi validado quando foi criado)."""
        agendamento = Agendamento(id, cliente, profissional, servico,
                                  data_hora, observacao, status)
        self.__agendamentos[id] = agendamento
        return agendamento

    def remarcar(self, id: int, nova_data_hora: datetime) -> Agendamento:
        agendamento = self.buscar(id)
        inicio = nova_data_hora.replace(second=0, microsecond=0)
        if agendamento.ativo:  # se não estiver ativo, o próprio agendamento recusa
            duracao = agendamento.servico.duracao_min
            self.__validar_horario(inicio, duracao)
            self.__verificar_conflitos(agendamento.cliente, agendamento.profissional,
                                       inicio, duracao, ignorar=agendamento)
        agendamento.remarcar(inicio)
        return agendamento

    # ---------------- consultas ----------------
    def buscar(self, id: int) -> Agendamento:
        try:
            return self.__agendamentos[int(id)]
        except (KeyError, ValueError, TypeError):
            raise RegistroNaoEncontradoErro(f"Agendamento #{id} não encontrado.") from None

    def listar(self, dia: Optional[date] = None, profissional=None, cliente=None,
               servico=None, status: Optional[StatusAgendamento] = None) -> List[Agendamento]:
        """Lista com filtros opcionais, em ordem de data (usa o __lt__)."""
        resultado = [
            ag for ag in self.__agendamentos.values()
            if (dia is None or ag.data_hora.date() == dia)
            and (profissional is None or ag.profissional is profissional)
            and (cliente is None or ag.cliente is cliente)
            and (servico is None or ag.servico is servico)
            and (status is None or ag.status is status)
        ]
        return sorted(resultado)

    def horarios_livres(self, profissional, servico, dia: date,
                        cliente=None) -> List[datetime]:
        """Horários do dia em que o profissional (e o cliente) estão livres."""
        livres = []
        agora = datetime.now()
        duracao = timedelta(minutes=servico.duracao_min)
        inicio = datetime.combine(dia, self.ABERTURA)
        limite = datetime.combine(dia, self.FECHAMENTO)
        while inicio + duracao <= limite:
            ocupado = any(
                ag.conflita_com(inicio, inicio + duracao)
                and (ag.profissional is profissional or ag.cliente is cliente)
                for ag in self.__agendamentos.values())
            if inicio > agora and not ocupado:
                livres.append(inicio)
            inicio += timedelta(minutes=self.INTERVALO_MIN)
        return livres

    def __len__(self) -> int:
        return len(self.__agendamentos)

    def __iter__(self) -> Iterator[Agendamento]:
        return iter(sorted(self.__agendamentos.values()))

    # ---------------- regras (métodos PRIVADOS) ----------------
    def __validar_horario(self, inicio: datetime, duracao_min: int) -> None:
        if inicio < datetime.now():
            raise HorarioIndisponivelErro("Não é possível agendar em data/hora que já passou.")
        fim = inicio + timedelta(minutes=duracao_min)
        if (inicio.time() < self.ABERTURA or fim.date() != inicio.date()
                or fim.time() > self.FECHAMENTO):
            raise HorarioIndisponivelErro(
                f"Fora do expediente: atendimentos das {self.ABERTURA:%H:%M} "
                f"às {self.FECHAMENTO:%H:%M}.")

    def __verificar_conflitos(self, cliente, profissional, inicio: datetime,
                              duracao_min: int, ignorar: Optional[Agendamento] = None) -> None:
        fim = inicio + timedelta(minutes=duracao_min)
        for ag in self.__agendamentos.values():
            if ag is ignorar or not ag.conflita_com(inicio, fim):
                continue
            if ag.profissional is profissional:
                raise HorarioIndisponivelErro(
                    f"{profissional.nome} já tem atendimento das "
                    f"{ag.data_hora:%H:%M} às {ag.fim:%H:%M}.")
            if ag.cliente is cliente:
                raise HorarioIndisponivelErro(
                    f"{cliente.nome} já tem outro horário das "
                    f"{ag.data_hora:%H:%M} às {ag.fim:%H:%M}.")
