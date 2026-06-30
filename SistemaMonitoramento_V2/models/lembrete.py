"""
models/lembrete.py

Representa um lembrete de cuidado para um paciente.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


CATEGORIAS_LEMBRETE = [
    "Medicação",
    "Alimentação",
    "Banho",
    "Consulta médica",
    "Fisioterapia",
    "Reposicionamento",
    "Hidratação",
    "Outro",
]

ICONES_CATEGORIA = {
    "Medicação": "medication",
    "Alimentação": "restaurant",
    "Banho": "water_drop",
    "Consulta médica": "local_hospital",
    "Fisioterapia": "accessibility_new",
    "Reposicionamento": "airline_seat_flat",
    "Hidratação": "local_drink",
    "Outro": "notifications",
}

CORES_CATEGORIA = {
    "Medicação": "#8b5cf6",
    "Alimentação": "#f59e0b",
    "Banho": "#06b6d4",
    "Consulta médica": "#ef4444",
    "Fisioterapia": "#10b981",
    "Reposicionamento": "#2d6cdf",
    "Hidratação": "#3b82f6",
    "Outro": "#6b7280",
}


@dataclass
class Lembrete:
    paciente_id: int
    categoria: str
    descricao: str
    hora: str           # formato "HH:MM"
    repetir: str        # "Nunca" | "Diário" | "Semanal"
    ativo: bool = True
    id: Optional[int] = None
    criado_em: Optional[str] = None

    @staticmethod
    def from_row(row) -> "Lembrete":
        return Lembrete(
            id=row["id"],
            paciente_id=row["paciente_id"],
            categoria=row["categoria"],
            descricao=row["descricao"],
            hora=row["hora"],
            repetir=row["repetir"],
            ativo=bool(row["ativo"]),
            criado_em=row["criado_em"] if "criado_em" in row.keys() else None,
        )
