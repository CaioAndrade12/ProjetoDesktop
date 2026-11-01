"""
Relatórios da agenda.

Conceito de OO: DEPENDÊNCIA. O Relatorio recebe a agenda como PARÂMETRO de cada
método e só a usa durante o cálculo; ele não guarda a agenda como atributo.
Funciona com qualquer coleção de agendamentos (a agenda inteira ou uma lista
filtrada), pois só precisa percorrê-la com `for` (duck typing).
"""
from __future__ import annotations

from typing import Dict, List

from .agendamento import StatusAgendamento
from .utilitarios import moeda


class Relatorio:
    def __init__(self, titulo: str = "Relatório da agenda") -> None:
        self.titulo = titulo

    def total_por_status(self, agenda) -> Dict[str, int]:
        totais = {status.value: 0 for status in StatusAgendamento}
        for ag in agenda:
            totais[ag.status.value] += 1
        return totais

    def faturamento_realizado(self, agenda) -> float:
        """Soma dos atendimentos concluídos."""
        return round(sum(ag.valor for ag in agenda
                         if ag.status is StatusAgendamento.CONCLUIDO), 2)

    def faturamento_previsto(self, agenda) -> float:
        """Soma dos agendamentos ainda em aberto (agendados + confirmados)."""
        return round(sum(ag.valor for ag in agenda if ag.ativo), 2)

    def por_profissional(self, agenda) -> List[dict]:
        resumo: Dict[str, dict] = {}
        for ag in agenda:
            nome = ag.profissional.nome
            linha = resumo.setdefault(nome, {"profissional": nome, "em_aberto": 0,
                                             "concluidos": 0, "faturado": 0.0})
            if ag.ativo:
                linha["em_aberto"] += 1
            elif ag.status is StatusAgendamento.CONCLUIDO:
                linha["concluidos"] += 1
                linha["faturado"] = round(linha["faturado"] + ag.valor, 2)
        return sorted(resumo.values(), key=lambda l: (-l["faturado"], l["profissional"]))

    def gerar_texto(self, agenda) -> str:
        agendamentos = list(agenda)
        status = self.total_por_status(agendamentos)
        linhas = [
            "=" * 60,
            f"  {self.titulo.upper()}",
            "=" * 60,
            f"Total de agendamentos: {len(agendamentos)}",
            "  " + " | ".join(f"{nome}: {qtd}" for nome, qtd in status.items()),
            f"Faturamento realizado (concluídos): {moeda(self.faturamento_realizado(agendamentos))}",
            f"Faturamento previsto (em aberto):   {moeda(self.faturamento_previsto(agendamentos))}",
            "",
            "Por profissional:",
        ]
        resumo = self.por_profissional(agendamentos)
        for item in resumo:
            linhas.append(f"  - {item['profissional']}: {item['em_aberto']} em aberto, "
                          f"{item['concluidos']} concluído(s), {moeda(item['faturado'])}")
        if not resumo:
            linhas.append("  (sem agendamentos)")
        return "\n".join(linhas)
