"""
database.py

Camada única de acesso a baixo nível ao SQLite.

Responsabilidades:
    - Criar/garantir o schema (tabelas pacientes, reposicionamentos, leituras).
    - Fornecer uma conexão configurada (row_factory, foreign_keys).

O arquivo do banco vive em data/monitoramento.db, ao lado de config.json.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "monitoramento.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    data_nascimento TEXT,
    sexo            TEXT,
    altura          REAL,
    peso            REAL,
    mobilidade      TEXT,
    condicao        TEXT,
    observacoes     TEXT,
    foto            TEXT,
    criado_em       TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reposicionamentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL,
    data            TEXT    NOT NULL,
    hora            TEXT    NOT NULL,
    tempo_sentado   INTEGER,            -- segundos
    pressao_maxima  REAL,
    pressao_media   REAL,
    pressao_minima  REAL,
    observacao      TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS leituras (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL,
    data_hora       TEXT    NOT NULL DEFAULT (datetime('now')),
    pressao_maxima  REAL,
    pressao_media   REAL,
    pressao_minima  REAL,
    matriz_json     TEXT,               -- reservado para uso futuro (matriz completa)
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reposicionamentos_paciente
    ON reposicionamentos (paciente_id);

CREATE INDEX IF NOT EXISTS idx_leituras_paciente
    ON leituras (paciente_id);

CREATE TABLE IF NOT EXISTS lembretes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL,
    categoria       TEXT    NOT NULL,
    descricao       TEXT    NOT NULL,
    hora            TEXT    NOT NULL,   -- "HH:MM"
    repetir         TEXT    NOT NULL DEFAULT 'Diário',
    ativo           INTEGER NOT NULL DEFAULT 1,
    criado_em       TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS log_lembretes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lembrete_id     INTEGER NOT NULL,
    paciente_id     INTEGER NOT NULL,
    data            TEXT    NOT NULL,
    hora            TEXT    NOT NULL,
    observacao      TEXT,
    FOREIGN KEY (lembrete_id) REFERENCES lembretes (id) ON DELETE CASCADE,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lembretes_paciente
    ON lembretes (paciente_id);

CREATE INDEX IF NOT EXISTS idx_log_lembretes_paciente
    ON log_lembretes (paciente_id);
"""


def inicializar_banco() -> None:
    """Cria o diretório data/ e as tabelas, se ainda não existirem."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def get_connection() -> sqlite3.Connection:
    """Abre uma conexão nova e configurada. Chamador deve fechar/usar `with`."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def conexao():
    """Context manager: `with conexao() as conn: ...` fecha a conexão sozinho."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
