"""Testes dos serviços: classe abstrata, herança, polimorfismo e fábrica."""
import unittest

from modelos import Consulta, DadoInvalidoErro, Exame, Retorno, Servico


class TestServico(unittest.TestCase):
    def test_servico_e_abstrato(self):
        with self.assertRaises(TypeError):
            Servico("Genérico", 100, 30)

    def test_polimorfismo_calcular_valor(self):
        servicos = [Consulta("Consulta geral", 150, 30),
                    Exame("Eletrocardiograma", 120, 30, taxa_material=35),
                    Retorno("Retorno", 150, 20)]
        valores = [s.calcular_valor() for s in servicos]  # mesma chamada, regras diferentes
        self.assertEqual(valores, [150.0, 155.0, 75.0])

    def test_atributo_de_classe_tipo(self):
        self.assertEqual([Consulta.TIPO, Exame.TIPO, Retorno.TIPO], ["Consulta", "Exame", "Retorno"])

    def test_preco_aceita_virgula(self):
        self.assertEqual(Consulta("Consulta geral", "150,50", 30).preco_base, 150.5)

    def test_preco_negativo_e_recusado(self):
        with self.assertRaises(DadoInvalidoErro):
            Consulta("Consulta geral", -10, 30)

    def test_preco_nao_numerico_e_recusado(self):
        with self.assertRaises(DadoInvalidoErro):
            Consulta("Consulta geral", "abc", 30)

    def test_duracao_fora_do_limite(self):
        with self.assertRaises(DadoInvalidoErro):
            Consulta("Consulta geral", 150, 5)
        with self.assertRaises(DadoInvalidoErro):
            Consulta("Consulta geral", 150, "30.5")

    def test_fabrica_cria_a_subclasse_certa(self):
        self.assertIsInstance(Servico.criar("consulta", "Consulta", 100, 30), Consulta)
        exame = Servico.criar("Exame", "Hemograma", 50, 15, taxa_material=10)
        self.assertIsInstance(exame, Exame)
        self.assertEqual(exame.calcular_valor(), 60.0)
        self.assertIsInstance(Servico.criar("RETORNO", "Retorno", 100, 20), Retorno)
        with self.assertRaises(DadoInvalidoErro):
            Servico.criar("massagem", "Massagem", 100, 30)

    def test_para_dict_do_exame_inclui_taxa(self):
        self.assertNotIn("taxa_material", Consulta("Consulta", 100, 30).para_dict())
        self.assertEqual(Exame("Hemograma", 50, 15, 10).para_dict()["taxa_material"], 10.0)

    def test_atualizar_polimorfico(self):
        consulta = Consulta("Consulta", 100, 30)
        exame = Exame("Hemograma", 50, 15, 10)
        for servico in (consulta, exame):  # a mesma chamada serve para os dois tipos
            servico.atualizar("Novo nome", 200, 45, taxa_material=20)
        self.assertEqual(consulta.calcular_valor(), 200.0)
        self.assertEqual(exame.calcular_valor(), 220.0)

    def test_atualizar_invalido_nao_muda_nada(self):
        exame = Exame("Hemograma", 50, 15, 10)
        with self.assertRaises(DadoInvalidoErro):
            exame.atualizar("Hemograma completo", 80, 15, taxa_material=-1)
        self.assertEqual((exame.nome, exame.preco_base, exame.taxa_material), ("Hemograma", 50.0, 10.0))


if __name__ == "__main__":
    unittest.main()
