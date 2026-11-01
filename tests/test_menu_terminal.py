"""Testes do menu no terminal: simulam o que o usuário digita."""
import io
import unittest
from contextlib import redirect_stdout

from interface.menu_terminal import MenuTerminal
from modelos import StatusAgendamento
from tests.auxiliares import CPF_LIVRE, amanha_as, nova_clinica


def rodar_menu(clinica, teclas):
    """Executa o menu com as teclas informadas e devolve tudo o que foi impresso."""
    entradas = iter(teclas)
    saida = io.StringIO()
    menu = MenuTerminal(clinica, entrada=lambda _rotulo: next(entradas), interativo=False)
    with redirect_stdout(saida):
        menu.executar()
    return saida.getvalue()


class TestMenuTerminal(unittest.TestCase):
    def setUp(self):
        self.clinica = nova_clinica()

    def test_sair(self):
        self.assertIn("Até logo!", rodar_menu(self.clinica, ["0"]))

    def test_opcao_invalida(self):
        self.assertIn("Opção inválida.", rodar_menu(self.clinica, ["9", "0"]))

    def test_cadastrar_cliente(self):
        rodar_menu(self.clinica, ["1", "1", "Daniel Costa", "(11) 99555-1234", CPF_LIVRE, "", "0", "0"])
        self.assertEqual(self.clinica.listar_clientes("daniel")[0].cpf_formatado, CPF_LIVRE)

    def test_erro_de_validacao_aparece_sem_travar(self):
        saida = rodar_menu(self.clinica, ["1", "1", "Daniel Costa", "123", CPF_LIVRE, "", "0", "0"])
        self.assertIn("[ERRO] Telefone deve ter DDD", saida)

    def test_cadastrar_exame(self):
        rodar_menu(self.clinica, ["3", "1", "2", "Hemograma", "40,00", "15", "10", "0", "0"])
        self.assertEqual(self.clinica.listar_servicos("hemograma")[0].calcular_valor(), 50.0)

    def test_novo_agendamento_com_aviso_por_whatsapp(self):
        data = amanha_as(0).strftime("%d/%m/%Y")
        saida = rodar_menu(self.clinica, ["4", "1", "1", "1", "1", data, "15:00", "Retorno", "1", "0", "0"])
        self.assertIn("Agendamento criado!", saida)
        self.assertIn("[WhatsApp para", saida)
        self.assertEqual(self.clinica.listar_agendamentos()[0].data_hora, amanha_as(15))

    def test_confirmar_e_cancelar(self):
        agendamento = self.clinica.agendar(1, 1, 1, amanha_as(9))
        rodar_menu(self.clinica, ["4", "5", str(agendamento.id), "0", "0"])
        self.assertIs(agendamento.status, StatusAgendamento.CONFIRMADO)
        rodar_menu(self.clinica, ["4", "7", str(agendamento.id), "0", "0"])
        self.assertIs(agendamento.status, StatusAgendamento.CANCELADO)

    def test_remarcar(self):
        agendamento = self.clinica.agendar(1, 1, 1, amanha_as(9))
        data = amanha_as(0).strftime("%d/%m/%Y")
        rodar_menu(self.clinica, ["4", "8", str(agendamento.id), data, "16:30", "0", "0", "0"])
        self.assertEqual(agendamento.data_hora, amanha_as(16, 30))

    def test_relatorio(self):
        self.assertIn("RELATÓRIO - CLÍNICA TESTE", rodar_menu(self.clinica, ["5", "0"]))

    def test_banco_de_dados_sem_banco(self):
        self.assertIn("sem banco de dados", rodar_menu(self.clinica, ["6", "0"]))


if __name__ == "__main__":
    unittest.main()
