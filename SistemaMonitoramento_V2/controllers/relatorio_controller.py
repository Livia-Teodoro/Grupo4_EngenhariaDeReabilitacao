"""
controllers/relatorio_controller.py

Geração dos relatórios resumidos (diário, semanal, mensal): 
número de reposicionamentos, tempo médio sentado,
maior pressão registrada, gráfico temporal e exportação em PDF.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer

import database


@dataclass
class ResumoRelatorio:
    periodo_inicio: str
    periodo_fim: str
    numero_reposicionamentos: int
    tempo_medio_sentado_seg: float
    maior_pressao: float
    grafico_png: Optional[bytes] = None


class RelatorioController:

    # ---------- Cálculo dos resumos ----------

    def resumo_diario(self, paciente_id: int, dia: Optional[date] = None) -> ResumoRelatorio:
        dia = dia or date.today()
        return self._resumo_periodo(paciente_id, dia, dia)

    def resumo_semanal(self, paciente_id: int, dia_referencia: Optional[date] = None) -> ResumoRelatorio:
        dia_referencia = dia_referencia or date.today()
        inicio = dia_referencia - timedelta(days=dia_referencia.weekday())
        fim = inicio + timedelta(days=6)
        return self._resumo_periodo(paciente_id, inicio, fim)

    def resumo_mensal(self, paciente_id: int, ano: Optional[int] = None, mes: Optional[int] = None) -> ResumoRelatorio:
        hoje = date.today()
        ano = ano or hoje.year
        mes = mes or hoje.month
        inicio = date(ano, mes, 1)
        if mes == 12:
            fim = date(ano, 12, 31)
        else:
            fim = date(ano, mes + 1, 1) - timedelta(days=1)
        return self._resumo_periodo(paciente_id, inicio, fim)

    def _resumo_periodo(self, paciente_id: int, inicio: date, fim: date) -> ResumoRelatorio:
        with database.conexao() as conn:
            reposicionamentos = conn.execute(
                """SELECT * FROM reposicionamentos
                   WHERE paciente_id = ? AND data BETWEEN ? AND ?
                   ORDER BY data, hora""",
                (paciente_id, inicio.isoformat(), fim.isoformat()),
            ).fetchall()
            leituras = conn.execute(
                """SELECT data_hora, pressao_maxima FROM leituras
                   WHERE paciente_id = ? AND date(data_hora) BETWEEN ? AND ?
                   ORDER BY data_hora""",
                (paciente_id, inicio.isoformat(), fim.isoformat()),
            ).fetchall()

        numero = len(reposicionamentos)
        tempos = [r["tempo_sentado"] for r in reposicionamentos if r["tempo_sentado"] is not None]
        tempo_medio = sum(tempos) / len(tempos) if tempos else 0.0
        maior_pressao = max((l["pressao_maxima"] for l in leituras), default=0.0)

        grafico = self._gerar_grafico_temporal(leituras) if leituras else None

        return ResumoRelatorio(
            periodo_inicio=inicio.isoformat(),
            periodo_fim=fim.isoformat(),
            numero_reposicionamentos=numero,
            tempo_medio_sentado_seg=tempo_medio,
            maior_pressao=maior_pressao,
            grafico_png=grafico,
        )

    # ---------- Gráfico temporal ----------

    def _gerar_grafico_temporal(self, leituras) -> bytes:
        horarios = [datetime.fromisoformat(l["data_hora"]) for l in leituras]
        valores = [l["pressao_maxima"] for l in leituras]

        fig, ax = plt.subplots(figsize=(7, 3), dpi=120)
        ax.plot(horarios, valores, color="#d35400", linewidth=1.5)
        ax.set_title("Pressão máxima ao longo do período")
        ax.set_ylabel("Pressão (un. sensor)")
        ax.grid(alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    # ---------- Exportação em PDF ----------

    def exportar_pdf(self, resumo: ResumoRelatorio, nome_paciente: str, caminho: str,
                      mapa_png: Optional[bytes] = None) -> None:
        doc = SimpleDocTemplate(caminho, pagesize=A4)
        estilos = getSampleStyleSheet()
        elementos = [
            Paragraph(f"Relatório de Monitoramento - {nome_paciente}", estilos["Title"]),
            Paragraph(f"Período: {resumo.periodo_inicio} a {resumo.periodo_fim}", estilos["Normal"]),
            Spacer(1, 0.5 * cm),
            Paragraph(f"Número de reposicionamentos: {resumo.numero_reposicionamentos}", estilos["Normal"]),
            Paragraph(
                f"Tempo médio sentado: {resumo.tempo_medio_sentado_seg / 60:.1f} minutos",
                estilos["Normal"],
            ),
            Paragraph(f"Maior pressão registrada: {resumo.maior_pressao:.1f}", estilos["Normal"]),
            Spacer(1, 0.5 * cm),
        ]

        if resumo.grafico_png:
            img_buf = io.BytesIO(resumo.grafico_png)
            elementos.append(RLImage(img_buf, width=16 * cm, height=7 * cm))
            elementos.append(Spacer(1, 0.5 * cm))

        if mapa_png:
            elementos.append(Paragraph("Último mapa de pressão registrado:", estilos["Heading3"]))
            mapa_buf = io.BytesIO(mapa_png)
            elementos.append(RLImage(mapa_buf, width=12 * cm, height=10 * cm))

        doc.build(elementos)
