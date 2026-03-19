"""
Script para agregar dados de demanda por Filial + Mês + Produto
e despivotar para usar em Pivot Table e Forecast

Fonte: Excel (aba BASE) OU BigQuery (projeto: dm-mottu-aluguel)
Agregação: Por Filial
Produtos: 0km, Semi, Usada
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DemandaForecastPrep:
    """Preparação de dados para forecast de demanda"""
    
    def __init__(self, source='excel'):
        self.source = source
        self.df = None
        self.df_aggregated = None
        
    def load_from_excel(self):
        """Carregar dados do Excel (aba BASE)"""
        
        logger.info("Carregando dados do Excel...")
        logger.info("Arquivo: data/xlsx/overview_sales.xlsx")
        logger.info("Aba: BASE")
        
        try:
            excel_file = 'data/xlsx/overview_sales.xlsx'
            
            # Tenta ler a aba BASE
            self.df = pd.read_excel(excel_file, sheet_name='BASE')
            
            logger.info(f"✓ Carregados {len(self.df):,} registros do Excel")
            
            # Verificar colunas necessárias
            required_cols = ['dataValor', 'filial', 'alugadas_0km', 'alugadas_semi', 'alugadas_usada']
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            
            if missing_cols:
                logger.error(f"❌ Colunas faltando: {missing_cols}")
                logger.info(f"Colunas disponíveis: {list(self.df.columns)}")
                return False
            
            # Estatísticas
            if 'dataValor' in self.df.columns:
                self.df['dataValor'] = pd.to_datetime(self.df['dataValor'])
                min_date = self.df['dataValor'].min()
                max_date = self.df['dataValor'].max()
                if hasattr(min_date, 'date'):
                    min_date = min_date.date()
                if hasattr(max_date, 'date'):
                    max_date = max_date.date()
                logger.info(f"  Período: {min_date} até {max_date}")
            
            if 'filial' in self.df.columns:
                logger.info(f"  Filiais: {self.df['filial'].nunique()}")
            
            return True
            
        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: data/xlsx/overview_sales.xlsx")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao carregar Excel: {e}")
            return False
    
    def load_from_bigquery(self):
        """Carregar dados do BigQuery (projeto: dm-mottu-aluguel)"""
        
        logger.info("Carregando dados do BigQuery...")
        logger.info("Projeto: dm-mottu-aluguel")
        logger.info("Tabela: z_ren_homologacao.input_o")
        
        try:
            from utils.bigquery_client import rodar_query
            
            query = """
            SELECT 
                dataValor,
                filial,
                alugadas_0km,
                alugadas_semi,
                alugadas_usada,
                alugadas_total
            FROM `dm-mottu-aluguel.z_ren_homologacao.input_o`
            WHERE dataValor >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
            ORDER BY dataValor DESC, filial
            """
            
            logger.info("Executando query...")
            self.df = rodar_query(query, project="dm-mottu-aluguel")
            
            logger.info(f"✓ Carregados {len(self.df):,} registros do BigQuery")
            
            # Verificar tipo de data e converter se necessário
            if 'dataValor' in self.df.columns:
                self.df['dataValor'] = pd.to_datetime(self.df['dataValor'])
                min_date = self.df['dataValor'].min()
                max_date = self.df['dataValor'].max()
                # Seguro: verifica se tem atributo .date() antes de chamar
                if hasattr(min_date, 'date'):
                    min_date = min_date.date()
                if hasattr(max_date, 'date'):
                    max_date = max_date.date()
                logger.info(f"  Período: {min_date} até {max_date}")
            
            if 'filial' in self.df.columns:
                logger.info(f"  Filiais: {self.df['filial'].nunique()}")
            
            return True
            
        except ImportError:
            logger.error("❌ utils.bigquery_client não encontrado")
            logger.error("   Use: python src/prepare_forecast_data.py --source excel")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao carregar BigQuery: {e}")
            logger.error("\nTente:")
            logger.error("1. Execute: gcloud auth application-default login")
            logger.error("2. Verifique acesso ao projeto dm-mottu-aluguel")
            logger.error("3. OU use: python src/prepare_forecast_data.py --source excel")
            return False
    
    def load_data(self):
        """Carregar dados de acordo com a fonte"""
        
        if self.source == 'excel':
            return self.load_from_excel()
        elif self.source == 'bigquery':
            return self.load_from_bigquery()
        else:
            logger.error(f"❌ Fonte desconhecida: {self.source}")
            return False
    
    def prepare_data(self):
        """Preparar e limpar os dados"""
        
        logger.info("Preparando dados...")
        
        # Converter dataValor para datetime
        self.df['dataValor'] = pd.to_datetime(self.df['dataValor'])
        
        # Extrair mês e ano (formato MM/YY)
        self.df['periodo'] = self.df['dataValor'].dt.strftime('%Y-%m')
        
        # Preencher valores NaN com 0
        self.df[['alugadas_0km', 'alugadas_semi', 'alugadas_usada']] = \
            self.df[['alugadas_0km', 'alugadas_semi', 'alugadas_usada']].fillna(0)
        
        # Converter para int
        self.df[['alugadas_0km', 'alugadas_semi', 'alugadas_usada']] = \
            self.df[['alugadas_0km', 'alugadas_semi', 'alugadas_usada']].astype(int)
        
        logger.info("✓ Dados preparados")
        return True
    
    def aggregate_by_filial_month(self):
        """Agregar dados por Filial + Mês"""
        
        logger.info("Agregando por Filial + Mês...")
        
        # Agregar
        self.df_aggregated = self.df.groupby(['filial', 'periodo'])[
            ['alugadas_0km', 'alugadas_semi', 'alugadas_usada']
        ].sum().reset_index()
        
        # Renomear colunas
        self.df_aggregated.columns = ['Filial', 'Período', '0km', 'Semi', 'Usada']
        
        # Ordenar
        self.df_aggregated = self.df_aggregated.sort_values(['Filial', 'Período'])
        
        logger.info(f"✓ Agregados:")
        logger.info(f"  Total de registros: {len(self.df_aggregated):,}")
        logger.info(f"  Filiais únicas: {self.df_aggregated['Filial'].nunique()}")
        logger.info(f"  Períodos únicos: {self.df_aggregated['Período'].nunique()}")
        
        return True
    
    def despivot_products(self):
        """Despivotar produtos em linhas (0km, Semi, Usada)"""
        
        logger.info("Despivotando produtos...")
        
        # Despivotar produtos
        df_melted = pd.melt(
            self.df_aggregated,
            id_vars=['Filial', 'Período'],
            value_vars=['0km', 'Semi', 'Usada'],
            var_name='Produto',
            value_name='Quantidade'
        )
        
        # Garantir ordem
        df_melted = df_melted.sort_values(['Filial', 'Período', 'Produto']).reset_index(drop=True)
        
        # Converter Quantidade para int
        df_melted['Quantidade'] = df_melted['Quantidade'].astype(int)
        
        logger.info(f"✓ Despivotado para {len(df_melted):,} linhas")
        
        return df_melted
    
    def save_output(self, output_path='data/csv/demanda_forecast_prep.csv'):
        """Salvar CSV pronto para Pivot Table"""
        
        Path('data/csv').mkdir(parents=True, exist_ok=True)
        
        df_final = self.despivot_products()
        df_final.to_csv(output_path, index=False, encoding='utf-8', quoting=1)
        
        logger.info(f"✓ Salvo em: {output_path}")
        logger.info(f"\n{'='*70}")
        logger.info(f"PRÓXIMOS PASSOS - Montar Pivot Table no Excel:")
        logger.info(f"{'='*70}")
        logger.info(f"1. Abra o arquivo em Excel:")
        logger.info(f"   open {output_path}")
        logger.info(f"\n2. Selecione todos os dados (Cmd+A)")
        logger.info(f"\n3. Insert → PivotTable")
        logger.info(f"\n4. Configure a Pivot Table:")
        logger.info(f"   ✓ LINHAS (Rows):")
        logger.info(f"     - Filial")
        logger.info(f"     - Produto")
        logger.info(f"   ✓ COLUNAS (Columns):")
        logger.info(f"     - Período")
        logger.info(f"   ✓ VALORES (Values):")
        logger.info(f"     - Sum of Quantidade")
        logger.info(f"\n5. Resultado esperado:")
        logger.info(f"   Filial | Produto | 01-25 | 02-25 | 03-25 | ... | 12-26")
        logger.info(f"{'='*70}\n")
        
        return output_path
    
    def show_sample(self):
        """Mostrar amostra dos dados"""
        
        logger.info("\n📊 Amostra dos dados despivotados:")
        logger.info("-" * 70)
        df_sample = self.despivot_products().head(20)
        print(df_sample.to_string(index=False))
        logger.info("-" * 70)
    
    def run(self, output_path='data/csv/demanda_forecast_prep.csv'):
        """Executar o pipeline completo"""
        
        print("\n" + "="*70)
        print("🚀 Pipeline: Preparação de Dados para Forecast de Demanda")
        print("="*70)
        print(f"Fonte: {self.source.upper()}")
        print("Agregação: Por Filial + Período (Mês)")
        print("Produtos: 0km, Semi, Usada")
        print("="*70 + "\n")
        
        # Executar pipeline
        if not self.load_data():
            logger.error(f"❌ Falha ao carregar dados de {self.source.upper()}")
            return False
        
        if not self.prepare_data():
            logger.error("❌ Falha ao preparar dados")
            return False
        
        if not self.aggregate_by_filial_month():
            logger.error("❌ Falha ao agregar dados")
            return False
        
        # Salvar e mostrar resultado
        self.save_output(output_path)
        self.show_sample()
        
        print("\n" + "="*70)
        print("✅ Pipeline concluído com sucesso!")
        print("="*70 + "\n")
        
        return True

def main():
    """Função principal"""
    
    # Determinar fonte (padrão: excel, pode ser bigquery)
    source = 'excel'
    
    if '--source' in sys.argv:
        idx = sys.argv.index('--source')
        if idx + 1 < len(sys.argv):
            source = sys.argv[idx + 1]
    
    prep = DemandaForecastPrep(source=source)
    prep.run()

if __name__ == '__main__':
    main()
