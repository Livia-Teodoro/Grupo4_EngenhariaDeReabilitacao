"""
views/relatorios_view.py

Tela de Relatórios: gera resumos diário/semanal/mensal com
número de reposicionamentos, tempo médio sentado, maior pressão
registrada e gráfico temporal, com exportação em PDF.
"""

from __future__ import annotations

import base64

import flet as ft

from controllers.relatorio_controller import RelatorioController
from models.paciente import Paciente


def build_relatorios_view(page: ft.Page, paciente: Paciente) -> ft.Container:

    controller = RelatorioController()
    estado = {"resumo": None}

    texto_numero = ft.Text("-", size=24, weight=ft.FontWeight.BOLD, color="#2d6cdf")
    texto_tempo_medio = ft.Text("-", size=24, weight=ft.FontWeight.BOLD, color="#1e8e3e")
    texto_maior_pressao = ft.Text("-", size=24, weight=ft.FontWeight.BOLD, color="#c0392b")
    texto_periodo = ft.Text("Selecione um período para gerar o relatório.", color="#6b7280")

    imagem_grafico = ft.Image(fit=ft.ImageFit.CONTAIN, visible=False, height=260)

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def _atualizar_cards(resumo):
        estado["resumo"] = resumo
        texto_periodo.value = f"Período: {resumo.periodo_inicio} a {resumo.periodo_fim}"
        texto_numero.value = str(resumo.numero_reposicionamentos)
        texto_tempo_medio.value = f"{resumo.tempo_medio_sentado_seg / 60:.0f} min"
        texto_maior_pressao.value = f"{resumo.maior_pressao:.0f}"

        if resumo.grafico_png:
            imagem_grafico.src_base64 = base64.b64encode(resumo.grafico_png).decode("utf-8")
            imagem_grafico.visible = True
        else:
            imagem_grafico.visible = False

        page.update()

    def _gerar_diario(e):
        _atualizar_cards(controller.resumo_diario(paciente.id))

    def _gerar_semanal(e):
        _atualizar_cards(controller.resumo_semanal(paciente.id))

    def _gerar_mensal(e):
        _atualizar_cards(controller.resumo_mensal(paciente.id))

    def _ao_resultado_arquivo(e: ft.FilePickerResultEvent):
        if not e.path or estado["resumo"] is None:
            return
        controller.exportar_pdf(estado["resumo"], paciente.nome, e.path)
        page.update()

    file_picker.on_result = _ao_resultado_arquivo

    def _exportar_pdf(e):
        if estado["resumo"] is None:
            return
        file_picker.save_file(file_name="relatorio.pdf", allowed_extensions=["pdf"])

    return ft.Container(
        expand=True, padding=24, bgcolor="#f5f7fa",
        content=ft.Column(spacing=18, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Text(f"Relatórios - {paciente.nome}", size=22, weight=ft.FontWeight.BOLD),
            ft.Row(spacing=10, controls=[
                ft.ElevatedButton("Resumo Diário", icon=ft.Icons.TODAY, on_click=_gerar_diario),
                ft.ElevatedButton("Resumo Semanal", icon=ft.Icons.DATE_RANGE, on_click=_gerar_semanal),
                ft.ElevatedButton("Resumo Mensal", icon=ft.Icons.CALENDAR_MONTH, on_click=_gerar_mensal),
                ft.OutlinedButton("Exportar PDF", icon=ft.Icons.PICTURE_AS_PDF_OUTLINED, on_click=_exportar_pdf),
            ]),
            texto_periodo,
            ft.Row(spacing=16, controls=[
                ft.Container(
                    expand=True, padding=20, bgcolor="#ffffff", border_radius=14,
                    content=ft.Column(spacing=4, controls=[
                        ft.Text("Reposicionamentos", size=12, color="#6b7280"), texto_numero,
                    ]),
                ),
                ft.Container(
                    expand=True, padding=20, bgcolor="#ffffff", border_radius=14,
                    content=ft.Column(spacing=4, controls=[
                        ft.Text("Tempo médio sentado", size=12, color="#6b7280"), texto_tempo_medio,
                    ]),
                ),
                ft.Container(
                    expand=True, padding=20, bgcolor="#ffffff", border_radius=14,
                    content=ft.Column(spacing=4, controls=[
                        ft.Text("Maior pressão registrada", size=12, color="#6b7280"), texto_maior_pressao,
                    ]),
                ),
            ]),
            ft.Container(
                padding=16, bgcolor="#ffffff", border_radius=14,
                content=ft.Column(controls=[
                    ft.Text("Gráfico temporal de pressão", weight=ft.FontWeight.W_600),
                    imagem_grafico,
                ]),
            ),
        ]),
    )
