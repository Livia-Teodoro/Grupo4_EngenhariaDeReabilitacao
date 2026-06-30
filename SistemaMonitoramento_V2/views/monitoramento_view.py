"""
views/monitoramento_view.py

Tela principal de monitoramento, dividida em três painéis:
esquerdo (status e ações), central (mapa térmico) e direito
(eventos/alertas/IA).

A aquisição roda inteiramente dentro do MonitoramentoController
(em thread própria). Esta view apenas registra um callback e
atualiza os controles do Flet quando notificada.
"""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Callable

import flet as ft

from controllers.monitoramento_controller import EstadoMonitoramento, MonitoramentoController
from models.paciente import Paciente
from services.visualizacao import INTERPOLACOES_DISPONIVEIS, PALETAS_DISPONIVEIS
from utils.config import Configuracoes
from views.lembretes_panel import build_lembretes_panel

CORES_RISCO = {
    "verde": ("#e8f8ef", "#1e8e3e", "Paciente seguro"),
    "amarelo": ("#fff8e1", "#b7791f", "Reposicionamento recomendado"),
    "vermelho": ("#fdecea", "#c0392b", "Reposicionamento urgente"),
}


def _formatar_tempo(segundos: float) -> str:
    segundos = int(max(0, segundos))
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def build_monitoramento_view(
    page: ft.Page,
    paciente: Paciente,
    config: Configuracoes,
    on_sair: Callable[[], None],
) -> ft.Container:

    controller = MonitoramentoController(paciente_id=paciente.id, config=config)

    # ---------- Painel esquerdo: status ----------

    icone_status = ft.Icon(ft.Icons.CIRCLE, color="#c0392b", size=12)
    texto_status = ft.Text("Desconectado", size=13, color="#6b7280")

    texto_tempo_reposicionamento = ft.Text("00:00", size=26, weight=ft.FontWeight.BOLD)
    texto_tempo_estabilidade = ft.Text("00:00", size=18, weight=ft.FontWeight.W_600)
    texto_pressao_max = ft.Text("-", size=20, weight=ft.FontWeight.BOLD, color="#c0392b")
    texto_pressao_media = ft.Text("-", size=20, weight=ft.FontWeight.BOLD, color="#2d6cdf")
    texto_pressao_min = ft.Text("-", size=20, weight=ft.FontWeight.BOLD, color="#1e8e3e")

    icone_risco = ft.Icon(ft.Icons.SHIELD_OUTLINED, color=CORES_RISCO["verde"][1])
    texto_risco = ft.Text(CORES_RISCO["verde"][2], size=14, weight=ft.FontWeight.W_600,
                           color=CORES_RISCO["verde"][1])
    card_risco = ft.Container(
        padding=16, border_radius=12, bgcolor=CORES_RISCO["verde"][0],
        content=ft.Row(spacing=10, controls=[icone_risco, texto_risco]),
    )

    botao_iniciar = ft.ElevatedButton(
        "Iniciar Monitoramento", icon=ft.Icons.PLAY_ARROW, bgcolor="#2d6cdf", color="#ffffff",
    )
    botao_parar = ft.ElevatedButton(
        "Parar Monitoramento", icon=ft.Icons.STOP, disabled=True, bgcolor="#fdecea", color="#c0392b",
    )
    botao_confirmar = ft.ElevatedButton(
        "Confirmar Reposicionamento", icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
        bgcolor="#1e8e3e", color="#ffffff",
    )
    botao_salvar_imagem = ft.OutlinedButton("Salvar Imagem", icon=ft.Icons.IMAGE_OUTLINED)
    botao_salvar_csv = ft.OutlinedButton("Salvar CSV", icon=ft.Icons.TABLE_CHART_OUTLINED)

    # ---------- Centro: mapa térmico ----------

    imagem_mapa = ft.Image(fit=ft.ImageFit.CONTAIN, expand=True, visible=False)
    texto_sem_dados = ft.Text("Aguardando dados da ESP32...", color="#9aa3b2")

    dropdown_paleta = ft.Dropdown(
        label="Paleta", value=config.paleta_mapa, width=150,
        options=[ft.dropdown.Option(p) for p in PALETAS_DISPONIVEIS],
    )
    dropdown_interpolacao = ft.Dropdown(
        label="Interpolação", value="bicubic", width=160,
        options=[ft.dropdown.Option(i) for i in INTERPOLACOES_DISPONIVEIS],
    )
    slider_zoom = ft.Slider(min=0.2, max=1.0, value=1.0, divisions=8, label="Zoom {value}", expand=True)

    # ---------- Painel direito ----------

    lista_eventos = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    card_ia = ft.Container(
        padding=16, border_radius=12, bgcolor="#f5f7fa", border=ft.border.all(1, "#e3e7ed"),
        content=ft.Column(spacing=6, controls=[
            ft.Row(spacing=6, controls=[
                ft.Icon(ft.Icons.SMART_TOY_OUTLINED, color="#9aa3b2"),
                ft.Text("Análise da IA", weight=ft.FontWeight.W_600),
            ]),
            ft.Text("Status: Aguardando modelo", size=12, color="#6b7280"),
            ft.Text("Probabilidade de lesão: --", size=12, color="#6b7280"),
            ft.Text("Região crítica: --", size=12, color="#6b7280"),
            ft.Text("Sugestão: --", size=12, color="#6b7280"),
        ]),
    )

    # ---------- File picker (salvar imagem / CSV) ----------

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def _ao_resultado_arquivo(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        if e.path.lower().endswith(".csv"):
            controller.salvar_csv(e.path)
        else:
            controller.salvar_imagem(e.path)
        _adicionar_evento(f"{datetime.now().strftime('%H:%M:%S')} - Arquivo salvo em {e.path}")
        page.update()

    file_picker.on_result = _ao_resultado_arquivo

    # ---------- Eventos / log ----------

    def _adicionar_evento(texto: str):
        lista_eventos.controls.insert(
            0,
            ft.Container(
                padding=10, border_radius=8, bgcolor="#ffffff", border=ft.border.all(1, "#e3e7ed"),
                content=ft.Text(texto, size=12),
            ),
        )
        if len(lista_eventos.controls) > 30:
            lista_eventos.controls.pop()

    # ---------- Callback chamado pela thread de aquisição ----------

    def _ao_atualizar(estado: EstadoMonitoramento):
        if estado.erro:
            icone_status.color = "#c0392b"
            texto_status.value = f"Erro: {estado.erro}"
        elif estado.conectado:
            icone_status.color = "#1e8e3e"
            texto_status.value = "Conectado"

        if estado.png_bytes:
            imagem_mapa.src_base64 = base64.b64encode(estado.png_bytes).decode("utf-8")
            imagem_mapa.visible = True
            texto_sem_dados.visible = False

        texto_tempo_reposicionamento.value = _formatar_tempo(estado.tempo_desde_reposicionamento)
        texto_tempo_estabilidade.value = _formatar_tempo(estado.tempo_estabilidade)
        texto_pressao_max.value = f"{estado.pressao_maxima:.0f}"
        texto_pressao_media.value = f"{estado.pressao_media:.0f}"
        texto_pressao_min.value = f"{estado.pressao_minima:.0f}"

        cor_fundo, cor_texto, label = CORES_RISCO.get(estado.risco, CORES_RISCO["verde"])
        card_risco.bgcolor = cor_fundo
        texto_risco.value = label
        texto_risco.color = cor_texto
        icone_risco.color = cor_texto

        if page:
            page.update()

    controller.registrar_callback(_ao_atualizar)

    # ---------- Ações dos botões ----------

    def _iniciar(e):
        controller.iniciar()
        botao_iniciar.disabled = True
        botao_parar.disabled = False
        _adicionar_evento(f"{datetime.now().strftime('%H:%M:%S')} - Monitoramento iniciado")
        page.update()

    def _parar(e):
        controller.parar()
        botao_iniciar.disabled = False
        botao_parar.disabled = True
        _adicionar_evento(f"{datetime.now().strftime('%H:%M:%S')} - Monitoramento pausado")
        page.update()

    def _confirmar(e):
        rep = controller.confirmar_reposicionamento()
        _adicionar_evento(
            f"{rep.hora} - Reposicionamento confirmado (sentado {rep.tempo_sentado_formatado})"
        )
        page.update()

    def _salvar_imagem(e):
        file_picker.save_file(file_name="mapa_pressao.png", allowed_extensions=["png"])

    def _salvar_csv(e):
        file_picker.save_file(file_name="leituras.csv", allowed_extensions=["csv"])

    def _mudar_paleta(e):
        controller.definir_paleta(dropdown_paleta.value)

    def _mudar_interpolacao(e):
        controller.definir_interpolacao(dropdown_interpolacao.value)

    def _mudar_zoom(e):
        controller.definir_zoom(slider_zoom.value)

    def _sair(e):
        controller.finalizar()
        on_sair()

    botao_iniciar.on_click = _iniciar
    botao_parar.on_click = _parar
    botao_confirmar.on_click = _confirmar
    botao_salvar_imagem.on_click = _salvar_imagem
    botao_salvar_csv.on_click = _salvar_csv
    dropdown_paleta.on_change = _mudar_paleta
    dropdown_interpolacao.on_change = _mudar_interpolacao
    slider_zoom.on_change = _mudar_zoom

    # ---------- Montagem dos painéis ----------

    painel_esquerdo = ft.Container(
        width=300, padding=16, bgcolor="#ffffff", border_radius=14,
        content=ft.Column(spacing=14, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Text(paciente.nome, weight=ft.FontWeight.BOLD, size=16),
            ft.Row(spacing=6, controls=[icone_status, texto_status]),
            ft.Divider(height=1),
            ft.Text("Tempo desde reposicionamento", size=12, color="#6b7280"),
            texto_tempo_reposicionamento,
            ft.Text("Tempo de estabilidade", size=12, color="#6b7280"),
            texto_tempo_estabilidade,
            ft.Divider(height=1),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Column(spacing=0, controls=[ft.Text("Máx.", size=11, color="#6b7280"), texto_pressao_max]),
                ft.Column(spacing=0, controls=[ft.Text("Média", size=11, color="#6b7280"), texto_pressao_media]),
                ft.Column(spacing=0, controls=[ft.Text("Mín.", size=11, color="#6b7280"), texto_pressao_min]),
            ]),
            card_risco,
            ft.Divider(height=1),
            botao_confirmar,
            ft.Row(spacing=8, controls=[botao_salvar_imagem, botao_salvar_csv]),
            ft.Divider(height=1),
            botao_iniciar,
            botao_parar,
            ft.OutlinedButton("Voltar para Pacientes", icon=ft.Icons.ARROW_BACK, on_click=_sair),
        ]),
    )

    painel_central = ft.Container(
        expand=True, padding=16, bgcolor="#ffffff", border_radius=14,
        content=ft.Column(spacing=10, expand=True, controls=[
            ft.Row(spacing=10, controls=[dropdown_paleta, dropdown_interpolacao, slider_zoom]),
            ft.Stack(expand=True, controls=[
                ft.Container(alignment=ft.alignment.center, expand=True, content=texto_sem_dados),
                imagem_mapa,
            ]),
        ]),
    )

    painel_direito = ft.Container(
        width=300, padding=16, bgcolor="#ffffff", border_radius=14,
        content=ft.Column(spacing=14, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Text("Últimos eventos", weight=ft.FontWeight.BOLD, size=15),
            lista_eventos,
            ft.Divider(height=1),
            card_ia,
            ft.Divider(height=1),
            build_lembretes_panel(page=page, paciente=paciente, on_log=_adicionar_evento),
        ]),
    )

    return ft.Container(
        expand=True,
        padding=20,
        bgcolor="#f5f7fa",
        content=ft.Row(expand=True, spacing=16, controls=[painel_esquerdo, painel_central, painel_direito]),
    )
