"""Testes do Agendamento e da Agenda (composição, conflitos e status)."""
import unittest
from datetime import date, datetime, time, timedelta

from modelos import (Agenda, Agendamento, Cliente, Consulta, Exame, HorarioIndisponivelErro,
                     OperacaoInvalidaErro, Profissional, RegistroNaoEncontradoErro,
                     StatusAgendamento)
from tests.auxiliares import CPF_ANA, CPF_BRUNO, amanha_as


class TestAgenda(unittest.TestCase):
    def setUp(self):
        self.agenda = Agenda()
        self.ana = Cliente("Ana Souza", "11987654321", CPF_ANA)
        self.bruno = Cliente("Bruno Lima", "11912345678", CPF_BRUNO)
        self.juliana = Profissional("Juliana Rocha", "1134567890", "Clínica Geral")
        self.marcos = Profissional("Marcos Alves", "1134567891", "Cardiologia")
        self.consulta = Consulta("Consulta geral", 150, 30)
        self.exame = Exame("Eletrocardiograma", 120, 30, 35)

    def agendar(self, cliente=None, profissional=None, hora=9, minuto=0, servico=None):
        return self.agenda.agendar(cliente or self.ana, profissional or self.juliana,
                                   servico or self.consulta, amanha_as(hora, minuto))

    def test_composicao_a_agenda_cria_os_agendamentos(self):
        agendamento = self.agendar()
        self.assertIsInstance(agendamento, Agendamento)
        self.assertEqual(len(self.agenda), 1)
        self.assertIs(self.agenda.buscar(agendamento.id), agendamento)

    def test_associacao_aponta_para_objetos_existentes(self):
        agendamento = self.agendar()
        self.assertIs(agendamento.cliente, self.ana)
        self.assertIs(agendamento.profissional, self.juliana)
        self.assertIs(agendamento.servico, self.consulta)

    def test_valor_usa_polimorfismo_do_servico(self):
        self.assertEqual(self.agendar(servico=self.exame).valor, 155.0)

    def test_fim_considera_a_duracao(self):
        self.assertEqual(self.agendar(hora=9).fim, amanha_as(9, 30))

    def test_conflito_com_o_mesmo_profissional(self):
        self.agendar(self.ana, self.juliana, 9)
        with self.assertRaises(HorarioIndisponivelErro):
            self.agendar(self.bruno, self.juliana, 9, 15)

    def test_conflito_com_o_mesmo_cliente(self):
        self.agendar(self.ana, self.juliana, 9)
        with self.assertRaises(HorarioIndisponivelErro):
            self.agendar(self.ana, self.marcos, 9)

    def test_horarios_encostados_sao_permitidos(self):
        self.agendar(self.ana, self.juliana, 9)
        self.agendar(self.bruno, self.juliana, 9, 30)
        self.assertEqual(len(self.agenda), 2)

    def test_nao_agenda_no_passado(self):
        ontem = datetime.combine(date.today() - timedelta(days=1), time(10))
        with self.assertRaises(HorarioIndisponivelErro):
            self.agenda.agendar(self.ana, self.juliana, self.consulta, ontem)

    def test_nao_agenda_fora_do_expediente(self):
        with self.assertRaises(HorarioIndisponivelErro):
            self.agendar(hora=7)
        with self.assertRaises(HorarioIndisponivelErro):
            self.agendar(hora=17, minuto=45)  # terminaria 18:15

    def test_cancelado_libera_o_horario(self):
        primeiro = self.agendar(self.ana, self.juliana, 9)
        primeiro.cancelar()
        self.agendar(self.bruno, self.juliana, 9)
        self.assertEqual(len(self.agenda), 2)

    def test_fluxo_de_status(self):
        agendamento = self.agendar()
        self.assertIs(agendamento.status, StatusAgendamento.AGENDADO)
        agendamento.confirmar()
        self.assertIs(agendamento.status, StatusAgendamento.CONFIRMADO)
        agendamento.concluir()
        self.assertIs(agendamento.status, StatusAgendamento.CONCLUIDO)
        self.assertFalse(agendamento.ativo)

    def test_nao_cancela_atendimento_concluido(self):
        agendamento = self.agendar()
        agendamento.concluir()
        with self.assertRaises(OperacaoInvalidaErro):
            agendamento.cancelar()

    def test_nao_confirma_duas_vezes(self):
        agendamento = self.agendar()
        agendamento.confirmar()
        with self.assertRaises(OperacaoInvalidaErro):
            agendamento.confirmar()

    def test_remarcar_para_horario_livre(self):
        agendamento = self.agendar(hora=9)
        agendamento.confirmar()
        self.agenda.remarcar(agendamento.id, amanha_as(15))
        self.assertEqual(agendamento.data_hora, amanha_as(15))
        self.assertIs(agendamento.status, StatusAgendamento.AGENDADO)  # precisa confirmar de novo

    def test_remarcar_para_horario_ocupado(self):
        self.agendar(self.bruno, self.juliana, 15)
        agendamento = self.agendar(self.ana, self.juliana, 9)
        with self.assertRaises(HorarioIndisponivelErro):
            self.agenda.remarcar(agendamento.id, amanha_as(15))
        self.assertEqual(agendamento.data_hora, amanha_as(9))

    def test_remarcar_cancelado_nao_pode(self):
        agendamento = self.agendar()
        agendamento.cancelar()
        with self.assertRaises(OperacaoInvalidaErro):
            self.agenda.remarcar(agendamento.id, amanha_as(15))

    def test_horarios_livres(self):
        livres = self.agenda.horarios_livres(self.juliana, self.consulta, amanha_as(0).date())
        self.assertEqual(len(livres), 20)  # 08:00 até 17:30, de 30 em 30 min
        self.agendar(self.ana, self.juliana, 9)
        livres = self.agenda.horarios_livres(self.juliana, self.consulta, amanha_as(0).date())
        self.assertNotIn(amanha_as(9), livres)
        self.assertEqual(len(livres), 19)

    def test_ordenacao_por_data_usa_sobrecarga_de_operador(self):
        tarde = self.agendar(self.ana, self.juliana, 15)
        manha = self.agendar(self.bruno, self.juliana, 8)
        self.assertEqual(sorted([tarde, manha]), [manha, tarde])
        self.assertEqual(list(self.agenda), [manha, tarde])

    def test_listar_com_filtros(self):
        self.agendar(self.ana, self.juliana, 9)
        self.agendar(self.bruno, self.marcos, 9)
        self.agenda.agendar(self.ana, self.juliana, self.consulta, amanha_as(9, dias=2))
        self.assertEqual(len(self.agenda.listar(dia=amanha_as(0).date())), 2)
        self.assertEqual(len(self.agenda.listar(profissional=self.juliana)), 2)
        self.assertEqual(len(self.agenda.listar(cliente=self.bruno)), 1)
        self.assertEqual(len(self.agenda.listar(status=StatusAgendamento.CANCELADO)), 0)

    def test_buscar_inexistente(self):
        with self.assertRaises(RegistroNaoEncontradoErro):
            self.agenda.buscar(99)

    def test_para_dict(self):
        dados = self.agendar(hora=10).para_dict()
        self.assertEqual(dados["status"], "AGENDADO")
        self.assertTrue(dados["data_hora"].endswith("10:00"))


if __name__ == "__main__":
    unittest.main()
