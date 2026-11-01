"""Funções que montam os cenários usados em vários testes."""
from datetime import date, datetime, time, timedelta

from modelos import Cliente, Clinica, Consulta, Exame, Profissional, Retorno

CPF_ANA = "158.813.998-03"
CPF_BRUNO = "698.797.309-17"
CPF_LIVRE = "884.472.940-72"


def amanha_as(hora: int, minuto: int = 0, dias: int = 1) -> datetime:
    """Data/hora sempre no futuro: amanhã (ou daqui a `dias` dias) no horário pedido."""
    return datetime.combine(date.today() + timedelta(days=dias), time(hora, minuto))


def nova_clinica(banco=None) -> Clinica:
    """Clínica com 2 clientes, 2 profissionais e 3 serviços (ids 1, 2, 3...)."""
    clinica = Clinica("Clínica Teste", banco)
    clinica.cadastrar_cliente(Cliente("Ana Souza", "(11) 98765-4321", CPF_ANA, "ana@email.com"))
    clinica.cadastrar_cliente(Cliente("Bruno Lima", "11912345678", CPF_BRUNO))
    clinica.cadastrar_profissional(Profissional("Juliana Rocha", "(11) 3456-7890", "Clínica Geral"))
    clinica.cadastrar_profissional(Profissional("Marcos Alves", "(11) 3456-7891", "Cardiologia"))
    clinica.cadastrar_servico(Consulta("Consulta geral", 150, 30))
    clinica.cadastrar_servico(Exame("Eletrocardiograma", 120, 30, taxa_material=35))
    clinica.cadastrar_servico(Retorno("Retorno", 150, 20))
    return clinica
