"""
models/leitura.py

Representa uma leitura periódica de pressão salva durante o
monitoramento (estatísticas resumidas; a matriz completa fica
reservada para uso futuro, conforme a especificação).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Leitura:
    paciente_id: int
    pressao_maxima: float
    pressao_media: float
    pressao_minima: float
    data_hora: Optional[str] = None
    matriz_json: Optional[str] = None
    id: Optional[int] = None

    @staticmethod
    def from_row(row) -> "Leitura":
        return Leitura(
            id=row["id"],
            paciente_id=row["paciente_id"],
            data_hora=row["data_hora"],
            pressao_maxima=row["pressao_maxima"],
            pressao_media=row["pressao_media"],
            pressao_minima=row["pressao_minima"],
            matriz_json=row["matriz_json"] if "matriz_json" in row.keys() else None,
        )
