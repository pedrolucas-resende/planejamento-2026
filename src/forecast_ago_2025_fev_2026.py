"""
Script de Forecasting de Demanda - Por Produto
Treina com: Todo histórico + Jan-Jul 2025 (dados reais)
Prevê: Ago 2025 até Fev 2026 (próximos 7 meses)
PRODUTOS: 0km, Semi, Usada (separadamente)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ForecastingDemandaPorProduto:
    def __init__(self):
        self.df_raw = None
        self.df_forecast = None
        
    def load_data(self):
        print("[DEBUG] Iniciando load_data...")
        logger.info("Carregando dados brutos...")
        try:
            self.df_raw = pd.read_csv('data/csv/input_o.csv')
            print(f"[DEBUG] Carregados {len(self.df_raw)} registros")
            logger.info(f"✓ Carregados {len(self.df_raw):,} registros")
            return True
        except Exception as e:
            print(f"[DEBUG] ERRO no load_data: {e}")
            logger.error(f"Arquivo input_o.csv não encontrado. Execute: python src/input_o.py - Erro: {e}")
            return False
    
    def prepare_data(self):
        print("[DEBUG] Iniciando prepare_data...")
        logger.info("Preparando dados para treinamento...")
        
        self.df_raw['dataValor'] = pd.to_datetime(self.df_raw['dataValor'])
        self.df_raw['periodo'] = self.df_raw['dataValor'].dt.strftime('%Y-%m')
        
        print("[DEBUG] Agrupando por filial, período e produto...")
        # Agrupar por filial, período e produto
        self.df_agg = self.df_raw.groupby(['filial', 'periodo'])[
            ['alugadas_0km', 'alugadas_semi', 'alugadas_usada']
        ].sum().reset_index()
        
        self.df_agg['dataValor'] = pd.to_datetime(self.df_agg['periodo'])
        self.df_agg = self.df_agg.sort_values(['filial', 'dataValor'])
        
        print(f"[DEBUG] prepare_data concluído - {self.df_agg['filial'].nunique()} filiais")
        logger.info(f"✓ Dados agregados para {self.df_agg['filial'].nunique()} filiais")
        logger.info(f"  Período: {self.df_agg['dataValor'].min().date()} até {self.df_agg['dataValor'].max().date()}")
        
        return True
    
    def forecast_media_movel(self, series, window=3, periods=7):
        if len(series) < window:
            window = max(1, len(series) - 1)
        
        ma = series.rolling(window=window).mean()
        last_ma = ma.iloc[-1]
        
        if pd.isna(last_ma):
            last_ma = series.mean()
        
        return pd.Series([last_ma] * periods)
    
    def forecast_linear_regression(self, series, periods=7):
        if len(series) < 3:
            return pd.Series([series.mean()] * periods)
        
        X = np.arange(len(series)).reshape(-1, 1)
        y = series.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        X_future = np.arange(len(series), len(series) + periods).reshape(-1, 1)
        forecast = model.predict(X_future)
        forecast = np.maximum(forecast, 0)
        
        return pd.Series(forecast)
    
    def forecast_exponential_smoothing(self, series, periods=7, alpha=0.3):
        if len(series) < 2:
            return pd.Series([series.mean()] * periods)
        
        result = [series.iloc[0]]
        
        for i in range(1, len(series)):
            result.append(alpha * series.iloc[i] + (1 - alpha) * result[-1])
        
        last_smooth = result[-1]
        return pd.Series([last_smooth] * periods)
    
    def run_forecast(self):
        print("[DEBUG] Iniciando run_forecast...")
        logger.info("Executando forecasting para Ago 2025 - Fev 2026...")
        
        forecast_period = pd.date_range('2025-08', '2026-02', freq='MS')
        forecast_periods = len(forecast_period)
        
        print(f"[DEBUG] Períodos: {forecast_period[0]} até {forecast_period[-1]}")
        logger.info(f"  Forecast: {forecast_period[0].strftime('%b/%Y')} até {forecast_period[-1].strftime('%b/%Y')} ({forecast_periods} meses)")
        
        # Produtos a fazer forecasting
        produtos = ['alugadas_0km', 'alugadas_semi', 'alugadas_usada']
        
        resultados_list = []
        filiais = sorted(self.df_agg['filial'].unique())
        print(f"[DEBUG] Processando {len(filiais)} filiais x {len(produtos)} produtos...")
        
        for idx, filial in enumerate(filiais):
            if idx % 50 == 0:
                print(f"[DEBUG] Progresso: {idx}/{len(filiais)} filiais")
            
            df_filial = self.df_agg[self.df_agg['filial'] == filial].sort_values('dataValor')
            
            # Para cada produto
            for produto in produtos:
                # Filtrar dados até Jul 2025 para treinamento
                mask_train = df_filial['dataValor'] <= '2025-07-31'
                series_train = df_filial[mask_train][produto]
                
                if len(series_train) < 2:
                    continue
                
                # 3 métodos de forecast
                fc_ma = self.forecast_media_movel(series_train, window=3, periods=forecast_periods)
                fc_lr = self.forecast_linear_regression(series_train, periods=forecast_periods)
                fc_es = self.forecast_exponential_smoothing(series_train, periods=forecast_periods, alpha=0.3)
                
                # Ensemble
                forecast_ensemble = (fc_ma.values + fc_lr.values + fc_es.values) / 3
                
                # Armazenar
                produto_nome = produto.replace('alugadas_', '')
                for i, periodo in enumerate(forecast_period):
                    periodo_str = periodo.strftime('%Y-%m')
                    
                    resultados_list.append({
                        'filial': filial,
                        'periodo': periodo_str,
                        'produto': produto_nome,
                        'forecast_ma': fc_ma.iloc[i],
                        'forecast_lr': fc_lr.iloc[i],
                        'forecast_es': fc_es.iloc[i],
                        'forecast_ensemble': forecast_ensemble[i]
                    })
        
        self.df_forecast = pd.DataFrame(resultados_list)
        
        print(f"[DEBUG] run_forecast concluído - {len(resultados_list)} séries")
        logger.info(f"✓ Forecast gerado para {len(resultados_list)} séries")
        
        return True
    
    def calculate_summary(self):
        print("[DEBUG] Calculando resumo...")
        logger.info("Calculando resumo...")
        
        # Resumo por período e produto
        summary = self.df_forecast.groupby(['periodo', 'produto']).agg({
            'forecast_ensemble': 'sum'
        }).reset_index()
        
        summary.columns = ['periodo', 'produto', 'demanda_forecast']
        return summary
    
    def save_results(self):
        Path('data/csv').mkdir(parents=True, exist_ok=True)
        
        print("[DEBUG] Salvando resultados...")
        logger.info("Salvando resultados...")
        
        output_forecast = 'data/csv/forecast_ago_2025_fev_2026_por_produto.csv'
        self.df_forecast.to_csv(output_forecast, index=False, encoding='utf-8')
        logger.info(f"✓ Forecast: {output_forecast}")
        
        summary = self.calculate_summary()
        output_summary = 'data/csv/forecast_resumo_ago_2025_fev_2026_por_produto.csv'
        summary.to_csv(output_summary, index=False, encoding='utf-8')
        logger.info(f"✓ Resumo: {output_summary}")
        
        return output_forecast, output_summary
    
    def print_summary(self):
        summary = self.calculate_summary()
        
        print("\n" + "="*100)
        print("📊 FORECAST POR PRODUTO: Ago 2025 até Fev 2026")
        print("="*100 + "\n")
        
        print("📈 Métodos Utilizados (Ensemble):")
        print("  1. Média Móvel (3 períodos)")
        print("  2. Regressão Linear")
        print("  3. Suavização Exponencial")
        print("  → Resultado: Média ponderada dos 3\n")
        
        print("📊 Demanda Prevista por Período e Produto:\n")
        print(f"{'Período':<12} {'0km':<15} {'Semi':<15} {'Usada':<15}")
        print("-" * 58)
        
        for periodo in sorted(summary['periodo'].unique()):
            df_periodo = summary[summary['periodo'] == periodo]
            valores = {}
            for _, row in df_periodo.iterrows():
                valores[row['produto']] = int(row['demanda_forecast'])
            
            print(f"{periodo:<12} {valores.get('0km', 0):>13,} {valores.get('semi', 0):>13,} {valores.get('usada', 0):>13,}")
        
        print("-" * 58)
        print(f"{'TOTAL':<12} {summary[summary['produto']=='0km']['demanda_forecast'].sum():>13,.0f} {summary[summary['produto']=='semi']['demanda_forecast'].sum():>13,.0f} {summary[summary['produto']=='usada']['demanda_forecast'].sum():>13,.0f}\n")
        
        print("="*100)
        print("✅ Resultados salvos")
        print("="*100 + "\n")
    
    def run(self):
        print("\n" + "="*100)
        print("🚀 Forecasting de Demanda por Produto (Ago 2025 - Fev 2026)")
        print("   Produtos: 0km, Semi, Usada")
        print("   Treinado com: Histórico completo + dados reais Jan-Jul 2025")
        print("="*100 + "\n")
        
        if not self.load_data():
            return False
        if not self.prepare_data():
            return False
        if not self.run_forecast():
            return False
        
        self.save_results()
        self.print_summary()
        
        return True

def main():
    print("oi")
    forecast = ForecastingDemandaPorProduto()
    print("oi2")
    forecast.run()
    

if __name__ == '__main__':
    main()
