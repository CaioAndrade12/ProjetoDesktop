"""Testes de Pessoa, Cliente, Profissional e Contato."""
import unittest

from modelos import Cliente, Contato, DadoInvalidoErro, Pessoa, Profissional
from tests.auxiliares import CPF_ANA


class TestContato(unittest.TestCase):
    def test_telefone_e_normalizado_e_formatado(self):
        contato = Contato("(11) 98765-4321", "ANA@Email.com")
        self.assertEqual(contato.telefone, "11987654321")
        self.assertEqual(contato.telefone_formatado, "(11) 98765-4321")
        self.assertEqual(contato.email, "ana@email.com")

    def test_telefone_invalido(self):
        with self.assertRaises(DadoInvalidoErro):
            Contato("1234")

    def test_email_invalido(self):
        with self.assertRaises(DadoInvalidoErro):
            Contato("11987654321", "ana.email.com")

    def test_email_e_opcional(self):
        self.assertEqual(Contato("1134567890").email, "")


class TestPessoa(unittest.TestCase):
    def test_pessoa_e_abstrata(self):
        with self.assertRaises(TypeError):
            Pessoa("Fulano", "11987654321")

    def test_heranca(self):
        cliente = Cliente("Ana Souza", "11987654321", CPF_ANA)
        profissional = Profissional("Juliana Rocha", "1134567890", "Clínica Geral")
        self.assertIsInstance(cliente, Pessoa)
        self.assertIsInstance(profissional, Pessoa)

    def test_polimorfismo_descricao(self):
        pessoas = [Cliente("Ana Souza", "11987654321", CPF_ANA),
                   Profissional("Juliana Rocha", "1134567890", "Clínica Geral")]
        descricoes = [str(p) for p in pessoas]  # mesma chamada, resultados diferentes
        self.assertTrue(descricoes[0].startswith("Cliente Ana Souza"))
        self.assertTrue(descricoes[1].startswith("Profissional Juliana Rocha (Clínica Geral)"))

    def test_composicao_cada_pessoa_tem_o_seu_contato(self):
        ana = Cliente("Ana Souza", "11987654321", CPF_ANA)
        juliana = Profissional("Juliana Rocha", "1134567890", "Clínica Geral")
        self.assertIsInstance(ana.contato, Contato)
        self.assertIsNot(ana.contato, juliana.contato)

    def test_nome_curto_e_recusado(self):
        with self.assertRaises(DadoInvalidoErro):
            Cliente("Al", "11987654321", CPF_ANA)

    def test_nome_remove_espacos_extras(self):
        self.assertEqual(Cliente("  Ana    Souza ", "11987654321", CPF_ANA).nome, "Ana Souza")


class TestCliente(unittest.TestCase):
    def test_cpf_valido_e_formatado(self):
        cliente = Cliente("Ana Souza", "11987654321", CPF_ANA)
        self.assertEqual(cliente.cpf, "15881399803")
        self.assertEqual(cliente.cpf_formatado, CPF_ANA)

    def test_metodo_estatico_valida_cpf(self):
        self.assertTrue(Cliente.cpf_valido(CPF_ANA))
        self.assertFalse(Cliente.cpf_valido("158.813.998-04"))
        self.assertFalse(Cliente.cpf_valido("111.111.111-11"))
        self.assertFalse(Cliente.cpf_valido("123"))

    def test_cpf_invalido_e_recusado(self):
        with self.assertRaises(DadoInvalidoErro):
            Cliente("Ana Souza", "11987654321", "123.456.789-00")

    def test_atualizar_so_muda_se_tudo_for_valido(self):
        cliente = Cliente("Ana Souza", "11987654321", CPF_ANA)
        with self.assertRaises(DadoInvalidoErro):
            cliente.atualizar("Ana Maria", "123", "ana@email.com")  # telefone inválido
        self.assertEqual(cliente.nome, "Ana Souza")  # nada mudou
        cliente.atualizar("Ana Maria Souza", "(11) 91111-2222", "ana@email.com")
        self.assertEqual(cliente.nome, "Ana Maria Souza")
        self.assertEqual(cliente.contato.telefone, "11911112222")

    def test_para_dict_estende_o_da_mae(self):
        dados = Cliente("Ana Souza", "11987654321", CPF_ANA, id=7).para_dict()
        self.assertEqual(dados, {"id": 7, "nome": "Ana Souza", "telefone": "11987654321",
                                 "email": "", "cpf": "15881399803"})


class TestProfissional(unittest.TestCase):
    def test_especialidade_obrigatoria(self):
        with self.assertRaises(DadoInvalidoErro):
            Profissional("Juliana Rocha", "1134567890", "")

    def test_atualizar_especialidade(self):
        profissional = Profissional("Juliana Rocha", "1134567890", "Clínica Geral")
        profissional.atualizar("Juliana Rocha", "1134567890", "", especialidade="Pediatria")
        self.assertEqual(profissional.especialidade, "Pediatria")
        self.assertEqual(profissional.para_dict()["especialidade"], "Pediatria")


if __name__ == "__main__":
    unittest.main()
