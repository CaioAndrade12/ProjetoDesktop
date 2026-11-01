"""Testes da interface gráfica (as janelas são criadas escondidas)."""
import unittest
from unittest import mock

try:
    import tkinter as tk
except ImportError:  # Python instalado sem Tkinter
    tk = None

from modelos import StatusAgendamento
from tests.auxiliares import CPF_LIVRE, amanha_as, nova_clinica


@unittest.skipIf(tk is None, "Tkinter não está instalado")
class TestInterfaceGrafica(unittest.TestCase):
    def setUp(self):
        from interface.janelas import JanelaPrincipal
        self.clinica = nova_clinica()
        self.clinica.agendar(1, 1, 1, amanha_as(9))
        try:
            self.janela = JanelaPrincipal(self.clinica)
        except tk.TclError as erro:  # computador sem tela (ex.: servidor)
            self.skipTest(f"Sem tela disponível: {erro}")
        self.janela.withdraw()  # não aparece na tela durante o teste
        self.janela.update_idletasks()

    def tearDown(self):
        self.janela.destroy()

    def test_janela_tem_as_cinco_abas(self):
        self.assertEqual([type(aba).__name__ for aba in self.janela.abas],
                         ["AbaAgenda", "AbaClientes", "AbaProfissionais", "AbaServicos", "AbaRelatorios"])

    def test_agenda_mostra_os_agendamentos_do_dia(self):
        self.janela.aba_agenda.mostrar_dia(amanha_as(0).date())
        linhas = self.janela.aba_agenda._tabela.arvore.get_children()
        self.assertEqual(len(linhas), 1)

    def test_cadastrar_cliente_pelo_formulario(self):
        aba = self.janela.abas[1]
        for campo, valor in {"nome": "Eduarda Martins", "cpf": CPF_LIVRE,
                             "telefone": "(31) 98888-7777", "email": "duda@email.com"}.items():
            aba._variaveis[campo].set(valor)
        aba._salvar()
        self.assertEqual(len(self.clinica.listar_clientes("eduarda")), 1)

    def test_formulario_invalido_mostra_erro(self):
        aba = self.janela.abas[1]
        aba._variaveis["nome"].set("Eduarda Martins")
        with mock.patch("interface.abas.messagebox.showerror") as erro:
            aba._salvar()
        erro.assert_called_once()
        self.assertEqual(len(self.clinica.listar_clientes("eduarda")), 0)

    def test_novo_agendamento_pela_janela(self):
        dialogo = self.janela.abrir_agendamento()
        dialogo.withdraw()
        dialogo.var_cliente.set(dialogo.combo_cliente["values"][1])
        dialogo.var_profissional.set(dialogo.combo_profissional["values"][0])
        dialogo.var_servico.set(dialogo.combo_servico["values"][1])
        dialogo.var_data.set(amanha_as(0).strftime("%d/%m/%Y"))
        dialogo.var_hora.set("10:00")
        dialogo.var_aviso.set(dialogo.WHATSAPP)
        with mock.patch("interface.janelas.messagebox.showinfo") as aviso:
            agendamento = dialogo.salvar()
        self.assertEqual(agendamento.data_hora, amanha_as(10))
        self.assertIn("WhatsApp", aviso.call_args[0][1])

    def test_botoes_de_status(self):
        aba = self.janela.aba_agenda
        aba.mostrar_dia(amanha_as(0).date(), selecionar=1)
        aba._mudar_status(self.clinica.confirmar_agendamento, "Confirmar")
        self.assertIs(self.clinica.buscar_agendamento(1).status, StatusAgendamento.CONFIRMADO)

    def test_relatorio_mostra_os_totais(self):
        aba = self.janela.abas[4]
        aba.atualizar()
        self.assertEqual(aba._cartoes["Agendado"].valor, "1")
        self.assertEqual(aba._cartoes["clientes"].valor, "2")


if __name__ == "__main__":
    unittest.main()
