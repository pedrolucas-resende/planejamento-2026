# Mottu S&OP Forecasting - Elite Model 🧠

Repositório dedicado à análise, categorização e previsão de vendas (locação de motos) para suporte ao ciclo de S&OP. O projeto utiliza modelos de Gradient Boosting (LightGBM) e bibliotecas de séries temporais de alta performance para reduzir o erro de planejamento.

## 🛠️ Stack Técnica
- **Linguagem:** Python 3.12
- **Data Source:** Google BigQuery (via `gcloud auth`)
- **Modelagem:** LightGBM, Darts (Global Models)

## 📂 Estrutura do Projeto
- `src/forecast/`: Core da inteligência de predição.
    - `preparar_dados_forecasting.py`: ETL e Feature Engineering (Lags, Sazonalidade).
    - `testar_modelos_forecasting.py`: Backtesting e validação de métricas.
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
- Resultado: 1.75 motos (Refinado em Março/2026)

