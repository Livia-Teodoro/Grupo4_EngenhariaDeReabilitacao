"""
services/visualizacao.py

Camada responsável apenas pelo Matplotlib:
recebe a matriz, atualiza a figura, e devolve a Figure
para a interface exibir embutida (sem abrir janela externa).

Nunca acessa banco. Nunca acessa interface diretamente.
"""

from __future__ import annotations

import io
from typing import List, Optional

import matplotlib

matplotlib.use("Agg")  # backend sem janela, seguro para rodar em thread/servidor

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

Matriz = List[List[float]]

PALETAS_DISPONIVEIS = [
    "inferno", "viridis", "plasma", "magma", "hot", "jet", "turbo",
]

INTERPOLACOES_DISPONIVEIS = [
    "nearest", "bilinear", "bicubic", "gaussian",
]


class Visualizacao:
    """
    Mantém uma única Figure/Axes reaproveitada entre atualizações
    (mais eficiente do que recriar a figura inteira a cada leitura).
    """

    def __init__(
        self,
        paleta: str = "inferno",
        interpolacao: str = "bicubic",
        figsize: tuple = (6.4, 5.2),
        dpi: int = 100,
    ):
        self.paleta = paleta if paleta in PALETAS_DISPONIVEIS else "inferno"
        self.interpolacao = interpolacao
        self._zoom = 1.0  # fator de "zoom" lógico (recorte central da matriz)

        self.figure: Figure = plt.figure(figsize=figsize, dpi=dpi)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

        self._im = None
        self._colorbar = None

    # ---------- Configuração ----------

    def definir_paleta(self, paleta: str) -> None:
        if paleta in PALETAS_DISPONIVEIS:
            self.paleta = paleta
            if self._im is not None:
                self._im.set_cmap(paleta)

    def definir_interpolacao(self, interpolacao: str) -> None:
        if interpolacao in INTERPOLACOES_DISPONIVEIS:
            self.interpolacao = interpolacao

    def definir_zoom(self, fator: float) -> None:
        """fator entre 1.0 (matriz completa) e <1.0 (recorte central, mais zoom)."""
        self._zoom = max(0.2, min(1.0, fator))

    # ---------- Atualização ----------

    def _aplicar_zoom(self, matriz):
        if self._zoom >= 0.999:
            return matriz
        h, w = matriz.shape
        novo_h, novo_w = int(h * self._zoom), int(w * self._zoom)
        ini_h, ini_w = (h - novo_h) // 2, (w - novo_w) // 2
        return matriz[ini_h: ini_h + novo_h, ini_w: ini_w + novo_w]

    def atualizar(self, matriz_interpolada, vmax: Optional[float] = None):
        """
        Redesenha o mapa térmico com a matriz já interpolada/processada.
        `vmax` permite fixar a escala de cores (ex.: limite clínico),
        evitando que a escala "pule" a cada leitura.
        """
        dados = self._aplicar_zoom(matriz_interpolada)

        if self._im is None:
            self._im = self.ax.imshow(
                dados,
                cmap=self.paleta,
                interpolation=self.interpolacao,
                vmin=0,
                vmax=vmax,
                aspect="auto",
            )
            self._colorbar = self.figure.colorbar(self._im, ax=self.ax)
            self._colorbar.set_label("Pressão (un. sensor)")
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_title("Mapa de Distribuição de Pressão")
        else:
            self._im.set_data(dados)
            self._im.set_cmap(self.paleta)
            self._im.set_interpolation(self.interpolacao)
            if vmax:
                self._im.set_clim(0, vmax)
            else:
                # Sem vmax fixo: a escala acompanha o valor máximo do quadro atual,
                # evitando que o mapa "estagne" com uma escala antiga.
                self._im.set_clim(0, max(float(dados.max()), 1.0))

        self.figure.canvas.draw()

    # ---------- Exportação ----------

    def obter_figura(self) -> Figure:
        return self.figure

    def obter_png_bytes(self) -> bytes:
        buf = io.BytesIO()
        self.figure.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        return buf.read()

    def salvar_imagem(self, caminho: str) -> None:
        self.figure.savefig(caminho, bbox_inches="tight", dpi=150)

    def fechar(self) -> None:
        plt.close(self.figure)
