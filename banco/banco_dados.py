"""
Persistência em banco de dados SQLite (vem junto com o Python: módulo sqlite3).

O arquivo agenda.db é criado sozinho na primeira execução, com 4 tabelas:
clientes, profissionais, servicos e agendamentos (esta com chaves estrangeiras).

Conceitos de OO aplicados:
- ENCAPSULAMENTO: a conexão é privada; o resto do sistema só chama salvar(),
  excluir() e carregar_*() e nunca escreve SQL.
- POLIMORFISMO: salvar() funciona com qualquer objeto do sistema, porque cada
  classe sabe gerar os próprios dados com para_dict().
- ATRIBUTO DE CLASSE: TABELAS (qual tabela guarda cada classe).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Union

from modelos.agendamento import Agendamento
from modelos.pessoa import Cliente, Profissional
from modelos.servico import Servico

SQL_CRIAR_TABELAS = """
CREATE TABLE IF NOT EXISTS clientes (
    id        INTEGER PRIMARY KEY,
    nome      TEXT NOT NULL,
    telefone  TEXT NOT NULL,
    email     TEXT,
    cpf       TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS profissionais (
    id             INTEGER PRIMARY KEY,
    nome           TEXT NOT NULL,
    telefone       TEXT NOT NULL,
    email          TEXT,
    especialidade  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS servicos (
    id             INTEGER PRIMARY KEY,
    tipo           TEXT NOT NULL,
    nome           TEXT NOT NULL,
    preco_base     REAL NOT NULL,
    duracao_min    INTEGER NOT NULL,
    taxa_material  REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS agendamentos (
    id               INTEGER PRIMARY KEY,
    cliente_id       INTEGER NOT NULL REFERENCES clientes(id),
    profissional_id  INTEGER NOT NULL REFERENCES profissionais(id),
    servico_id       INTEGER NOT NULL REFERENCES servicos(id),
    data_hora        TEXT NOT NULL,
    status           TEXT NOT NULL,
    observacao       TEXT
);
"""


class BancoDeDados:
    # ATRIBUTO DE CLASSE: em qual tabela cada tipo de objeto é guardado
    TABELAS = ((Cliente, "clientes"), (Profissional, "profissionais"),
               (Servico, "servicos"), (Agendamento, "agendamentos"))

    def __init__(self, caminho: Union[str, Path] = "agenda.db") -> None:
        self.__caminho = str(caminho)
        self.__conexao = sqlite3.connect(self.__caminho)
        self.__conexao.row_factory = sqlite3.Row  # linhas acessadas pelo nome da coluna
        self.__conexao.execute("PRAGMA foreign_keys = ON")
        self.__conexao.executescript(SQL_CRIAR_TABELAS)

    @property
    def caminho(self) -> str:
        return self.__caminho

    # ------------------------- gravação -------------------------
    def salvar(self, objeto) -> None:
        """INSERT do objeto novo ou UPDATE do que já existe (UPSERT)."""
        tabela = self.__tabela_de(objeto)
        dados = objeto.para_dict()  # POLIMORFISMO: cada classe gera os seus dados
        colunas = ", ".join(dados)
        marcadores = ", ".join("?" for _ in dados)
        atualizacao = ", ".join(f"{coluna} = excluded.{coluna}" for coluna in dados if coluna != "id")
        sql = (f"INSERT INTO {tabela} ({colunas}) VALUES ({marcadores}) "
               f"ON CONFLICT(id) DO UPDATE SET {atualizacao}")
        with self.__conexao:  # transação: COMMIT se der certo, ROLLBACK se der erro
            self.__conexao.execute(sql, tuple(dados.values()))

    def excluir(self, objeto) -> None:
        tabela = self.__tabela_de(objeto)
        with self.__conexao:
            self.__conexao.execute(f"DELETE FROM {tabela} WHERE id = ?", (objeto.id,))

    # ------------------------- leitura -------------------------
    def carregar_clientes(self) -> List[Cliente]:
        return [Cliente(l["nome"], l["telefone"], l["cpf"], l["email"] or "", id=l["id"])
                for l in self.__selecionar("clientes")]

    def carregar_profissionais(self) -> List[Profissional]:
        return [Profissional(l["nome"], l["telefone"], l["especialidade"], l["email"] or "",
                             id=l["id"])
                for l in self.__selecionar("profissionais")]

    def carregar_servicos(self) -> List[Servico]:
        return [Servico.criar(l["tipo"], l["nome"], l["preco_base"], l["duracao_min"],
                              l["taxa_material"], id=l["id"])  # FÁBRICA
                for l in self.__selecionar("servicos")]

    def carregar_agendamentos(self) -> List[Dict]:
        """Devolve os dados crus: quem recria os objetos é a Agenda (composição)."""
        return [dict(linha) for linha in self.__selecionar("agendamentos")]

    def consultar_tabela(self, tabela: str) -> Tuple[List[str], List[tuple]]:
        """Colunas + linhas de uma tabela (usado na opção 'Banco de dados' do menu)."""
        cursor = self.__conexao.execute(f"SELECT * FROM {self.__validar_tabela(tabela)} ORDER BY id")
        colunas = [descricao[0] for descricao in cursor.description]
        return colunas, [tuple(linha) for linha in cursor.fetchall()]

    def contar(self, tabela: str) -> int:
        sql = f"SELECT COUNT(*) FROM {self.__validar_tabela(tabela)}"
        return self.__conexao.execute(sql).fetchone()[0]

    def nomes_tabelas(self) -> List[str]:
        return [tabela for _, tabela in self.TABELAS]

    def fechar(self) -> None:
        self.__conexao.close()

    # ------------------------- privados -------------------------
    def __selecionar(self, tabela: str) -> List[sqlite3.Row]:
        return self.__conexao.execute(f"SELECT * FROM {tabela} ORDER BY id").fetchall()

    def __tabela_de(self, objeto) -> str:
        for classe, tabela in self.TABELAS:
            if isinstance(objeto, classe):
                return tabela
        raise TypeError(f"Não sei salvar objetos do tipo {type(objeto).__name__}.")

    def __validar_tabela(self, tabela: str) -> str:
        if tabela not in self.nomes_tabelas():
            raise ValueError(f"Tabela desconhecida: {tabela}")
        return tabela
