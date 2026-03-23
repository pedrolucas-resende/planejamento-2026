# Mottu S&OP Forecasting - Elite Model 🧠

Repositório dedicado à análise, categorização e previsão de vendas (locação de motos) para suporte ao ciclo de S&OP. O projeto utiliza modelos de Gradient Boosting (LightGBM) e bibliotecas de séries temporais de alta performance para reduzir o erro de planejamento.

## 🛠️ Stack Técnica

- **Linguagem:** Python 3.12
- **Data Source:** Google BigQuery (via `gcloud auth`)
- **Modelagem:** LightGBM, Darts (Global Models)

## 📂 Estrutura do Projeto

- `src/forecast/`: Core da inteligência de predição.
  - `preparar_dados_forecasting.py`: ETL e Feature Engineering (Lags, Sazonalidade).
  - `treinar_modelo_global_darts.py`: Treinamento do modelo "Elite".
- `src/`: Scripts de análise por hierarquia (População, Região, Estado).
- `queries/`: SQLs estruturados para consumo direto do BigQuery.
- `data/xlsx/`: Armazenamento de snapshots e visões de planejamento (ex: `overview_sales.xlsx`).
- `zzz/`: Scripts legados e utilitários de exportação de gráficos.

## 🚀 Como Executar

1. **Configurar Ambiente:**

   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   gcloud auth application-default login
   ```

2. **⚙️ Fluxo de Execução**
   ```bash
   ./run_pipeline.sh
   ```

## 📈 Performance Atual

- Métrica Alvo: MAE (Mean Absolute Error)
- Resultado: **5.8 motos** (Março/2026)

## 📊 Dashboard

Visualizações interativas e relatórios consolidados para monitoramento da performance do modelo e métricas de S&OP em tempo real.

[📊 Visualizar Dashboard](https://pedrolucas-resende.github.io/planejamento-2026/dashboard_forecast_mottu.html)
