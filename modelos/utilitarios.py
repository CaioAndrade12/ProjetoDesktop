"""Funções auxiliares de validação e formatação usadas pelos modelos."""
import math
import re

from .excecoes import DadoInvalidoErro


def somente_digitos(texto) -> str:
    """Remove tudo que não for número: '(11) 98765-4321' -> '11987654321'."""
    return re.sub(r"\D", "", str(texto or ""))


def texto_obrigatorio(valor, campo: str, minimo: int = 3) -> str:
    """Tira espaços extras e exige um tamanho mínimo."""
    texto = " ".join(str(valor or "").split())
    if len(texto) < minimo:
        raise DadoInvalidoErro(f"{campo} deve ter pelo menos {minimo} caracteres.")
    return texto


def numero_decimal(valor, campo: str) -> float:
    """Converte para número aceitando vírgula ('150,50') e proíbe negativos."""
    try:
        numero = float(str(valor).strip().replace(",", "."))
    except ValueError:
        raise DadoInvalidoErro(f"{campo} deve ser um número.") from None
    if not math.isfinite(numero) or numero < 0:
        raise DadoInvalidoErro(f"{campo} deve ser um número maior ou igual a zero.")
    return round(numero, 2)


def numero_inteiro(valor, campo: str, minimo: int, maximo: int) -> int:
    """Converte para inteiro e exige que esteja entre minimo e maximo."""
    try:
        numero = float(str(valor).strip().replace(",", "."))
    except ValueError:
        raise DadoInvalidoErro(f"{campo} deve ser um número inteiro.") from None
    if not numero.is_integer() or not minimo <= numero <= maximo:
        raise DadoInvalidoErro(f"{campo} deve ser um inteiro entre {minimo} e {maximo}.")
    return int(numero)


def moeda(valor: float) -> str:
    """Formata no padrão brasileiro: 1234.5 -> 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"
