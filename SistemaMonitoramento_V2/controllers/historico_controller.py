"""
controllers/historico_controller.py

Consulta e exportação do histórico de reposicionamentos de um paciente.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

import database
from models.reposicionamento import Reposicionamento


class HistoricoController:

    def listar(
        self,
        paciente_id: int,
        termo_busca: str = "",
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
    ) -> List[Reposicionamento]:
        clausulas = ["paciente_id = ?"]
        parametros: list = [paciente_id]

        if termo_busca:
            clausulas.append("(observacao LIKE ? OR data LIKE ?)")
            parametros += [f"%{termo_busca}%", f"%{termo_busca}%"]
        if data_inicio:
            clausulas.append("data >= ?")
            parametros.append(data_inicio)
        if data_fim:
            clausulas.append("data <= ?")
            parametros.append(data_fim)

        sql = (
            "SELECT * FROM reposicionamentos WHERE "
            + " AND ".join(clausulas)
            + " ORDER BY data DESC, hora DESC"
        )

        with database.conexao() as conn:
            rows = conn.execute(sql, parametros).fetchall()
        return [Reposicionamento.from_row(r) for r in rows]

    def exportar_csv(self, paciente_id: int, caminho: str, **filtros) -> None:
        registros = self.listar(paciente_id, **filtros)
        df = pd.DataFrame(
            [
                {
                    "Data": r.data,
                    "Hora": r.hora,
                    "Tempo sentado": r.tempo_sentado_formatado,
                    "Pressão máxima": r.pressao_maxima,
                    "Pressão média": r.pressao_media,
                    "Observação": r.observacao or "",
                }
                for r in registros
            ]
        )
        df.to_csv(caminho, index=False, encoding="utf-8")

    def exportar_pdf(self, paciente_id: int, caminho: str, nome_paciente: str = "", **filtros) -> None:
        registros = self.listar(paciente_id, **filtros)

        doc = SimpleDocTemplate(caminho, pagesize=A4)
        estilos = getSampleStyleSheet()
        elementos = [
            Paragraph(f"Histórico de Reposicionamentos - {nome_paciente}", estilos["Title"]),
            Spacer(1, 0.5 * cm),
        ]

        dados_tabela = [["Data", "Hora", "Tempo sentado", "Pressão máx.", "Pressão média", "Observação"]]
        for r in registros:
            dados_tabela.append(
                [
                    r.data, r.hora, r.tempo_sentado_formatado,
                    f"{r.pressao_maxima:.1f}" if r.pressao_maxima is not None else "-",
                    f"{r.pressao_media:.1f}" if r.pressao_media is not None else "-",
                    r.observacao or "-",
                ]
            )

        tabela = Table(dados_tabela, repeatRows=1)
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f4f7")]),
                ]
            )
        )
        elementos.append(tabela)
        doc.build(elementos)
