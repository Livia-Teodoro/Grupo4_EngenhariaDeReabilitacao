"""
views/lembretes_panel.py

Painel de lembretes exibido abaixo do histórico na aba de monitoramento.
Inclui:
  - Lista dos lembretes cadastrados para o paciente
  - Formulário inline para adicionar novo lembrete
  - Pop-up de alerta quando um lembrete dispara
  - Botão de confirmação que registra no log e nos eventos
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Callable, Optional

import flet as ft

from controllers.lembrete_controller import LembreteController
from models.lembrete import (
    CATEGORIAS_LEMBRETE,
    CORES_CATEGORIA,
    ICONES_CATEGORIA,
    Lembrete,
)
from models.paciente import Paciente


# ------------------------------------------------------------------ #
#  Utilitários                                                         #
# ------------------------------------------------------------------ #

def _icone_categoria(cat: str) -> str:
    mapa = {
        "Medicação":      ft.Icons.MEDICATION,
        "Alimentação":    ft.Icons.RESTAURANT,
        "Banho":          ft.Icons.WATER_DROP,
        "Consulta médica":ft.Icons.LOCAL_HOSPITAL,
        "Fisioterapia":   ft.Icons.ACCESSIBILITY_NEW,
        "Reposicionamento": ft.Icons.AIRLINE_SEAT_FLAT,
        "Hidratação":     ft.Icons.LOCAL_DRINK,
        "Outro":          ft.Icons.NOTIFICATIONS,
    }
    return mapa.get(cat, ft.Icons.NOTIFICATIONS)


# ------------------------------------------------------------------ #
#  Painel principal                                                    #
# ------------------------------------------------------------------ #

def build_lembretes_panel(
    page: ft.Page,
    paciente: Paciente,
    on_log: Callable[[str], None],  # callback para _adicionar_evento na monitoramento_view
) -> ft.Container:
    """
    Retorna um Container que pode ser encaixado abaixo do histórico
    no painel direito da monitoramento_view.
    """

    ctrl = LembreteController()

    # ---- estado local ----
    lista_controles = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
    _popup_aberto: dict = {"ativo": False}  # flag simples sem threading

    # ================================================================
    #  Pop-up de alerta
    # ================================================================
    def _mostrar_popup(lembrete: Lembrete) -> None:
        if _popup_aberto["ativo"]:
            return
        _popup_aberto["ativo"] = True

        cor = CORES_CATEGORIA.get(lembrete.categoria, "#6b7280")

        campo_obs = ft.TextField(
            hint_text="Observação (opcional)",
            multiline=True,
            min_lines=2,
            max_lines=3,
            filled=True,
            bgcolor="#f5f7fa",
        )

        def _confirmar(e):
            ctrl.registrar_confirmacao(
                lembrete_id=lembrete.id,
                paciente_id=paciente.id,
                observacao=campo_obs.value or "",
            )
            agora = datetime.now().strftime("%H:%M:%S")
            on_log(f"{agora} - ✅ {lembrete.categoria}: {lembrete.descricao} — realizado")
            dlg.open = False
            _popup_aberto["ativo"] = False
            page.update()

        def _adiar(e):
            dlg.open = False
            _popup_aberto["ativo"] = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(spacing=10, controls=[
                ft.Icon(name=_icone_categoria(lembrete.categoria), color=cor, size=28),
                ft.Text(f"Lembrete: {lembrete.categoria}", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column(spacing=12, tight=True, controls=[
                ft.Container(
                    padding=14,
                    border_radius=10,
                    bgcolor=f"{cor}18",
                    border=ft.border.all(1, f"{cor}44"),
                    content=ft.Column(spacing=6, controls=[
                        ft.Text(lembrete.descricao, size=14, weight=ft.FontWeight.W_600),
                        ft.Text(f"Horário programado: {lembrete.hora}", size=12, color="#6b7280"),
                    ]),
                ),
                ft.Text("Confirme quando o cuidado for realizado:", size=12, color="#6b7280"),
                campo_obs,
            ]),
            actions=[
                ft.TextButton("Adiar", on_click=_adiar),
                ft.ElevatedButton(
                    "✓ Confirmar realizado",
                    bgcolor=cor,
                    color="#ffffff",
                    on_click=_confirmar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ================================================================
    #  Renderizar lista de lembretes
    # ================================================================
    def _recarregar(e=None):
        lembretes = ctrl.listar(paciente.id, apenas_ativos=True)
        lista_controles.controls.clear()

        if not lembretes:
            lista_controles.controls.append(
                ft.Text("Nenhum lembrete cadastrado.", size=12, color="#9aa3b2")
            )
        else:
            for lem in lembretes:
                cor = CORES_CATEGORIA.get(lem.categoria, "#6b7280")

                def _del_fn(e, lid=lem.id):
                    ctrl.excluir(lid)
                    _recarregar()

                card = ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=10,
                    bgcolor="#ffffff",
                    border=ft.border.all(1, "#e3e7ed"),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Container(
                                width=4, height=40, border_radius=4, bgcolor=cor
                            ),
                            ft.Icon(name=_icone_categoria(lem.categoria), color=cor, size=18),
                            ft.Column(spacing=1, expand=True, controls=[
                                ft.Text(lem.categoria, size=12, weight=ft.FontWeight.W_600, color=cor),
                                ft.Text(lem.descricao, size=11, color="#374151"),
                            ]),
                            ft.Text(lem.hora, size=13, weight=ft.FontWeight.W_600, color="#374151"),
                            ft.Text(lem.repetir, size=10, color="#9aa3b2"),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color="#c0392b",
                                icon_size=16,
                                tooltip="Excluir",
                                on_click=_del_fn,
                            ),
                        ],
                    ),
                )
                lista_controles.controls.append(card)

        if page:
            page.update()

    # ================================================================
    #  Formulário de adição
    # ================================================================
    dd_categoria = ft.Dropdown(
        label="Categoria",
        value=CATEGORIAS_LEMBRETE[0],
        options=[ft.dropdown.Option(c) for c in CATEGORIAS_LEMBRETE],
        dense=True,
        filled=True,
        bgcolor="#ffffff",
        expand=True,
    )
    tf_descricao = ft.TextField(
        label="Descrição",
        hint_text="Ex.: Dipirona 500mg",
        filled=True,
        bgcolor="#ffffff",
        expand=True,
    )
    tf_hora = ft.TextField(
        label="Hora (HH:MM)",
        hint_text="08:00",
        width=100,
        filled=True,
        bgcolor="#ffffff",
    )
    dd_repetir = ft.Dropdown(
        label="Repetir",
        value="Diário",
        options=[ft.dropdown.Option(r) for r in ["Nunca", "Diário", "Semanal"]],
        width=110,
        dense=True,
        filled=True,
        bgcolor="#ffffff",
    )
    texto_erro = ft.Text("", color="#c0392b", size=11, visible=False)

    def _adicionar(e):
        hora = tf_hora.value.strip()
        descricao = tf_descricao.value.strip()

        # Validação mínima
        if not descricao:
            texto_erro.value = "Preencha a descrição."
            texto_erro.visible = True
            page.update()
            return
        try:
            h, m = hora.split(":")
            assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
        except Exception:
            texto_erro.value = "Hora inválida. Use HH:MM (ex.: 08:30)."
            texto_erro.visible = True
            page.update()
            return

        texto_erro.visible = False
        lem = Lembrete(
            paciente_id=paciente.id,
            categoria=dd_categoria.value,
            descricao=descricao,
            hora=hora,
            repetir=dd_repetir.value,
        )
        ctrl.criar(lem)
        tf_descricao.value = ""
        tf_hora.value = ""
        on_log(
            f"{datetime.now().strftime('%H:%M:%S')} - 🔔 Lembrete criado: "
            f"{lem.categoria} às {lem.hora}"
        )
        _recarregar()

    # ================================================================
    #  Thread de verificação em background
    # ================================================================
    _parar_thread = threading.Event()

    def _verificar_loop():
        while not _parar_thread.is_set():
            try:
                pendentes = ctrl.verificar_lembretes_agora(paciente.id)
                for lem in pendentes:
                    if not _popup_aberto["ativo"]:
                        _mostrar_popup(lem)
                        break  # mostra um pop-up por vez
            except Exception:
                pass
            time.sleep(30)

    thread_verificacao = threading.Thread(target=_verificar_loop, daemon=True)
    thread_verificacao.start()

    # ================================================================
    #  Montagem
    # ================================================================
    _recarregar()

    formulario = ft.Container(
        padding=12,
        border_radius=10,
        bgcolor="#f5f7fa",
        border=ft.border.all(1, "#e3e7ed"),
        content=ft.Column(spacing=8, controls=[
            ft.Text("Novo lembrete", size=12, weight=ft.FontWeight.W_600, color="#374151"),
            ft.Row(spacing=8, controls=[dd_categoria, tf_descricao]),
            ft.Row(spacing=8, controls=[
                tf_hora,
                dd_repetir,
                ft.ElevatedButton(
                    "Adicionar",
                    icon=ft.Icons.ADD_ALARM,
                    bgcolor="#2d6cdf",
                    color="#ffffff",
                    on_click=_adicionar,
                ),
            ]),
            texto_erro,
        ]),
    )

    painel = ft.Container(
        content=ft.Column(spacing=10, controls=[
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.ALARM, color="#2d6cdf", size=18),
                    ft.Text("Lembretes de cuidado", weight=ft.FontWeight.BOLD, size=14),
                ],
            ),
            lista_controles,
            formulario,
        ]),
    )

    # Expõe stop para quem precisar encerrar a thread
    painel.data = {"stop": _parar_thread.set}
    return painel
