# Sistema de Monitoramento Inteligente de Pressão

Software desktop para monitoramento em tempo real da distribuição de
pressão em pacientes cadeirantes ou acamados, com foco na prevenção
de lesões por pressão (LPP).

Construído em **Python + Flet (interface) + Matplotlib (mapa térmico)
+ SQLite (persistência)**, com arquitetura MVC.

## 1. Instalação

> **Importante:** o `requirements.txt` fixa `flet==0.28.3` de propósito.
> Versões mais novas do Flet (0.80.0+, lançadas como "Flet 1.0 Beta")
> trazem mudanças incompatíveis em praticamente toda a API (`ft.app()` →
> `ft.run()`, `ft.padding.symmetric` → `ft.Padding(...)`, `ft.alignment.center`
> → `ft.Alignment.CENTER`, FilePicker virou serviço assíncrono, etc.).
> Este projeto foi escrito contra a API estável anterior. Se você já
> instalou uma versão mais nova, desinstale antes:
> ```bash
> pip uninstall flet -y
> pip install -r requirements.txt
> ```

```bash
cd SistemaMonitoramento
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Executando

Abre a aplicação como **app desktop nativo** (janela própria,
via Flutter/Flet). Se preferir abrir no navegador em vez de uma
janela nativa, troque a última linha de `main.py` por:

```python
ft.app(target=main, view=ft.AppView.WEB_BROWSER)
```

Na primeira execução, o sistema cria automaticamente:

- `data/monitoramento.db` — banco SQLite com as tabelas de pacientes,
  reposicionamentos e leituras.
- `data/config.json` — configurações (IP da ESP32, limites de tempo,
  paleta do mapa, etc.), editáveis também pela tela **Configurações**.

## 3. Modo simulador (testar sem a ESP32)

Por padrão, `modo_simulacao = True` em `data/config.json` (ou na tela
de Configurações). Nesse modo, o sistema usa `SimuladorESP32`
(em `services/receptor.py`), que gera uma matriz de pressão sintética
com pontos de contato realistas (ísquios e sacro), permitindo testar
toda a aplicação — mapa térmico, indicador de risco, histórico,
relatórios — sem nenhum hardware conectado.

Para conectar à ESP32 real, desmarque "Usar simulador" em
Configurações (ou defina `"modo_simulacao": false` no `config.json`)
e informe o IP/porta corretos.

## 4. Protocolo esperado da ESP32

A classe `Receptor` (`services/receptor.py`) espera uma conexão
**TCP simples**, na qual a ESP32 envia repetidamente uma linha de
texto terminada em `\n`, contendo um JSON no formato:

```json
{"matrix": [[12, 15, 9, ...], [18, 22, 14, ...], ...]}
```

onde cada valor é a leitura crua de um sensor (ex.: 0–4095 de um ADC).
O número de linhas/colunas deve corresponder a `sensor_linhas` e
`sensor_colunas` em `data/config.json`. Ajuste o firmware da ESP32
para esse formato, ou adapte o método `receber_matriz()` caso utilize
outro protocolo (ex.: MQTT, UDP, Serial/USB).

## 5. Estrutura do projeto

```
SistemaMonitoramento/
├── main.py                      # ponto de entrada, roteamento de telas
├── database.py                  # schema SQLite + conexões
├── requirements.txt
├── data/                        # banco de dados e config.json (gerados em runtime)
├── models/                      # Paciente, Reposicionamento, Leitura
├── services/
│   ├── receptor.py              # comunicação TCP com a ESP32 + SimuladorESP32
│   ├── processamento.py         # interpolação, normalização, estatísticas
│   └── visualizacao.py          # mapa térmico em Matplotlib
├── controllers/
│   ├── paciente_controller.py
│   ├── monitoramento_controller.py   # orquestra Receptor -> Processamento -> Visualização -> BD
│   ├── historico_controller.py
│   └── relatorio_controller.py
└── views/
    ├── components/ (top_bar, side_menu)
    ├── home_view.py
    ├── paciente_view.py
    ├── monitoramento_view.py    # tela com os 3 painéis (status / mapa / eventos)
    ├── historico_view.py
    ├── relatorios_view.py
    └── configuracoes_view.py
```