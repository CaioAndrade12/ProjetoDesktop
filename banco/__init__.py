"""Camada de PERSISTÊNCIA: banco SQLite e dados de exemplo."""
from .banco_dados import BancoDeDados
from .dados_exemplo import popular_dados_exemplo

__all__ = ["BancoDeDados", "popular_dados_exemplo"]
