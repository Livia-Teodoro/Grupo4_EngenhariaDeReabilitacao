"""
views/home_view.py

Tela Home: lista de pacientes, pesquisa, e ações de
novo/editar/excluir/abrir monitoramento.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from controllers.paciente_controller import PacienteController
from models.paciente import Paciente


def build_home_view(
    on_novo_paciente: Callable[[], None],
    on_editar_paciente: Callable[[Paciente], None],
    on_abrir_monitoramento: Callable[[Paciente], None],
    on_excluir_paciente: Callable[[Paciente], None],
) -> ft.Container:

    controller = PacienteController()
    selecionado: dict = {"paciente": None}

    campo_busca = ft.TextField(
        hint_text="Pesquisar paciente...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=10,
        filled=True,
        bgcolor="#ffffff",
        width=320,
    )

    lista_coluna = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    botao_editar = ft.ElevatedButton("Editar", icon=ft.Icons.EDIT_OUTLINED, disabled=True)
    botao_excluir = ft.ElevatedButton("Excluir", icon=ft.Icons.DELETE_OUTLINE, disabled=True,
                                       bgcolor="#fdecea", color="#c0392b")
    botao_abrir = ft.ElevatedButton("Abrir Monitoramento", icon=ft.Icons.MONITOR_HEART,
                                     disabled=True, bgcolor="#2d6cdf", color="#ffffff")

    def _selecionar(paciente: Paciente, card: ft.Container):
        for c in lista_coluna.controls:
            c.bgcolor = "#ffffff"
            c.border = ft.border.all(1, "#e3e7ed")
        card.bgcolor = "#eef3fb"
        card.border = ft.border.all(2, "#2d6cdf")

        selecionado["paciente"] = paciente
        botao_editar.disabled = False
        botao_excluir.disabled = False
        botao_abrir.disabled = False
        card.page.update()

    def _card_paciente(p: Paciente) -> ft.Container:
        subtitulo_partes = []
        if p.idade is not None:
            subtitulo_partes.append(f"{p.idade} anos")
        if p.mobilidade:
            subtitulo_partes.append(p.mobilidade)
        if p.condicao:
            subtitulo_partes.append(p.condicao)
        subtitulo = " · ".join(subtitulo_partes) if subtitulo_partes else "Sem dados clínicos"

        card = ft.Container(
            padding=16,
            border_radius=12,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#e3e7ed"),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.CircleAvatar(
                        content=ft.Text(p.nome[:1].upper() if p.nome else "?"),
                        bgcolor="#dbe7fb",
                        color="#2d6cdf",
                    ),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(p.nome, weight=ft.FontWeight.W_600, size=15),
                            ft.Text(subtitulo, size=12, color="#6b7280"),
                        ],
                    ),
                ],
            ),
        )
        card.on_click = lambda e, pp=p, cc=card: _selecionar(pp, cc)
        return card

    def _recarregar(termo: str = ""):
        lista_coluna.controls.clear()
        pacientes = controller.listar(termo)
        if not pacientes:
            lista_coluna.controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.alignment.center,
                    content=ft.Text("Nenhum paciente cadastrado ainda.", color="#9aa3b2"),
                )
            )
        else:
            for p in pacientes:
                lista_coluna.controls.append(_card_paciente(p))

        selecionado["paciente"] = None
        botao_editar.disabled = True
        botao_excluir.disabled = True
        botao_abrir.disabled = True

    def _ao_buscar(e: ft.ControlEvent):
        _recarregar(campo_busca.value or "")
        campo_busca.page.update()

    campo_busca.on_change = _ao_buscar

    def _confirmar_exclusao(e):
        p = selecionado["paciente"]
        if p:
            on_excluir_paciente(p)
            _recarregar()
            campo_busca.page.update()

    botao_editar.on_click = lambda e: on_editar_paciente(selecionado["paciente"])
    botao_excluir.on_click = _confirmar_exclusao
    botao_abrir.on_click = lambda e: on_abrir_monitoramento(selecionado["paciente"])

    _recarregar()

    return ft.Container(
        expand=True,
        padding=24,
        bgcolor="#f5f7fa",
        content=ft.Column(
            spacing=18,
            expand=True,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Pacientes", size=22, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Novo Paciente",
                            icon=ft.Icons.PERSON_ADD_ALT_1,
                            bgcolor="#2d6cdf",
                            color="#ffffff",
                            on_click=lambda e: on_novo_paciente(),
                        ),
                    ],
                ),
                campo_busca,
                ft.Row(spacing=10, controls=[botao_editar, botao_excluir, botao_abrir]),
                ft.Container(expand=True, content=lista_coluna),
            ],
        ),
    )
