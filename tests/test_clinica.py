"""Testes da Clínica (cadastros e agenda), dos notificadores e do relatório."""
import unittest

from modelos import (Agenda, Cliente, DadoInvalidoErro, HorarioIndisponivelErro,
                     Notificador, NotificadorEmail, NotificadorWhatsApp, OperacaoInvalidaErro,
                     RegistroNaoEncontradoErro, Relatorio, StatusAgendamento)
from tests.auxiliares import CPF_ANA, CPF_LIVRE, amanha_as, nova_clinica


class TestClinicaCadastros(unittest.TestCase):
    def setUp(self):
        self.clinica = nova_clinica()

    def test_composicao_clinica_cria_a_propria_agenda(self):
        self.assertIsInstance(self.clinica.agenda, Agenda)
        self.assertIsNot(self.clinica.agenda, nova_clinica().agenda)

    def test_ids_sao_gerados_em_sequencia(self):
        novo = self.clinica.cadastrar_cliente(Cliente("Carla Mendes", "21998761234", CPF_LIVRE))
        self.assertEqual(novo.id, 3)

    def test_agregacao_o_objeto_cadastrado_e_o_mesmo_criado_fora(self):
        carla = Cliente("Carla Mendes", "21998761234", CPF_LIVRE)
        self.clinica.cadastrar_cliente(carla)
        self.assertIs(self.clinica.buscar_cliente(carla.id), carla)

    def test_cpf_duplicado_e_recusado(self):
        with self.assertRaises(DadoInvalidoErro):
            self.clinica.cadastrar_cliente(Cliente("Outra Ana", "11911112222", CPF_ANA))

    def test_pesquisar_clientes_por_nome_e_cpf(self):
        self.assertEqual([c.nome for c in self.clinica.listar_clientes("bru")], ["Bruno Lima"])
        self.assertEqual([c.nome for c in self.clinica.listar_clientes("158.813")], ["Ana Souza"])

    def test_editar_cliente(self):
        self.clinica.editar_cliente(1, "Ana Maria Souza", "11911112222", CPF_ANA, "")
        ana = self.clinica.buscar_cliente(1)
        self.assertEqual((ana.nome, ana.contato.email), ("Ana Maria Souza", ""))

    def test_editar_cliente_com_cpf_de_outro_e_recusado(self):
        with self.assertRaises(DadoInvalidoErro):
            self.clinica.editar_cliente(2, "Bruno Lima", "11912345678", CPF_ANA)

    def test_buscar_inexistente(self):
        with self.assertRaises(RegistroNaoEncontradoErro):
            self.clinica.buscar_cliente(99)
        with self.assertRaises(RegistroNaoEncontradoErro):
            self.clinica.buscar_servico("abc")

    def test_remover_sem_agendamentos(self):
        self.clinica.remover_cliente(2)
        self.assertEqual(len(self.clinica.listar_clientes()), 1)

    def test_nao_remove_quem_tem_agendamento(self):
        self.clinica.agendar(1, 1, 1, amanha_as(9))
        with self.assertRaises(OperacaoInvalidaErro):
            self.clinica.remover_cliente(1)
        with self.assertRaises(OperacaoInvalidaErro):
            self.clinica.remover_profissional(1)
        with self.assertRaises(OperacaoInvalidaErro):
            self.clinica.remover_servico(1)

    def test_editar_profissional_e_servico(self):
        self.clinica.editar_profissional(2, "Marcos Alves", "1134567891", "Cardiologia Infantil")
        self.assertEqual(self.clinica.buscar_profissional(2).especialidade, "Cardiologia Infantil")
        self.clinica.editar_servico(2, "Eletrocardiograma", "130,00", 30, taxa_material="40")
        self.assertEqual(self.clinica.buscar_servico(2).calcular_valor(), 170.0)

    def test_listar_profissionais_por_especialidade(self):
        self.assertEqual([p.nome for p in self.clinica.listar_profissionais("cardio")],
                         ["Marcos Alves"])


class TestClinicaAgenda(unittest.TestCase):
    def setUp(self):
        self.clinica = nova_clinica()

    def test_agendar_pelos_codigos(self):
        agendamento = self.clinica.agendar(1, 1, 2, amanha_as(10), "Em jejum")
        self.assertEqual(agendamento.cliente.nome, "Ana Souza")
        self.assertEqual(agendamento.valor, 155.0)
        self.assertEqual(agendamento.observacao, "Em jejum")

    def test_agendar_com_codigo_inexistente(self):
        with self.assertRaises(RegistroNaoEncontradoErro):
            self.clinica.agendar(1, 99, 1, amanha_as(10))

    def test_mudancas_de_status(self):
        a = self.clinica.agendar(1, 1, 1, amanha_as(9))
        b = self.clinica.agendar(2, 1, 1, amanha_as(10))
        self.clinica.confirmar_agendamento(a.id)
        self.clinica.concluir_agendamento(a.id)
        self.clinica.cancelar_agendamento(b.id)
        self.assertIs(a.status, StatusAgendamento.CONCLUIDO)
        self.assertIs(b.status, StatusAgendamento.CANCELADO)

    def test_remarcar(self):
        a = self.clinica.agendar(1, 1, 1, amanha_as(9))
        self.clinica.agendar(2, 1, 1, amanha_as(10))
        with self.assertRaises(HorarioIndisponivelErro):
            self.clinica.remarcar_agendamento(a.id, amanha_as(10))
        self.clinica.remarcar_agendamento(a.id, amanha_as(11))
        self.assertEqual(a.data_hora, amanha_as(11))

    def test_listar_agendamentos_por_dia_e_profissional(self):
        self.clinica.agendar(1, 1, 1, amanha_as(9))
        self.clinica.agendar(2, 2, 2, amanha_as(9))
        dia = amanha_as(0).date()
        self.assertEqual(len(self.clinica.listar_agendamentos(dia=dia)), 2)
        self.assertEqual(len(self.clinica.listar_agendamentos(dia=dia, id_profissional=2)), 1)

    def test_horarios_livres_considera_o_cliente(self):
        self.clinica.agendar(1, 2, 1, amanha_as(9))  # Ana ocupada às 9h com o Marcos
        livres = self.clinica.horarios_livres(1, 1, amanha_as(0).date(), id_cliente=1)
        self.assertNotIn(amanha_as(9), livres)
        self.assertIn(amanha_as(9), self.clinica.horarios_livres(1, 1, amanha_as(0).date()))


class TestNotificadores(unittest.TestCase):
    def setUp(self):
        self.clinica = nova_clinica()
        self.agendamento = self.clinica.agendar(1, 1, 1, amanha_as(9))

    def test_notificador_e_abstrato(self):
        with self.assertRaises(TypeError):
            Notificador()

    def test_polimorfismo_e_dependencia(self):
        mensagens = [self.clinica.notificar(self.agendamento, canal)
                     for canal in (NotificadorWhatsApp(), NotificadorEmail())]
        self.assertTrue(mensagens[0].startswith("[WhatsApp para (11) 98765-4321]"))
        self.assertTrue(mensagens[1].startswith("[E-mail para ana@email.com]"))

    def test_email_sem_endereco_nao_e_enviado(self):
        do_bruno = self.clinica.agendar(2, 2, 1, amanha_as(9))
        canal = NotificadorEmail()
        self.assertIn("NÃO enviado", self.clinica.notificar(do_bruno, canal))
        self.assertEqual(len(canal.historico), 1)

    def test_historico_e_uma_copia(self):
        canal = NotificadorWhatsApp()
        canal.enviar(self.agendamento)
        canal.historico.clear()  # mexer na cópia não altera o original
        self.assertEqual(len(canal.historico), 1)


class TestRelatorio(unittest.TestCase):
    def test_totais_e_faturamento(self):
        clinica = nova_clinica()
        a = clinica.agendar(1, 1, 1, amanha_as(9))    # consulta R$ 150
        b = clinica.agendar(2, 2, 2, amanha_as(9))    # exame R$ 155
        c = clinica.agendar(1, 1, 3, amanha_as(14))   # retorno R$ 75
        clinica.concluir_agendamento(a.id)
        clinica.cancelar_agendamento(c.id)
        relatorio = Relatorio()  # DEPENDÊNCIA: recebe a agenda só no método
        self.assertEqual(relatorio.total_por_status(clinica.agenda),
                         {"Agendado": 1, "Confirmado": 0, "Concluído": 1, "Cancelado": 1})
        self.assertEqual(relatorio.faturamento_realizado(clinica.agenda), 150.0)
        self.assertEqual(relatorio.faturamento_previsto(clinica.agenda), 155.0)
        por_profissional = relatorio.por_profissional(clinica.agenda)
        self.assertEqual(por_profissional[0]["profissional"], "Juliana Rocha")
        self.assertEqual(por_profissional[0]["faturado"], 150.0)
        texto = relatorio.gerar_texto(clinica.agenda)
        self.assertIn("R$ 150,00", texto)
        self.assertIsNotNone(b)

    def test_relatorio_vazio(self):
        self.assertIn("(sem agendamentos)", Relatorio().gerar_texto(nova_clinica().agenda))


if __name__ == "__main__":
    unittest.main()
