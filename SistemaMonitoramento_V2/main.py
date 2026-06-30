"""
main.py

Ponto de entrada da aplicação.

Monta a barra superior e o menu lateral (sempre visíveis) e troca
apenas o conteúdo da área central conforme o item de menu selecionado.
"""

from __future__ import annotations

import flet as ft

import database
from controllers.paciente_controller import PacienteController
from models.paciente import Paciente
from utils.config import carregar_configuracoes

from views.components.side_menu import build_side_menu
from views.components.top_bar import build_top_bar
from views.home_view import build_home_view
from views.paciente_view import build_paciente_view
from views.monitoramento_view import build_monitoramento_view
from views.historico_view import build_historico_view
from views.relatorios_view import build_relatorios_view
from views.configuracoes_view import build_configuracoes_view

ROTA_HOME, ROTA_PACIENTES, ROTA_MONITORAMENTO, ROTA_HISTORICO, ROTA_RELATORIOS, ROTA_CONFIGURACOES = range(6)


def main(page: ft.Page) -> None:
    page.title = "Monitor de Pressão - Prevenção de Lesões"
    page.padding = 0
    page.bgcolor = "#f5f7fa"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {}  # reservado para fontes customizadas, se desejado

    database.inicializar_banco()

    estado = {
        "paciente_atual": None,        # type: Paciente | None
        "config": carregar_configuracoes(),
        "indice_menu": ROTA_HOME,
        "paciente_em_edicao": None,    # type: Paciente | None
    }

    area_topo = ft.Container()
    area_conteudo = ft.Container(expand=True)

    def _navegar(indice: int) -> None:
        estado["indice_menu"] = indice
        _renderizar()

    menu_lateral = build_side_menu(selected_index=estado["indice_menu"], on_navegar=_navegar)

    # ---------- Ações compartilhadas entre telas ----------

    def _ir_para_home(e=None):
        estado["indice_menu"] = ROTA_HOME
        _renderizar()

    def _abrir_cadastro_novo():
        estado["paciente_em_edicao"] = None
        _mostrar_cadastro()

    def _abrir_cadastro_edicao(paciente: Paciente):
        estado["paciente_em_edicao"] = paciente
        _mostrar_cadastro()

    def _mostrar_cadastro():
        page.overlay.clear()
        area_conteudo.content = build_paciente_view(
            paciente=estado["paciente_em_edicao"],
            on_salvar=_ao_salvar_paciente,
            on_cancelar=_ir_para_home,
        )
        page.update()

    def _ao_salvar_paciente():
        estado["indice_menu"] = ROTA_HOME
        _renderizar()

    def _excluir_paciente(paciente: Paciente):
        PacienteController().excluir(paciente.id)
        if estado["paciente_atual"] and estado["paciente_atual"].id == paciente.id:
            estado["paciente_atual"] = None

    def _abrir_monitoramento(paciente: Paciente):
        estado["paciente_atual"] = paciente
        estado["indice_menu"] = ROTA_MONITORAMENTO
        _renderizar()

    def _trocar_paciente(e=None):
        estado["indice_menu"] = ROTA_HOME
        _renderizar()

    def _editar_paciente_atual(e=None):
        if estado["paciente_atual"]:
            _abrir_cadastro_edicao(estado["paciente_atual"])

    def _sair_do_monitoramento():
        estado["indice_menu"] = ROTA_HOME
        _renderizar()

    def _ao_salvar_configuracoes(nova_config):
        estado["config"] = nova_config

    # ---------- Roteamento central ----------

    def _renderizar() -> None:
        page.overlay.clear()
        menu_lateral.selected_index = estado["indice_menu"]

        area_topo.content = build_top_bar(
            paciente_atual=estado["paciente_atual"],
            on_editar_paciente=_editar_paciente_atual,
            on_trocar_paciente=_trocar_paciente,
        )

        indice = estado["indice_menu"]

        if indice == ROTA_HOME or indice == ROTA_PACIENTES:
            area_conteudo.content = build_home_view(
                on_novo_paciente=_abrir_cadastro_novo,
                on_editar_paciente=_abrir_cadastro_edicao,
                on_abrir_monitoramento=_abrir_monitoramento,
                on_excluir_paciente=_excluir_paciente,
            )

        elif indice == ROTA_MONITORAMENTO:
            if estado["paciente_atual"] is None:
                area_conteudo.content = _aviso_sem_paciente()
            else:
                area_conteudo.content = build_monitoramento_view(
                    page=page,
                    paciente=estado["paciente_atual"],
                    config=estado["config"],
                    on_sair=_sair_do_monitoramento,
                )

        elif indice == ROTA_HISTORICO:
            if estado["paciente_atual"] is None:
                area_conteudo.content = _aviso_sem_paciente()
            else:
                area_conteudo.content = build_historico_view(page=page, paciente=estado["paciente_atual"])

        elif indice == ROTA_RELATORIOS:
            if estado["paciente_atual"] is None:
                area_conteudo.content = _aviso_sem_paciente()
            else:
                area_conteudo.content = build_relatorios_view(page=page, paciente=estado["paciente_atual"])

        elif indice == ROTA_CONFIGURACOES:
            area_conteudo.content = build_configuracoes_view(
                config=estado["config"], on_salvar=_ao_salvar_configuracoes,
            )

        page.update()

    def _aviso_sem_paciente() -> ft.Container:
        return ft.Container(
            expand=True, alignment=ft.alignment.center,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12,
                controls=[
                    ft.Icon(ft.Icons.PERSON_SEARCH, size=48, color="#9aa3b2"),
                    ft.Text("Selecione um paciente na Home para continuar.", color="#6b7280"),
                    ft.ElevatedButton("Ir para Pacientes", on_click=_ir_para_home),
                ],
            ),
        )

    # ---------- Layout raiz ----------

    page.add(
        ft.Column(
            expand=True, spacing=0,
            controls=[
                area_topo,
                ft.Row(
                    expand=True, spacing=0,
                    controls=[menu_lateral, ft.VerticalDivider(width=1), area_conteudo],
                ),
            ],
        )
    )

    _renderizar()


if __name__ == "__main__":
    ft.app(target=main)
