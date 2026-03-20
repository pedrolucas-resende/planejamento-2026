#!/bin/bash

# Interromper o script em caso de erro
set -e

echo "🚀 Iniciando Pipeline de S&OP..."

# 1. Rodar input_o.py
echo "📥 Extraindo dados brutos (input_o.py)..."
python3 src/input_o.py

# 2. Rodar scripts de análise (em paralelo ou sequência)
echo "📊 Processando hierarquias e categorização..."
for script in src/sheets/*.py; do
    echo "🔄 Rodando $script..."
    python3 "$script"
done

# 3. Rodar scripts de Forecast
echo "🧠 Treinando Modelo Elite e gerando Forecast..."
python3 src/forecast/preparar_dados_forecasting.py
python3 src/forecast/treinar_modelo_global_darts.py

echo "✅ Pipeline finalizado com sucesso! Dados prontos em data/xlsx/"
