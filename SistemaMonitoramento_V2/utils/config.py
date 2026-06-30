"""
utils/config.py

Camada de configuração do sistema.

Mantém as configurações ajustáveis pelo usuário (tela "Configurações")
persistidas em um arquivo JSON simples dentro de data/config.json.

Mantida isolada de banco de dados / interface para que possa ser
reaproveitada por qualquer camada (services, controllers, views).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")


@dataclass
class Configuracoes:
    """Representa todas as configurações ajustáveis do sistema."""

    # Comunicação com a ESP32
    esp32_ip: str = "192.168.4.1"
    esp32_porta: int = 8080

    # Regras de negócio / risco
    tempo_maximo_permitido: int = 120          # minutos sentado/posição até risco vermelho
    tempo_estabilidade: int = 30               # minutos sem mudança até alerta amarelo

    # Aparência
    tema: str = "claro"                        # "claro" | "escuro"
    paleta_mapa: str = "inferno"                # paleta padrão do Matplotlib

    # Aquisição
    frequencia_atualizacao: float = 1.0         # segundos entre leituras

    # Sensores (não exposto mas necessário para interpolação/visualização e para o simulador)
    sensor_linhas: int = 8
    sensor_colunas: int = 8

    # Modo de operação
    modo_simulacao: bool = True                 # True = usa SimuladorESP32 (sem hardware)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Configuracoes":
        campos_validos = Configuracoes().to_dict().keys()
        filtrado = {k: v for k, v in data.items() if k in campos_validos}
        return Configuracoes(**filtrado)


def carregar_configuracoes() -> Configuracoes:
    """Lê data/config.json. Se não existir, cria com valores padrão."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        cfg = Configuracoes()
        salvar_configuracoes(cfg)
        return cfg

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return Configuracoes.from_dict(dados)
    except (json.JSONDecodeError, OSError):
        # Arquivo corrompido: recria com padrão para não travar o sistema.
        cfg = Configuracoes()
        salvar_configuracoes(cfg)
        return cfg


def salvar_configuracoes(cfg: Configuracoes) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, indent=4, ensure_ascii=False)
