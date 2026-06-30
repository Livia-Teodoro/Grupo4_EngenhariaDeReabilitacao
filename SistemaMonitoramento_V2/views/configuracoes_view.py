"""
views/configuracoes_view.py

Tela de Configurações: IP/porta da ESP32, limites de tempo,
tema, paleta do mapa e frequência de atualização.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from services.visualizacao import PALETAS_DISPONIVEIS
from utils.config import Configuracoes, salvar_configuracoes


def build_configuracoes_view(config: Configuracoes, on_salvar: Callable[[Configuracoes], None]) -> ft.Container:

    campo_ip = ft.TextField(label="IP da ESP32", value=config.esp32_ip, width=220)
    campo_porta = ft.TextField(label="Porta", value=str(config.esp32_porta), width=120)
    switch_simulacao = ft.Switch(label="Usar simulador (sem hardware)", value=config.modo_simulacao)

    campo_tempo_maximo = ft.TextField(
        label="Tempo máximo permitido (min)", value=str(config.tempo_maximo_permitido), width=220,
    )
    campo_tempo_estabilidade = ft.TextField(
        label="Tempo de estabilidade (min)", value=str(config.tempo_estabilidade), width=220,
    )

    dropdown_tema = ft.Dropdown(
        label="Tema", value=config.tema, width=160,
        options=[ft.dropdown.Option("claro"), ft.dropdown.Option("escuro")],
    )
    dropdown_paleta = ft.Dropdown(
        label="Paleta do mapa", value=config.paleta_mapa, width=180,
        options=[ft.dropdown.Option(p) for p in PALETAS_DISPONIVEIS],
    )
    campo_frequencia = ft.TextField(
        label="Frequência de atualização (s)", value=str(config.frequencia_atualizacao), width=220,
    )

    texto_status = ft.Text("", color="#1e8e3e", size=13)

    def _salvar(e):
        try:
            nova = Configuracoes(
                esp32_ip=campo_ip.value.strip(),
                esp32_porta=int(campo_porta.value),
                tempo_maximo_permitido=int(campo_tempo_maximo.value),
                tempo_estabilidade=int(campo_tempo_estabilidade.value),
                tema=dropdown_tema.value,
                paleta_mapa=dropdown_paleta.value,
                frequencia_atualizacao=float(campo_frequencia.value),
                sensor_linhas=config.sensor_linhas,
                sensor_colunas=config.sensor_colunas,
                modo_simulacao=switch_simulacao.value,
            )
        except ValueError:
            texto_status.value = "Verifique se os campos numéricos estão corretos."
            texto_status.color = "#c0392b"
            e.page.update()
            return

        salvar_configuracoes(nova)
        texto_status.value = "Configurações salvas com sucesso."
        texto_status.color = "#1e8e3e"
        on_salvar(nova)
        e.page.update()

    return ft.Container(
        expand=True, padding=24, bgcolor="#f5f7fa",
        content=ft.Column(spacing=18, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Text("Configurações", size=22, weight=ft.FontWeight.BOLD),

            ft.Container(
                padding=20, bgcolor="#ffffff", border_radius=14,
                content=ft.Column(spacing=12, controls=[
                    ft.Text("Comunicação com a ESP32", weight=ft.FontWeight.W_600),
                    ft.Row(spacing=14, controls=[campo_ip, campo_porta, switch_simulacao]),
                ]),
            ),

            ft.Container(
                padding=20, bgcolor="#ffffff", border_radius=14,
                content=ft.Column(spacing=12, controls=[
                    ft.Text("Regras de risco", weight=ft.FontWeight.W_600),
                    ft.Row(spacing=14, controls=[campo_tempo_maximo, campo_tempo_estabilidade]),
                ]),
            ),

            ft.Container(
                padding=20, bgcolor="#ffffff", border_radius=14,
                content=ft.Column(spacing=12, controls=[
                    ft.Text("Aparência e aquisição", weight=ft.FontWeight.W_600),
                    ft.Row(spacing=14, controls=[dropdown_tema, dropdown_paleta, campo_frequencia]),
                ]),
            ),

            ft.Row(spacing=12, controls=[
                ft.ElevatedButton("Salvar Configurações", icon=ft.Icons.SAVE_OUTLINED,
                                  bgcolor="#2d6cdf", color="#ffffff", on_click=_salvar),
                texto_status,
            ]),
        ]),
    )
