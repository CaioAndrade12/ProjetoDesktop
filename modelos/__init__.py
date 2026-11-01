"""Camada de MODELOS: as classes de negócio do sistema de agendamento."""
from .excecoes import (AgendaErro, DadoInvalidoErro, HorarioIndisponivelErro,
                       OperacaoInvalidaErro, RegistroNaoEncontradoErro)
from .pessoa import Cliente, Contato, Pessoa, Profissional
from .servico import TIPOS_DE_SERVICO, Consulta, Exame, Retorno, Servico
from .agendamento import Agendamento, StatusAgendamento
from .agenda import Agenda
from .notificador import Notificador, NotificadorEmail, NotificadorWhatsApp
from .relatorio import Relatorio
from .clinica import Clinica

__all__ = [
    "AgendaErro", "DadoInvalidoErro", "HorarioIndisponivelErro", "OperacaoInvalidaErro",
    "RegistroNaoEncontradoErro", "Pessoa", "Contato", "Cliente", "Profissional",
    "Servico", "Consulta", "Exame", "Retorno", "TIPOS_DE_SERVICO", "Agendamento",
    "StatusAgendamento", "Agenda", "Notificador", "NotificadorEmail",
    "NotificadorWhatsApp", "Relatorio", "Clinica",
]
