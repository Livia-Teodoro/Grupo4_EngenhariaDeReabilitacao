"""
views/components/side_menu.py

Menu lateral fixo (NavigationRail). A troca de telas nunca abre
janelas novas: apenas dispara `on_navegar(indice)`, que o main.py
usa para substituir o conteúdo da área central.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

ITENS_MENU = [
    (ft.Icons.HOME_OUTLINED, ft.Icons.HOME, "Home"),
    (ft.Icons.PEOPLE_OUTLINE, ft.Icons.PEOPLE, "Pacientes"),
    (ft.Icons.MONITOR_HEART_OUTLINED, ft.Icons.MONITOR_HEART, "Monitoramento"),
    (ft.Icons.HISTORY, ft.Icons.HISTORY, "Histórico"),
    (ft.Icons.DESCRIPTION_OUTLINED, ft.Icons.DESCRIPTION, "Relatórios"),
    (ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS, "Configurações"),
]


def build_side_menu(
    selected_index: int,
    on_navegar: Callable[[int], None],
) -> ft.NavigationRail:
    destinos = [
        ft.NavigationRailDestination(icon=icone, selected_icon=icone_sel, label=label)
        for (icone, icone_sel, label) in ITENS_MENU
    ]

    def _ao_mudar(e: ft.ControlEvent) -> None:
        on_navegar(e.control.selected_index)

    return ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=88,
        min_extended_width=180,
        bgcolor="#f5f7fa",
        destinations=destinos,
        on_change=_ao_mudar,
    )
