"""
views/components/top_bar.py

Barra superior, sempre visível, conforme a especificação:
logo, nome do sistema, paciente atual, botões de editar/trocar
paciente e usuário logado (estrutura preparada para login futuro).
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from models.paciente import Paciente


def build_top_bar(
    paciente_atual: Optional[Paciente],
    on_editar_paciente: Callable[[], None],
    on_trocar_paciente: Callable[[], None],
) -> ft.Container:

    nome_paciente = paciente_atual.nome if paciente_atual else "Nenhum paciente selecionado"

    return ft.Container(
        bgcolor="#ffffff",
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
        border=ft.border.only(bottom=ft.BorderSide(1, "#e3e7ed")),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.HEALTH_AND_SAFETY, color="#2d6cdf", size=28),
                        ft.Text(
                            "Monitor de Pressão",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="#1f2733",
                        ),
                    ],
                ),
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=14, vertical=8),
                            bgcolor="#eef3fb",
                            border_radius=10,
                            content=ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.PERSON_OUTLINE, size=18, color="#2d6cdf"),
                                    ft.Text(nome_paciente, size=14, color="#1f2733"),
                                ],
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            tooltip="Editar paciente",
                            on_click=lambda e: on_editar_paciente(),
                            disabled=paciente_atual is None,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SWAP_HORIZ,
                            tooltip="Trocar paciente",
                            on_click=lambda e: on_trocar_paciente(),
                        ),
                        ft.VerticalDivider(width=1),
                        ft.CircleAvatar(
                            content=ft.Icon(ft.Icons.PERSON, color="#ffffff"),
                            bgcolor="#2d6cdf",
                            radius=16,
                        ),
                    ],
                ),
            ],
        ),
    )
