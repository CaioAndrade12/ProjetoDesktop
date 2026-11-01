"""
Pessoas do sistema.

Conceitos de OO neste arquivo:
- CLASSE ABSTRATA: Pessoa (não pode ser instanciada diretamente).
- HERANÇA: Cliente e Profissional herdam de Pessoa (reaproveitam nome e contato).
- POLIMORFISMO: descricao(), para_dict() e atualizar() são sobrescritos nas filhas.
- ENCAPSULAMENTO: atributos privados (__) acessados por @property com validação.
- COMPOSIÇÃO: toda Pessoa é dona de um Contato criado no próprio construtor.
- MÉTODO ESTÁTICO: Cliente.cpf_valido().
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Optional

from .excecoes import DadoInvalidoErro
from .utilitarios import somente_digitos, texto_obrigatorio


class Contato:
    """Telefone e e-mail de uma pessoa.

    COMPOSIÇÃO: o Contato é criado DENTRO da Pessoa e não existe sozinho.
    Se a pessoa for apagada, o contato vai junto.
    """

    def __init__(self, telefone: str, email: str = "") -> None:
        self.telefone = telefone  # passa pelo setter, que valida
        self.email = email

    @property
    def telefone(self) -> str:
        return self.__telefone

    @telefone.setter
    def telefone(self, valor: str) -> None:
        digitos = somente_digitos(valor)
        if len(digitos) not in (10, 11):
            raise DadoInvalidoErro("Telefone deve ter DDD + número (10 ou 11 dígitos).")
        self.__telefone = digitos

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, valor: str) -> None:
        email = str(valor or "").strip().lower()
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email):
            raise DadoInvalidoErro("E-mail inválido.")
        self.__email = email

    @property
    def telefone_formatado(self) -> str:
        d = self.__telefone
        return f"({d[:2]}) {d[2:-4]}-{d[-4:]}"

    def __str__(self) -> str:
        return self.telefone_formatado + (f" | {self.email}" if self.email else "")


class Pessoa(ABC):
    """Classe ABSTRATA com o que toda pessoa do sistema tem em comum."""

    def __init__(self, nome: str, telefone: str, email: str = "",
                 id: Optional[int] = None) -> None:
        self.id = id
        self.nome = nome
        self._contato = Contato(telefone, email)  # COMPOSIÇÃO (protegido: as filhas usam)

    @property
    def nome(self) -> str:
        return self.__nome

    @nome.setter
    def nome(self, valor: str) -> None:
        self.__nome = texto_obrigatorio(valor, "Nome")

    @property
    def contato(self) -> Contato:
        return self._contato

    @property
    def primeiro_nome(self) -> str:
        return self.__nome.split()[0]

    def atualizar(self, nome: str, telefone: str, email: str = "") -> None:
        """Muda os dados SOMENTE se todos forem válidos (nada fica pela metade)."""
        novo_nome = texto_obrigatorio(nome, "Nome")
        novo_contato = Contato(telefone, email)  # valida telefone e e-mail
        self.__nome, self._contato = novo_nome, novo_contato

    def para_dict(self) -> dict:
        """Dados básicos para o banco; as filhas acrescentam os delas."""
        return {"id": self.id, "nome": self.nome,
                "telefone": self._contato.telefone, "email": self._contato.email}

    @abstractmethod
    def descricao(self) -> str:
        """POLIMORFISMO: cada tipo de pessoa se descreve do seu jeito."""

    def __str__(self) -> str:
        return self.descricao()


class Cliente(Pessoa):
    """HERANÇA: Cliente É UMA Pessoa (cliente ou paciente)."""

    def __init__(self, nome: str, telefone: str, cpf: str, email: str = "",
                 id: Optional[int] = None) -> None:
        super().__init__(nome, telefone, email, id)  # reaproveita o construtor da mãe
        self.cpf = cpf

    @property
    def cpf(self) -> str:
        return self.__cpf

    @cpf.setter
    def cpf(self, valor: str) -> None:
        if not Cliente.cpf_valido(valor):
            raise DadoInvalidoErro("CPF inválido.")
        self.__cpf = somente_digitos(valor)

    @property
    def cpf_formatado(self) -> str:
        c = self.__cpf
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"

    @staticmethod
    def cpf_valido(cpf: str) -> bool:
        """MÉTODO ESTÁTICO: confere os dois dígitos verificadores do CPF."""
        cpf = somente_digitos(cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        for tamanho in (9, 10):
            soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
            if (soma * 10) % 11 % 10 != int(cpf[tamanho]):
                return False
        return True

    def atualizar(self, nome: str, telefone: str, email: str = "",
                  cpf: Optional[str] = None) -> None:
        """Sobrescrita que ESTENDE a da mãe: valida o CPF e chama super()."""
        if cpf is not None and not Cliente.cpf_valido(cpf):
            raise DadoInvalidoErro("CPF inválido.")
        super().atualizar(nome, telefone, email)
        if cpf is not None:
            self.cpf = cpf

    def para_dict(self) -> dict:
        dados = super().para_dict()
        dados["cpf"] = self.cpf
        return dados

    def descricao(self) -> str:
        return f"Cliente {self.nome} | CPF {self.cpf_formatado} | {self.contato}"


class Profissional(Pessoa):
    """HERANÇA: Profissional É UMA Pessoa (médico, dentista, consultor...)."""

    def __init__(self, nome: str, telefone: str, especialidade: str, email: str = "",
                 id: Optional[int] = None) -> None:
        super().__init__(nome, telefone, email, id)
        self.especialidade = especialidade

    @property
    def especialidade(self) -> str:
        return self.__especialidade

    @especialidade.setter
    def especialidade(self, valor: str) -> None:
        self.__especialidade = texto_obrigatorio(valor, "Especialidade")

    def atualizar(self, nome: str, telefone: str, email: str = "",
                  especialidade: Optional[str] = None) -> None:
        nova = (self.especialidade if especialidade is None
                else texto_obrigatorio(especialidade, "Especialidade"))
        super().atualizar(nome, telefone, email)
        self.__especialidade = nova

    def para_dict(self) -> dict:
        dados = super().para_dict()
        dados["especialidade"] = self.especialidade
        return dados

    def descricao(self) -> str:
        return f"Profissional {self.nome} ({self.especialidade}) | {self.contato}"
