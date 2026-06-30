"""
controllers/monitoramento_controller.py

O Controller principal, que integra o fluxo completo:

    ESP32 -> Receptor -> Processamento -> Visualização -> Interface

Roda a aquisição em uma thread própria, e notifica a view através de um callback,
mantendo este módulo livre de qualquer import do Flet.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional

import database
from models.leitura import Leitura
from models.reposicionamento import Reposicionamento
from services.processamento import Processamento
from services.receptor import ErroReceptor, Receptor, SimuladorESP32
from services.visualizacao import Visualizacao
from utils.config import Configuracoes


@dataclass
class EstadoMonitoramento:
    """Snapshot enviado à view a cada atualização."""
    rodando: bool
    conectado: bool
    pressao_maxima: float = 0.0
    pressao_media: float = 0.0
    pressao_minima: float = 0.0
    tempo_desde_reposicionamento: float = 0.0   # segundos
    tempo_estabilidade: float = 0.0             # segundos
    risco: str = "verde"                        # "verde" | "amarelo" | "vermelho"
    png_bytes: Optional[bytes] = None
    erro: Optional[str] = None


CallbackAtualizacao = Callable[[EstadoMonitoramento], None]


class MonitoramentoController:

    def __init__(self, paciente_id: int, config: Configuracoes):
        self.paciente_id = paciente_id
        self.config = config

        self.processamento = Processamento()
        self.visualizacao = Visualizacao(
            paleta=config.paleta_mapa, interpolacao="bicubic"
        )

        self._receptor = self._criar_receptor()

        self._thread: Optional[threading.Thread] = None
        self._rodando = threading.Event()
        self._callback: Optional[CallbackAtualizacao] = None

        self._inicio_reposicionamento = time.monotonic()
        self._ultima_matriz_bruta: Optional[List[List[float]]] = None
        self._ultimas_estatisticas = (0.0, 0.0, 0.0)

    # ---------- Configuração interna ----------

    def _criar_receptor(self):
        if self.config.modo_simulacao:
            return SimuladorESP32(
                linhas=self.config.sensor_linhas,
                colunas=self.config.sensor_colunas,
                intervalo=self.config.frequencia_atualizacao,
            )
        return Receptor(self.config.esp32_ip, self.config.esp32_porta)

    def registrar_callback(self, callback: CallbackAtualizacao) -> None:
        """A view chama isto para receber cada novo EstadoMonitoramento."""
        self._callback = callback

    # ---------- Ciclo de vida ----------

    def iniciar(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._rodando.set()
        self._thread = threading.Thread(target=self._loop_aquisicao, daemon=True)
        self._thread.start()

    def parar(self) -> None:
        self._rodando.clear()
        if self._thread is not None:
            self._thread.join(timeout=2)
        try:
            self._receptor.desconectar()
        except Exception:
            pass

    def finalizar(self) -> None:
        """Chamado ao sair da tela de monitoramento: libera recursos do Matplotlib."""
        self.parar()
        self.visualizacao.fechar()

    # ---------- Loop principal (roda em thread separada) ----------

    def _loop_aquisicao(self) -> None:
        try:
            self._receptor.conectar()
        except ErroReceptor as exc:
            self._notificar(erro=str(exc), conectado=False)

        while self._rodando.is_set():
            try:
                if not self._receptor.conectado:
                    self._receptor.reconectar()

                matriz = self._receptor.receber_matriz()
                self._processar_leitura(matriz)

            except ErroReceptor as exc:
                self._notificar(erro=str(exc), conectado=False)
                time.sleep(1.0)
            except Exception as exc:  # nunca deixar a thread morrer silenciosamente
                self._notificar(erro=f"Erro inesperado: {exc}", conectado=False)
                time.sleep(1.0)

    def _processar_leitura(self, matriz_bruta) -> None:
        stats = self.processamento.calcular_estatisticas(matriz_bruta)
        tempo_estabilidade = self.processamento.atualizar_estabilidade(matriz_bruta)
        interpolada = self.processamento.interpolar_matriz(
            matriz_bruta, fator=8
        )
        self.visualizacao.atualizar(interpolada, vmax=None)

        self._ultima_matriz_bruta = matriz_bruta
        self._ultimas_estatisticas = (stats.maxima, stats.media, stats.minima)

        self._salvar_leitura(stats)

        tempo_reposicionamento = time.monotonic() - self._inicio_reposicionamento
        risco = self._calcular_risco(tempo_reposicionamento, tempo_estabilidade)

        self._notificar(
            conectado=True,
            pressao_maxima=stats.maxima,
            pressao_media=stats.media,
            pressao_minima=stats.minima,
            tempo_desde_reposicionamento=tempo_reposicionamento,
            tempo_estabilidade=tempo_estabilidade,
            risco=risco,
            png_bytes=self.visualizacao.obter_png_bytes(),
        )

    # ---------- Regras de negócio ----------

    def _calcular_risco(self, tempo_reposicionamento: float, tempo_estabilidade: float) -> str:
        """
        Cálculo inicial baseado apenas em tempo.
        Os limiares são configuráveis pelo usuário em Configurações.
        Preparado para, no futuro, ser substituído/combinado com saída de IA.
        """
        maximo = self.config.tempo_maximo_permitido * 60
        alerta = self.config.tempo_estabilidade * 60

        if tempo_reposicionamento >= maximo:
            return "vermelho"
        if tempo_reposicionamento >= alerta:
            return "amarelo"
        return "verde"

    def confirmar_reposicionamento(self, observacao: str = "") -> Reposicionamento:
        agora = datetime.now()
        tempo_sentado = int(time.monotonic() - self._inicio_reposicionamento)
        maxima, media, minima = self._ultimas_estatisticas

        rep = Reposicionamento(
            paciente_id=self.paciente_id,
            data=agora.strftime("%Y-%m-%d"),
            hora=agora.strftime("%H:%M:%S"),
            tempo_sentado=tempo_sentado,
            pressao_maxima=maxima,
            pressao_media=media,
            pressao_minima=minima,
            observacao=observacao or None,
        )

        with database.conexao() as conn:
            cur = conn.execute(
                """INSERT INTO reposicionamentos
                   (paciente_id, data, hora, tempo_sentado, pressao_maxima,
                    pressao_media, pressao_minima, observacao)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    rep.paciente_id, rep.data, rep.hora, rep.tempo_sentado,
                    rep.pressao_maxima, rep.pressao_media, rep.pressao_minima,
                    rep.observacao,
                ),
            )
            conn.commit()
            rep.id = cur.lastrowid

        # Reinicia os contadores para o novo ciclo de posicionamento.
        self._inicio_reposicionamento = time.monotonic()
        self.processamento.reiniciar_estabilidade()
        return rep

    # ---------- Persistência de leituras ----------

    def _salvar_leitura(self, stats) -> None:
        with database.conexao() as conn:
            conn.execute(
                """INSERT INTO leituras
                   (paciente_id, pressao_maxima, pressao_media, pressao_minima)
                   VALUES (?,?,?,?)""",
                (self.paciente_id, stats.maxima, stats.media, stats.minima),
            )
            conn.commit()

    # ---------- Exportação manual (botões da tela) ----------

    def salvar_imagem(self, caminho: str) -> None:
        self.visualizacao.salvar_imagem(caminho)

    def salvar_csv(self, caminho: str) -> None:
        import pandas as pd

        with database.conexao() as conn:
            rows = conn.execute(
                """SELECT data_hora, pressao_maxima, pressao_media, pressao_minima
                   FROM leituras WHERE paciente_id = ? ORDER BY data_hora""",
                (self.paciente_id,),
            ).fetchall()

        df = pd.DataFrame(
            [dict(r) for r in rows],
            columns=["data_hora", "pressao_maxima", "pressao_media", "pressao_minima"],
        )
        df.to_csv(caminho, index=False, encoding="utf-8")

    # ---------- Aparência (ajustes em tempo real, vindos da tela) ----------

    def definir_paleta(self, paleta: str) -> None:
        self.visualizacao.definir_paleta(paleta)

    def definir_interpolacao(self, interpolacao: str) -> None:
        self.visualizacao.definir_interpolacao(interpolacao)

    def definir_zoom(self, fator: float) -> None:
        self.visualizacao.definir_zoom(fator)

    # ---------- Notificação da view ----------

    def _notificar(self, **kwargs) -> None:
        if self._callback is None:
            return
        rodando = self._rodando.is_set()
        estado = EstadoMonitoramento(rodando=rodando, conectado=False)
        for k, v in kwargs.items():
            setattr(estado, k, v)
        try:
            self._callback(estado)
        except Exception:
            # Um erro na view nunca deve derrubar a thread de aquisição.
            pass
