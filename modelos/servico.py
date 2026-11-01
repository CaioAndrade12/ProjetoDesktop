"""
Serviços oferecidos pela clínica/empresa.

Conceitos de OO neste arquivo:
- CLASSE ABSTRATA: Servico.
- HERANÇA: Consulta, Exame e Retorno herdam de Servico.
- POLIMORFISMO: cada serviço calcula o valor de um jeito (calcular_valor).
- ATRIBUTOS DE CLASSE: TIPO e DESCONTO (valem para a classe inteira).
- MÉTODO ESTÁTICO / FÁBRICA: Servico.criar() devolve a subclasse certa.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .excecoes import DadoInvalidoErro
from .utilitarios import moeda, numero_decimal, numero_inteiro, texto_obrigatorio

TIPOS_DE_SERVICO = ("Consulta", "Exame", "Retorno")


class Servico(ABC):
    """Classe ABSTRATA: todo serviço tem nome, preço base e duração."""

    TIPO = "Serviço"  # ATRIBUTO DE CLASSE (cada filha define o seu)

    def __init__(self, nome: str, preco_base: float, duracao_min: int,
                 id: Optional[int] = None) -> None:
        self.id = id
        self.nome = nome
        self.preco_base = preco_base
        self.duracao_min = duracao_min

    # ---------- ENCAPSULAMENTO: atributos privados + validação ----------
    @property
    def nome(self) -> str:
        return self.__nome

    @nome.setter
    def nome(self, valor: str) -> None:
        self.__nome = texto_obrigatorio(valor, "Nome do serviço")

    @property
    def preco_base(self) -> float:
        return self.__preco_base

    @preco_base.setter
    def preco_base(self, valor) -> None:
        self.__preco_base = numero_decimal(valor, "Preço")

    @property
    def duracao_min(self) -> int:
        return self.__duracao_min

    @duracao_min.setter
    def duracao_min(self, valor) -> None:
        self.__duracao_min = numero_inteiro(valor, "Duração (min)", 10, 480)

    # ---------- POLIMORFISMO ----------
    @abstractmethod
    def calcular_valor(self) -> float:
        """Valor final cobrado do cliente (cada tipo calcula do seu jeito)."""

    def atualizar(self, nome: str, preco_base, duracao_min, **extras) -> None:
        """Muda os dados só se TODOS forem válidos. `extras` = dados de cada tipo."""
        novos = (texto_obrigatorio(nome, "Nome do serviço"),
                 numero_decimal(preco_base, "Preço"),
                 numero_inteiro(duracao_min, "Duração (min)", 10, 480))
        self.__nome, self.__preco_base, self.__duracao_min = novos

    def para_dict(self) -> dict:
        return {"id": self.id, "tipo": self.TIPO, "nome": self.nome,
                "preco_base": self.preco_base, "duracao_min": self.duracao_min}

    def __str__(self) -> str:
        return (f"{self.TIPO}: {self.nome} | {moeda(self.calcular_valor())} | "
                f"{self.duracao_min} min")

    @staticmethod
    def criar(tipo: str, nome: str, preco_base, duracao_min, taxa_material=0,
              id: Optional[int] = None) -> "Servico":
        """FÁBRICA: cria o objeto da subclasse certa a partir do nome do tipo."""
        tipo = str(tipo).strip().lower()
        if tipo == "consulta":
            return Consulta(nome, preco_base, duracao_min, id)
        if tipo == "exame":
            return Exame(nome, preco_base, duracao_min, taxa_material, id)
        if tipo == "retorno":
            return Retorno(nome, preco_base, duracao_min, id)
        raise DadoInvalidoErro(f"Tipo de serviço desconhecido: {tipo}.")


class Consulta(Servico):
    """Consulta: cobra exatamente o preço base."""

    TIPO = "Consulta"

    def calcular_valor(self) -> float:
        return self.preco_base


class Exame(Servico):
    """Exame: preço base + taxa de material (atributo que só o exame tem)."""

    TIPO = "Exame"

    def __init__(self, nome: str, preco_base: float, duracao_min: int,
                 taxa_material: float = 0, id: Optional[int] = None) -> None:
        super().__init__(nome, preco_base, duracao_min, id)
        self.taxa_material = taxa_material

    @property
    def taxa_material(self) -> float:
        return self.__taxa_material

    @taxa_material.setter
    def taxa_material(self, valor) -> None:
        self.__taxa_material = numero_decimal(valor, "Taxa de material")

    def calcular_valor(self) -> float:
        return round(self.preco_base + self.taxa_material, 2)

    def atualizar(self, nome: str, preco_base, duracao_min,
                  taxa_material=None, **extras) -> None:
        nova_taxa = (self.taxa_material if taxa_material is None
                     else numero_decimal(taxa_material, "Taxa de material"))
        super().atualizar(nome, preco_base, duracao_min)
        self.__taxa_material = nova_taxa

    def para_dict(self) -> dict:
        dados = super().para_dict()  # reaproveita o da mãe e acrescenta
        dados["taxa_material"] = self.taxa_material
        return dados


class Retorno(Servico):
    """Retorno: o cliente paga só metade do preço base."""

    TIPO = "Retorno"
    DESCONTO = 0.5  # 50 %

    def calcular_valor(self) -> float:
        return round(self.preco_base * (1 - self.DESCONTO), 2)
