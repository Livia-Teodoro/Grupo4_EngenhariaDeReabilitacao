"""
models/paciente.py

Representa um paciente e centraliza os cálculos derivados
(idade, IMC, classificação do IMC) pedidos na especificação,
para que tanto controllers quanto views usem a mesma lógica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Paciente:
    nome: str
    data_nascimento: Optional[str] = None   
    sexo: Optional[str] = None             
    altura: Optional[float] = None          
    peso: Optional[float] = None            
    mobilidade: Optional[str] = None        
    condicao: Optional[str] = None          
    observacoes: Optional[str] = None
    foto: Optional[str] = None              # caminho do arquivo de imagem
    id: Optional[int] = None                # chave primária no banco de dados
    criado_em: Optional[str] = None         # timestamp de criação preenchido automaticamente pelo SQLite

    # ---------- Campos calculados ----------

    @property
    def idade(self) -> Optional[int]:
        if not self.data_nascimento:
            return None
        try:
            nasc = datetime.strptime(self.data_nascimento, "%Y-%m-%d").date()
        except ValueError:
            return None
        hoje = date.today()
        idade = hoje.year - nasc.year - (
            (hoje.month, hoje.day) < (nasc.month, nasc.day)
        )
        return idade

    @property
    def imc(self) -> Optional[float]:
        if not self.altura or not self.peso or self.altura <= 0:
            return None
        imc = self.peso / (self.altura ** 2)
        return round(imc, 1)

    @property
    def classificacao_imc(self) -> Optional[str]:
        imc = self.imc
        if imc is None:
            return None
        if imc < 18.5:
            return "Abaixo do peso"
        if imc < 25:
            return "Peso normal"
        if imc < 30:
            return "Sobrepeso"
        if imc < 35:
            return "Obesidade grau I"
        if imc < 40:
            return "Obesidade grau II"
        return "Obesidade grau III"

    # ---------- Conversões ----------

    @staticmethod
    def from_row(row) -> "Paciente":
        """Constrói um Paciente a partir de uma sqlite3.Row."""
        return Paciente(
            id=row["id"],
            nome=row["nome"],
            data_nascimento=row["data_nascimento"],
            sexo=row["sexo"],
            altura=row["altura"],
            peso=row["peso"],
            mobilidade=row["mobilidade"],
            condicao=row["condicao"],
            observacoes=row["observacoes"],
            foto=row["foto"],
            criado_em=row["criado_em"] if "criado_em" in row.keys() else None,
        )

    def to_dict(self) -> dict:
        d = {
            "nome": self.nome,
            "data_nascimento": self.data_nascimento,
            "sexo": self.sexo,
            "altura": self.altura,
            "peso": self.peso,
            "mobilidade": self.mobilidade,
            "condicao": self.condicao,
            "observacoes": self.observacoes,
            "foto": self.foto,
        }
        return d
