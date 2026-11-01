"""
Avisos ao cliente (envio SIMULADO: a mensagem é montada e guardada no histórico).

Conceitos de OO neste arquivo:
- CLASSE ABSTRATA + HERANÇA: NotificadorWhatsApp e NotificadorEmail.
- POLIMORFISMO: cada canal monta e "envia" a mensagem do seu jeito, mas quem
  usa só chama notificador.enviar(agendamento).
- DEPENDÊNCIA: o notificador recebe o Agendamento como PARÂMETRO de enviar(),
  usa e esquece — não guarda o agendamento como atributo.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class Notificador(ABC):
    CANAL = "Notificação"

    def __init__(self) -> None:
        self.__historico: List[str] = []

    @property
    def historico(self) -> List[str]:
        return list(self.__historico)  # devolve uma CÓPIA (encapsulamento)

    @abstractmethod
    def enviar(self, agendamento) -> str:
        """Envia o aviso do agendamento e devolve o texto enviado."""

    def _registrar(self, mensagem: str) -> str:
        """Método PROTEGIDO: usado pelas filhas para guardar o que enviaram."""
        self.__historico.append(mensagem)
        return mensagem


class NotificadorWhatsApp(Notificador):
    CANAL = "WhatsApp"

    def enviar(self, agendamento) -> str:
        cliente = agendamento.cliente
        return self._registrar(
            f"[WhatsApp para {cliente.contato.telefone_formatado}] "
            f"Olá, {cliente.primeiro_nome}! Seu horário de {agendamento.servico.nome} "
            f"com {agendamento.profissional.nome} ficou para "
            f"{agendamento.data_hora:%d/%m às %H:%M}.")


class NotificadorEmail(Notificador):
    CANAL = "E-mail"

    def enviar(self, agendamento) -> str:
        cliente = agendamento.cliente
        if not cliente.contato.email:
            return self._registrar(
                f"[E-mail NÃO enviado] {cliente.nome} não tem e-mail cadastrado.")
        return self._registrar(
            f"[E-mail para {cliente.contato.email}] Assunto: Confirmação de agendamento. "
            f"Prezado(a) {cliente.nome}, confirmamos {agendamento.servico.nome} com "
            f"{agendamento.profissional.nome} em {agendamento.data_hora:%d/%m/%Y às %H:%M}.")
