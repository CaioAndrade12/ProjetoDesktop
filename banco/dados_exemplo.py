"""Dados de exemplo gravados na primeira execução (quando o banco está vazio)."""
from datetime import date, datetime, time, timedelta

from modelos import Cliente, Clinica, Consulta, Exame, Profissional, Retorno


def popular_dados_exemplo(clinica: Clinica) -> None:
    # AGREGAÇÃO: os objetos são criados aqui fora e depois entregues à clínica
    ana = clinica.cadastrar_cliente(
        Cliente("Ana Souza", "(11) 98765-4321", "158.813.998-03", "ana.souza@email.com"))
    bruno = clinica.cadastrar_cliente(
        Cliente("Bruno Lima", "(11) 91234-5678", "698.797.309-17"))
    carla = clinica.cadastrar_cliente(
        Cliente("Carla Mendes", "(21) 99876-1234", "114.170.753-50", "carla.mendes@email.com"))

    juliana = clinica.cadastrar_profissional(
        Profissional("Juliana Rocha", "(11) 3456-7890", "Clínica Geral", "juliana@bemestar.com"))
    marcos = clinica.cadastrar_profissional(
        Profissional("Marcos Alves", "(11) 3456-7891", "Cardiologia", "marcos@bemestar.com"))
    paula = clinica.cadastrar_profissional(
        Profissional("Paula Nunes", "(11) 3456-7892", "Nutrição"))

    consulta = clinica.cadastrar_servico(Consulta("Consulta geral", 150, 30))
    exame = clinica.cadastrar_servico(Exame("Eletrocardiograma", 120, 30, taxa_material=35))
    retorno = clinica.cadastrar_servico(Retorno("Retorno", 150, 20))
    nutricao = clinica.cadastrar_servico(Consulta("Avaliação nutricional", 180, 60))

    amanha = date.today() + timedelta(days=1)
    depois = date.today() + timedelta(days=2)

    def em(dia: date, hora: int, minuto: int = 0) -> datetime:
        return datetime.combine(dia, time(hora, minuto))

    primeiro = clinica.agendar(ana.id, juliana.id, consulta.id, em(amanha, 9), "Primeira consulta")
    clinica.confirmar_agendamento(primeiro.id)
    clinica.agendar(bruno.id, marcos.id, exame.id, em(amanha, 10))
    clinica.agendar(carla.id, paula.id, nutricao.id, em(amanha, 14))
    clinica.agendar(ana.id, juliana.id, retorno.id, em(depois, 9, 30), "Trazer os exames")
    clinica.agendar(bruno.id, juliana.id, consulta.id, em(depois, 11))
