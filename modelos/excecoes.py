"""
Exceções personalizadas do sistema.

Conceito de OO: HERANÇA. Todas herdam de AgendaErro, que herda de Exception.
Assim, as telas podem tratar qualquer erro do sistema com um único
`except AgendaErro` (POLIMORFISMO: a filha é tratada como a mãe).
"""


class AgendaErro(Exception):
    """Exceção base do sistema de agendamento."""


class DadoInvalidoErro(AgendaErro):
    """Um dado informado não passou na validação (nome, CPF, preço...)."""


class RegistroNaoEncontradoErro(AgendaErro):
    """O código (id) procurado não existe."""


class HorarioIndisponivelErro(AgendaErro):
    """O horário já está ocupado, já passou ou está fora do expediente."""


class OperacaoInvalidaErro(AgendaErro):
    """A ação não é permitida (ex.: cancelar um atendimento já concluído)."""
