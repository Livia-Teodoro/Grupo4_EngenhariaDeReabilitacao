"""
views/historico_view.py

Tela de Histórico: tabela de reposicionamentos com pesquisa,
filtro por data e exportação em CSV/PDF.
"""

from __future__ import annotations

import flet as ft

from controllers.historico_controller import HistoricoController
from models.paciente import Paciente


def build_historico_view(page: ft.Page, paciente: Paciente) -> ft.Container:

    controller = HistoricoController()

    campo_busca = ft.TextField(hint_text="Pesquisar observação...", width=260,
                                prefix_icon=ft.Icons.SEARCH, filled=True, bgcolor="#ffffff")
    campo_data_inicio = ft.TextField(hint_text="Data início (AAAA-MM-DD)", width=200, filled=True, bgcolor="#ffffff")
    campo_data_fim = ft.TextField(hint_text="Data fim (AAAA-MM-DD)", width=200, filled=True, bgcolor="#ffffff")

    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Data")),
            ft.DataColumn(ft.Text("Hora")),
            ft.DataColumn(ft.Text("Tempo sentado")),
            ft.DataColumn(ft.Text("Pressão máx.")),
            ft.DataColumn(ft.Text("Pressão média")),
            ft.DataColumn(ft.Text("Observação")),
        ],
        rows=[],
    )

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def _filtros() -> dict:
        f = {}
        if campo_busca.value:
            f["termo_busca"] = campo_busca.value.strip()
        if campo_data_inicio.value:
            f["data_inicio"] = campo_data_inicio.value.strip()
        if campo_data_fim.value:
            f["data_fim"] = campo_data_fim.value.strip()
        return f

    def _recarregar(e=None):
        registros = controller.listar(paciente.id, **_filtros())
        tabela.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(r.data)),
                ft.DataCell(ft.Text(r.hora)),
                ft.DataCell(ft.Text(r.tempo_sentado_formatado)),
                ft.DataCell(ft.Text(f"{r.pressao_maxima:.1f}" if r.pressao_maxima is not None else "-")),
                ft.DataCell(ft.Text(f"{r.pressao_media:.1f}" if r.pressao_media is not None else "-")),
                ft.DataCell(ft.Text(r.observacao or "-")),
            ])
            for r in registros
        ]
        if page:
            page.update()

    def _ao_resultado_arquivo(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        if e.path.lower().endswith(".pdf"):
            controller.exportar_pdf(paciente.id, e.path, nome_paciente=paciente.nome, **_filtros())
        else:
            controller.exportar_csv(paciente.id, e.path, **_filtros())
        page.update()

    file_picker.on_result = _ao_resultado_arquivo

    campo_busca.on_change = _recarregar
    campo_data_inicio.on_change = _recarregar
    campo_data_fim.on_change = _recarregar

    _recarregar()

    return ft.Container(
        expand=True, padding=24, bgcolor="#f5f7fa",
        content=ft.Column(spacing=16, expand=True, controls=[
            ft.Text(f"Histórico de Reposicionamentos - {paciente.nome}", size=22, weight=ft.FontWeight.BOLD),
            ft.Row(spacing=12, controls=[campo_busca, campo_data_inicio, campo_data_fim]),
            ft.Row(spacing=10, controls=[
                ft.ElevatedButton(
                    "Exportar CSV", icon=ft.Icons.DOWNLOAD,
                    on_click=lambda e: file_picker.save_file(file_name="historico.csv", allowed_extensions=["csv"]),
                ),
                ft.ElevatedButton(
                    "Exportar PDF", icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                    on_click=lambda e: file_picker.save_file(file_name="historico.pdf", allowed_extensions=["pdf"]),
                ),
            ]),
            ft.Container(
                expand=True, bgcolor="#ffffff", border_radius=14, padding=16,
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, controls=[tabela]),
            ),
        ]),
    )
