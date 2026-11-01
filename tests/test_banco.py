"""Testes do banco de dados SQLite (salvar, atualizar, excluir e recarregar)."""
import os
import shutil
import tempfile
import unittest

from banco import BancoDeDados, popular_dados_exemplo
from modelos import Clinica, Exame, StatusAgendamento
from tests.auxiliares import amanha_as, nova_clinica


class TestBancoDeDados(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.caminho = os.path.join(self.pasta, "teste.db")
        self.banco = BancoDeDados(self.caminho)

    def tearDown(self):
        self.banco.fechar()  # fecha antes de apagar (no Windows o arquivo fica preso)
        shutil.rmtree(self.pasta, ignore_errors=True)

    def reabrir(self) -> Clinica:
        """Fecha o banco e abre de novo, como se o programa tivesse reiniciado."""
        self.banco.fechar()
        self.banco = BancoDeDados(self.caminho)
        return Clinica("Clínica Teste", self.banco)

    def test_cria_as_quatro_tabelas(self):
        self.assertEqual(self.banco.nomes_tabelas(),
                         ["clientes", "profissionais", "servicos", "agendamentos"])
        for tabela in self.banco.nomes_tabelas():
            self.assertEqual(self.banco.contar(tabela), 0)

    def test_dados_continuam_depois_de_reabrir(self):
        clinica = nova_clinica(self.banco)
        agendamento = clinica.agendar(1, 2, 2, amanha_as(10), "Em jejum")
        clinica.confirmar_agendamento(agendamento.id)

        recarregada = self.reabrir()
        self.assertEqual([c.nome for c in recarregada.listar_clientes()], ["Ana Souza", "Bruno Lima"])
        exame = recarregada.buscar_servico(2)
        self.assertIsInstance(exame, Exame)  # a fábrica recriou a subclasse certa
        self.assertEqual(exame.calcular_valor(), 155.0)
        copia = recarregada.buscar_agendamento(agendamento.id)
        self.assertEqual(copia.data_hora, amanha_as(10))
        self.assertIs(copia.status, StatusAgendamento.CONFIRMADO)
        self.assertEqual(copia.observacao, "Em jejum")
        self.assertIs(copia.cliente, recarregada.buscar_cliente(1))  # associação refeita

    def test_edicao_e_salva(self):
        clinica = nova_clinica(self.banco)
        clinica.editar_cliente(2, "Bruno Lima Santos", "11912345678", "698.797.309-17", "b@email.com")
        recarregada = self.reabrir()
        bruno = recarregada.buscar_cliente(2)
        self.assertEqual((bruno.nome, bruno.contato.email), ("Bruno Lima Santos", "b@email.com"))

    def test_exclusao_e_salva(self):
        clinica = nova_clinica(self.banco)
        clinica.remover_servico(3)
        self.assertEqual(self.banco.contar("servicos"), 2)
        self.assertEqual(len(self.reabrir().listar_servicos()), 2)

    def test_upsert_nao_duplica_registros(self):
        clinica = nova_clinica(self.banco)
        agendamento = clinica.agendar(1, 1, 1, amanha_as(9))
        clinica.confirmar_agendamento(agendamento.id)
        clinica.concluir_agendamento(agendamento.id)
        self.assertEqual(self.banco.contar("agendamentos"), 1)

    def test_consultar_tabela(self):
        nova_clinica(self.banco)
        colunas, linhas = self.banco.consultar_tabela("clientes")
        self.assertEqual(colunas, ["id", "nome", "telefone", "email", "cpf"])
        self.assertEqual(len(linhas), 2)
        with self.assertRaises(ValueError):
            self.banco.consultar_tabela("senhas")

    def test_dados_de_exemplo(self):
        clinica = Clinica("Clínica Teste", self.banco)
        self.assertTrue(clinica.vazia)
        popular_dados_exemplo(clinica)
        self.assertFalse(self.reabrir().vazia)
        self.assertEqual(self.banco.contar("agendamentos"), 5)


if __name__ == "__main__":
    unittest.main()
