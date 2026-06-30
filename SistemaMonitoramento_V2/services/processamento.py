"""
services/processamento.py

Camada de processamento de dados. Recebe a matriz crua do Receptor e produz:

    - matriz interpolada (maior resolução, mais suave para o mapa térmico)
    - matriz normalizada
    - estatísticas (máxima, média, mínima)
    - tempo de estabilidade (há quanto tempo a distribuição de pressão
      não muda de forma significativa, indicando ausência de movimento)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from scipy.ndimage import zoom as scipy_zoom

Matriz = List[List[float]]


@dataclass
class Estatisticas:
    maxima: float
    media: float
    minima: float


class Processamento:
    """
    Mantém estado entre leituras (para calcular tempo de estabilidade),
    por isso é instanciado uma vez por sessão de monitoramento, e não
    chamado como funções puras soltas.
    """

    def __init__(self, limiar_estabilidade: float = 15.0):
        """
        limiar_estabilidade: variação média (em unidades de pressão crua)
        acima da qual consideramos que houve movimento/mudança de postura,
        reiniciando a contagem de tempo de estabilidade.
        """
        self.limiar_estabilidade = limiar_estabilidade
        self._ultima_matriz: Optional[np.ndarray] = None
        self._inicio_estabilidade: float = time.monotonic()

    # ---------- Interpolação / normalização ----------

    @staticmethod
    def interpolar_matriz(matriz: Matriz, fator: int = 8) -> np.ndarray:
        """
        Aumenta a resolução da matriz de sensores (ex.: 8x8 -> 64x64)
        usando interpolação suave (spline cúbica via scipy.ndimage.zoom),
        deixando o mapa térmico visualmente contínuo.
        """
        arr = np.asarray(matriz, dtype=float)
        if arr.size == 0:
            return arr
        return scipy_zoom(arr, zoom=fator, order=3)

    @staticmethod
    def normalizar(matriz: np.ndarray, maximo_escala: Optional[float] = None) -> np.ndarray:
        """
        Normaliza para o intervalo [0, 1]. Se `maximo_escala` for informado
        (ex.: limite máximo calibrado do sensor), normaliza por ele;
        caso contrário, normaliza pelo valor máximo presente na própria matriz.
        """
        arr = np.asarray(matriz, dtype=float)
        if arr.size == 0:
            return arr
        topo = maximo_escala if maximo_escala else arr.max()
        if topo <= 0:
            return np.zeros_like(arr)
        return np.clip(arr / topo, 0, 1)

    # ---------- Estatísticas ----------

    @staticmethod
    def calcular_estatisticas(matriz: Matriz) -> Estatisticas:
        arr = np.asarray(matriz, dtype=float)
        if arr.size == 0:
            return Estatisticas(0.0, 0.0, 0.0)
        return Estatisticas(
            maxima=float(arr.max()),
            media=float(arr.mean()),
            minima=float(arr.min()),
        )

    # ---------- Tempo de estabilidade ----------

    def atualizar_estabilidade(self, matriz: Matriz) -> float:
        """
        Compara a leitura atual com a anterior. Se a diferença média
        ultrapassar o limiar, considera que o paciente se moveu e reinicia
        o contador. Retorna o tempo de estabilidade atual, em segundos.
        """
        arr = np.asarray(matriz, dtype=float)
        agora = time.monotonic()

        if self._ultima_matriz is None or self._ultima_matriz.shape != arr.shape:
            self._ultima_matriz = arr
            self._inicio_estabilidade = agora
            return 0.0

        diferenca_media = float(np.mean(np.abs(arr - self._ultima_matriz)))
        self._ultima_matriz = arr

        if diferenca_media > self.limiar_estabilidade:
            self._inicio_estabilidade = agora

        return agora - self._inicio_estabilidade

    def reiniciar_estabilidade(self) -> None:
        """Chamado pelo Controller ao confirmar um reposicionamento."""
        self._inicio_estabilidade = time.monotonic()
        self._ultima_matriz = None
