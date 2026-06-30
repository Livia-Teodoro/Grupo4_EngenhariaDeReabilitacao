"""
models/reposicionamento.py

Representa um evento de reposicionamento confirmado pelo
cuidador/profissional de saúde durante o monitoramento.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Reposicionamento:
    paciente_id: int
    data: str               # "YYYY-MM-DD"
    hora: str               # "HH:MM:SS"
    tempo_sentado: int      # segundos desde o reposicionamento anterior
    pressao_maxima: Optional[float] = None
    pressao_media: Optional[float] = None
    pressao_minima: Optional[float] = None
    observacao: Optional[str] = None
    id: Optional[int] = None

    @property
    def tempo_sentado_formatado(self) -> str:
        """Converte segundos em 'Hh MMm SSs' para exibição em tabelas/relatórios."""
        if self.tempo_sentado is None:
            return "-"
        total = int(self.tempo_sentado)
        h, resto = divmod(total, 3600)
        m, s = divmod(resto, 60)
        if h:
            return f"{h}h {m:02d}m {s:02d}s"
        return f"{m}m {s:02d}s"

    @staticmethod
    def from_row(row) -> "Reposicionamento":
        return Reposicionamento(
            id=row["id"],
            paciente_id=row["paciente_id"],
            data=row["data"],
            hora=row["hora"],
            tempo_sentado=row["tempo_sentado"],
            pressao_maxima=row["pressao_maxima"],
            pressao_media=row["pressao_media"],
            pressao_minima=row["pressao_minima"],
            observacao=row["observacao"],
        )
