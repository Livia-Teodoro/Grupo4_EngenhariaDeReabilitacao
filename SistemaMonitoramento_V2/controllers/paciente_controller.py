"""
controllers/paciente_controller.py

Regras relacionadas a pacientes, isolando as
views de qualquer SQL direto.
"""

from __future__ import annotations

from typing import List, Optional

import database
from models.paciente import Paciente


class PacienteController:

    def listar(self, termo_busca: str = "") -> List[Paciente]:
        with database.conexao() as conn:
            if termo_busca:
                rows = conn.execute(
                    "SELECT * FROM pacientes WHERE nome LIKE ? ORDER BY nome",
                    (f"%{termo_busca}%",),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM pacientes ORDER BY nome"
                ).fetchall()
        return [Paciente.from_row(r) for r in rows]

    def obter(self, paciente_id: int) -> Optional[Paciente]:
        with database.conexao() as conn:
            row = conn.execute(
                "SELECT * FROM pacientes WHERE id = ?", (paciente_id,)
            ).fetchone()
        return Paciente.from_row(row) if row else None

    def criar(self, paciente: Paciente) -> Paciente:
        dados = paciente.to_dict()
        with database.conexao() as conn:
            cur = conn.execute(
                """INSERT INTO pacientes
                   (nome, data_nascimento, sexo, altura, peso, mobilidade,
                    condicao, observacoes, foto)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    dados["nome"], dados["data_nascimento"], dados["sexo"],
                    dados["altura"], dados["peso"], dados["mobilidade"],
                    dados["condicao"], dados["observacoes"], dados["foto"],
                ),
            )
            conn.commit()
            paciente.id = cur.lastrowid
        return paciente

    def atualizar(self, paciente: Paciente) -> None:
        if paciente.id is None:
            raise ValueError("Paciente sem id não pode ser atualizado.")
        dados = paciente.to_dict()
        with database.conexao() as conn:
            conn.execute(
                """UPDATE pacientes SET
                   nome=?, data_nascimento=?, sexo=?, altura=?, peso=?,
                   mobilidade=?, condicao=?, observacoes=?, foto=?
                   WHERE id=?""",
                (
                    dados["nome"], dados["data_nascimento"], dados["sexo"],
                    dados["altura"], dados["peso"], dados["mobilidade"],
                    dados["condicao"], dados["observacoes"], dados["foto"],
                    paciente.id,
                ),
            )
            conn.commit()

    def excluir(self, paciente_id: int) -> None:
        with database.conexao() as conn:
            conn.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))
            conn.commit()
