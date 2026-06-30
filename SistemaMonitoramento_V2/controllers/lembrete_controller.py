"""
controllers/lembrete_controller.py

CRUD e verificação de lembretes de cuidado para pacientes.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import database
from models.lembrete import Lembrete


class LembreteController:

    def listar(self, paciente_id: int, apenas_ativos: bool = True) -> List[Lembrete]:
        sql = "SELECT * FROM lembretes WHERE paciente_id = ?"
        params: list = [paciente_id]
        if apenas_ativos:
            sql += " AND ativo = 1"
        sql += " ORDER BY hora ASC"
        with database.conexao() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [Lembrete.from_row(r) for r in rows]

    def criar(self, lembrete: Lembrete) -> Lembrete:
        sql = """
            INSERT INTO lembretes (paciente_id, categoria, descricao, hora, repetir, ativo)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        with database.conexao() as conn:
            cur = conn.execute(sql, (
                lembrete.paciente_id, lembrete.categoria, lembrete.descricao,
                lembrete.hora, lembrete.repetir, int(lembrete.ativo),
            ))
            conn.commit()
            lembrete.id = cur.lastrowid
        return lembrete

    def atualizar(self, lembrete: Lembrete) -> None:
        sql = """
            UPDATE lembretes
            SET categoria = ?, descricao = ?, hora = ?, repetir = ?, ativo = ?
            WHERE id = ?
        """
        with database.conexao() as conn:
            conn.execute(sql, (
                lembrete.categoria, lembrete.descricao, lembrete.hora,
                lembrete.repetir, int(lembrete.ativo), lembrete.id,
            ))
            conn.commit()

    def excluir(self, lembrete_id: int) -> None:
        with database.conexao() as conn:
            conn.execute("DELETE FROM lembretes WHERE id = ?", (lembrete_id,))
            conn.commit()

    def registrar_confirmacao(self, lembrete_id: int, paciente_id: int, observacao: str = "") -> None:
        """Grava no log que o cuidado foi realizado."""
        agora = datetime.now()
        sql = """
            INSERT INTO log_lembretes (lembrete_id, paciente_id, data, hora, observacao)
            VALUES (?, ?, ?, ?, ?)
        """
        with database.conexao() as conn:
            conn.execute(sql, (
                lembrete_id, paciente_id,
                agora.strftime("%Y-%m-%d"), agora.strftime("%H:%M:%S"),
                observacao,
            ))
            conn.commit()

    def verificar_lembretes_agora(self, paciente_id: int, tolerancia_minutos: int = 1) -> List[Lembrete]:
        """
        Retorna lembretes que devem disparar agora
        (hora atual dentro da janela de tolerância e que ainda não foram
        confirmados hoje nesse horário).
        """
        agora = datetime.now()
        hora_atual = agora.strftime("%H:%M")
        h, m = map(int, hora_atual.split(":"))
        data_hoje = agora.strftime("%Y-%m-%d")

        # Gera janela de horários tolerados (hora_atual ± tolerancia_minutos)
        horarios_janela = set()
        for delta in range(-tolerancia_minutos, tolerancia_minutos + 1):
            minuto_total = h * 60 + m + delta
            minuto_total = max(0, min(1439, minuto_total))
            hj, mj = divmod(minuto_total, 60)
            horarios_janela.add(f"{hj:02d}:{mj:02d}")

        lembretes_ativos = self.listar(paciente_id, apenas_ativos=True)
        resultado = []
        for lem in lembretes_ativos:
            if lem.hora not in horarios_janela:
                continue
            # Verifica se já foi confirmado hoje neste horário
            with database.conexao() as conn:
                ja_confirmado = conn.execute(
                    """SELECT 1 FROM log_lembretes
                       WHERE lembrete_id = ? AND data = ? AND hora LIKE ?
                       LIMIT 1""",
                    (lem.id, data_hoje, f"{lem.hora}%"),
                ).fetchone()
            if not ja_confirmado:
                resultado.append(lem)

        return resultado
