"""
services/receptor.py

Camada de comunicação.

Protocolo assumido com a ESP32 (ajustável no firmware):
    - Conexão TCP simples no IP/porta configurados.
    - A ESP32 envia, repetidamente, uma linha de texto terminada em
      '\\n' contendo um JSON no formato:
          {"matrix": [[v11, v12, ...], [v21, v22, ...], ...]}
      onde cada v_ij é a leitura crua do sensor (ex.: 0-4095 de um ADC).

Esta classe:
    - Conecta.
    - Recebe a matriz (bloqueante, roda em thread própria via Controller).
    - Detecta desconexão.
    - Reconecta automaticamente (com backoff simples).

Também é fornecido `SimuladorESP32`, com a MESMA interface pública,
para permitir desenvolver/testar o sistema completo sem hardware.
O Controller decide qual usar a partir de `config.modo_simulacao`.
"""

from __future__ import annotations

import json
import math
import random
import socket
import time
from typing import List, Optional

Matriz = List[List[float]]


class ErroReceptor(Exception):
    """
    Erro de comunicação com a ESP32 (conexão recusada, timeout, etc.).
    """


class Receptor:
    """
    Cliente TCP responsável apenas por obter a matriz de pressão da ESP32.

    """

    def __init__(self, ip: str, porta: int, timeout: float = 5.0):
        self.ip = ip
        self.porta = porta
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None
        self._buffer = b""
        self.conectado = False

    def conectar(self) -> None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect((self.ip, self.porta))
            self._socket = s
            self._buffer = b""
            self.conectado = True
        except OSError as exc:
            self.conectado = False
            raise ErroReceptor(f"Falha ao conectar em {self.ip}:{self.porta}: {exc}")

    def desconectar(self) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
        self._socket = None
        self.conectado = False

    def reconectar(self, tentativas: int = 5, espera_inicial: float = 1.0) -> None:
        """Tenta reconectar com backoff exponencial simples."""
        self.desconectar()
        espera = espera_inicial
        ultimo_erro: Optional[Exception] = None
        for _ in range(tentativas):
            try:
                self.conectar()
                return
            except ErroReceptor as exc:
                ultimo_erro = exc
                time.sleep(espera)
                espera = min(espera * 2, 15.0)
        raise ErroReceptor(f"Não foi possível reconectar: {ultimo_erro}")

    def receber_matriz(self) -> Matriz:
        """
        Lê uma linha JSON completa do socket e retorna a matriz de pressão.
        Bloqueia até receber uma linha ou levanta ErroReceptor em caso de
        desconexão/timeout/JSON inválido.
        """
        if self._socket is None:
            raise ErroReceptor("Receptor não está conectado.")

        try:
            while b"\n" not in self._buffer:
                pedaco = self._socket.recv(4096)
                if not pedaco:
                    self.conectado = False
                    raise ErroReceptor("Conexão encerrada pela ESP32.")
                self._buffer += pedaco

            linha, self._buffer = self._buffer.split(b"\n", 1)
            dados = json.loads(linha.decode("utf-8").strip())
            matriz = dados["matrix"]
            return matriz
        except socket.timeout as exc:
            raise ErroReceptor(f"Timeout aguardando dados da ESP32: {exc}")
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            self.conectado = False
            raise ErroReceptor(f"Erro na leitura/parse da matriz: {exc}")


class SimuladorESP32:
    """
    Substituto do Receptor para desenvolvimento/demonstração sem hardware.
    Gera uma matriz sintética simulando pontos de contato corporal
    (glúteos/ísquios, sacro, calcanhares) com leve variação ao longo do
    tempo, para que o mapa térmico e os indicadores reajam de forma realista.

    Possui a mesma interface pública usada pelo Controller
    (conectar / receber_matriz / desconectar), podendo ser trocado pelo
    Receptor real sem alterar o restante do sistema.
    """

    def __init__(self, linhas: int = 8, colunas: int = 8, intervalo: float = 1.0):
        self.linhas = linhas
        self.colunas = colunas
        self.intervalo = intervalo
        self.conectado = False
        self._t = 0.0
        # Pontos de pressão simulados (linha, coluna, intensidade_base, raio)
        self._pontos_base = [
            (linhas * 0.30, colunas * 0.30, 220, 1.4),   # ísquio esquerdo
            (linhas * 0.30, colunas * 0.70, 220, 1.4),   # ísquio direito
            (linhas * 0.65, colunas * 0.50, 160, 1.6),   # sacro
        ]

    def conectar(self) -> None:
        time.sleep(0.2)  # simula latência de handshake
        self.conectado = True

    def desconectar(self) -> None:
        self.conectado = False

    def reconectar(self, tentativas: int = 5, espera_inicial: float = 1.0) -> None:
        self.conectar()

    def receber_matriz(self) -> Matriz:
        if not self.conectado:
            raise ErroReceptor("Simulador não está conectado.")

        time.sleep(self.intervalo)
        self._t += self.intervalo

        matriz = [[0.0 for _ in range(self.colunas)] for _ in range(self.linhas)]
        oscilacao = 1.0 + 0.08 * math.sin(self._t / 6.0)

        for (li, ci, intensidade, raio) in self._pontos_base:
            li_atual = li + 0.15 * math.sin(self._t / 13.0)
            ci_atual = ci + 0.15 * math.cos(self._t / 17.0)
            for i in range(self.linhas):
                for j in range(self.colunas):
                    d2 = (i - li_atual) ** 2 + (j - ci_atual) ** 2
                    valor = intensidade * oscilacao * math.exp(-d2 / (2 * raio ** 2))
                    matriz[i][j] += valor

        # ruído de sensor
        for i in range(self.linhas):
            for j in range(self.colunas):
                matriz[i][j] = max(0.0, matriz[i][j] + random.uniform(-4, 4))

        return matriz
