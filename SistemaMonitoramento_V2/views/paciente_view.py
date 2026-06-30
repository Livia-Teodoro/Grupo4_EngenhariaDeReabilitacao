"""
views/paciente_view.py

Tela de cadastro/edição do paciente, com cálculo automático
de idade, IMC e classificação do IMC conforme a especificação.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from controllers.paciente_controller import PacienteController
from models.paciente import Paciente

OPCOES_SEXO = ["Masculino", "Feminino", "Outro"]
OPCOES_MOBILIDADE = ["Acamado", "Cadeirante", "Semi-móvel", "Móvel com auxílio"]


def build_paciente_view(
    paciente: Optional[Paciente],
    on_salvar: Callable[[], None],
    on_cancelar: Callable[[], None],
) -> ft.Container:

    controller = PacienteController()
    editando = paciente is not None

    campo_nome = ft.TextField(label="Nome completo", value=paciente.nome if editando else "", expand=True)
    campo_nascimento = ft.TextField(
        label="Data de nascimento (AAAA-MM-DD)",
        value=paciente.data_nascimento if editando else "",
        width=240,
    )
    campo_sexo = ft.Dropdown(
        label="Sexo",
        value=paciente.sexo if editando else None,
        options=[ft.dropdown.Option(o) for o in OPCOES_SEXO],
        width=200,
    )
    campo_altura = ft.TextField(
        label="Altura (m)", value=str(paciente.altura) if editando and paciente.altura else "",
        width=140, keyboard_type=ft.KeyboardType.NUMBER,
    )
    campo_peso = ft.TextField(
        label="Peso (kg)", value=str(paciente.peso) if editando and paciente.peso else "",
        width=140, keyboard_type=ft.KeyboardType.NUMBER,
    )
    campo_mobilidade = ft.Dropdown(
        label="Mobilidade",
        value=paciente.mobilidade if editando else None,
        options=[ft.dropdown.Option(o) for o in OPCOES_MOBILIDADE],
        width=220,
    )
    campo_condicao = ft.TextField(
        label="Condição clínica", value=paciente.condicao if editando else "", expand=True,
    )
    campo_observacoes = ft.TextField(
        label="Observações", value=paciente.observacoes if editando else "",
        multiline=True, min_lines=3, max_lines=5, expand=True,
    )

    texto_idade = ft.Text("Idade: -", size=13, color="#6b7280")
    texto_imc = ft.Text("IMC: -", size=13, color="#6b7280")
    texto_erro = ft.Text("", color="#c0392b", size=13)

    def _atualizar_calculados(e=None):
        nasc = campo_nascimento.value.strip() if campo_nascimento.value else None
        altura_txt = campo_altura.value.strip() if campo_altura.value else None
        peso_txt = campo_peso.value.strip() if campo_peso.value else None

        try:
            altura = float(altura_txt.replace(",", ".")) if altura_txt else None
        except ValueError:
            altura = None
        try:
            peso = float(peso_txt.replace(",", ".")) if peso_txt else None
        except ValueError:
            peso = None

        temp = Paciente(nome="", data_nascimento=nasc, altura=altura, peso=peso)
        texto_idade.value = f"Idade: {temp.idade if temp.idade is not None else '-'} anos"
        if temp.imc is not None:
            texto_imc.value = f"IMC: {temp.imc} ({temp.classificacao_imc})"
        else:
            texto_imc.value = "IMC: -"
        if texto_idade.page:
            texto_idade.page.update()

    campo_nascimento.on_change = _atualizar_calculados
    campo_altura.on_change = _atualizar_calculados
    campo_peso.on_change = _atualizar_calculados

    def _salvar(e):
        if not campo_nome.value or not campo_nome.value.strip():
            texto_erro.value = "O nome do paciente é obrigatório."
            texto_erro.page.update()
            return

        try:
            altura = float(campo_altura.value.replace(",", ".")) if campo_altura.value else None
            peso = float(campo_peso.value.replace(",", ".")) if campo_peso.value else None
        except ValueError:
            texto_erro.value = "Altura e peso devem ser numéricos (ex.: 1.70 / 68.5)."
            texto_erro.page.update()
            return

        dados = Paciente(
            id=paciente.id if editando else None,
            nome=campo_nome.value.strip(),
            data_nascimento=campo_nascimento.value.strip() or None,
            sexo=campo_sexo.value,
            altura=altura,
            peso=peso,
            mobilidade=campo_mobilidade.value,
            condicao=campo_condicao.value.strip() or None,
            observacoes=campo_observacoes.value.strip() or None,
        )

        if editando:
            controller.atualizar(dados)
        else:
            controller.criar(dados)

        on_salvar()

    _atualizar_calculados()

    return ft.Container(
        expand=True,
        padding=24,
        bgcolor="#f5f7fa",
        content=ft.Column(
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text(
                    "Editar Paciente" if editando else "Novo Paciente",
                    size=22, weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    padding=24,
                    bgcolor="#ffffff",
                    border_radius=14,
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Row(controls=[campo_nome]),
                            ft.Row(spacing=14, controls=[campo_nascimento, campo_sexo]),
                            ft.Row(spacing=14, controls=[campo_altura, campo_peso, campo_mobilidade]),
                            ft.Row(controls=[texto_idade, ft.Container(width=20), texto_imc]),
                            ft.Row(controls=[campo_condicao]),
                            ft.Row(controls=[campo_observacoes]),
                            texto_erro,
                            ft.Row(
                                alignment=ft.MainAxisAlignment.END,
                                spacing=10,
                                controls=[
                                    ft.OutlinedButton("Cancelar", on_click=lambda e: on_cancelar()),
                                    ft.ElevatedButton(
                                        "Salvar Paciente",
                                        icon=ft.Icons.SAVE_OUTLINED,
                                        bgcolor="#2d6cdf",
                                        color="#ffffff",
                                        on_click=_salvar,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
