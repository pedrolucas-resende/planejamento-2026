"""
Script para gerar planilha de demanda formatada manualmente
Estrutura:
  Filial
    0km      | Fev/2025 | Mar/2025 | ...
    Semi     | Fev/2025 | Mar/2025 | ...
    Usada    | Fev/2025 | Mar/2025 | ...
    Total    | Fev/2025 | Mar/2025 | ...
  Filial 2
    ...
"""

import pandas as pd
from pathlib import Path
import logging
from utils.bigquery_client import rodar_query

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DemandaFormatada:
    """Gera planilha formatada de demanda por filial, produto e período"""
    
    def __init__(self):
        self.df_raw = None
        self.output_path = 'data/csv/demanda_formatada.csv'
        
    def load_data(self):
        """Carregar dados do BigQuery"""
        
        logger.info("Carregando dados do BigQuery...")
        
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
        AND terceiro = 0
        ORDER BY dataValor DESC, filial
        """
        
        self.df_raw = rodar_query(query, project="dm-mottu-aluguel")
        
        logger.info(f"✓ Carregados {len(self.df_raw):,} registros")
        return True
    
    def prepare_data(self):
        """Preparar dados para formatação"""
        
        logger.info("Preparando dados...")
        
        # Converter data
        self.df_raw['dataValor'] = pd.to_datetime(self.df_raw['dataValor'])
        
        # Extrair período (YYYY-MM)
        self.df_raw['periodo'] = self.df_raw['dataValor'].dt.strftime('%Y-%m')
        
        # Preencher NaN com 0
        self.df_raw[['alugadas_0km', 'alugadas_semi', 'alugadas_usada', 'alugadas_total']] = \
            self.df_raw[['alugadas_0km', 'alugadas_semi', 'alugadas_usada', 'alugadas_total']].fillna(0).astype(int)
        
        logger.info("✓ Dados preparados")
        return True
    
    def format_planilha(self):
        """Criar estrutura formatada da planilha"""
        
        logger.info("Formatando planilha...")
        
        # Agrupar por filial e período
        df_grouped = self.df_raw.groupby(['filial', 'periodo'])[
            ['alugadas_0km', 'alugadas_semi', 'alugadas_usada', 'alugadas_total']
        ].sum().reset_index()
        
        # Pivotar para ter períodos em colunas
        df_pivoted = df_grouped.pivot_table(
            index='filial',
            columns='periodo',
            values=['alugadas_0km', 'alugadas_semi', 'alugadas_usada', 'alugadas_total'],
            aggfunc='sum'
        )
        
        # Estrutura final: lista de linhas para escrever no CSV
        rows = []
        
        # Pegar lista única de filiais e períodos (sorted)
        filiais = sorted(df_grouped['filial'].unique())
        periodos = sorted(df_grouped['periodo'].unique())
        
        logger.info(f"  Filiais: {len(filiais)}")
        logger.info(f"  Períodos: {len(periodos)}")
        
        # Montar estrutura
        for filial in filiais:
            # Linha da filial
            rows.append([filial] + [''] * len(periodos))
            
            # Produtos
            produtos = ['0km', 'Semi', 'Usada', 'Total']
            
            for produto in produtos:
                # Mapear nome interno para nome da coluna
                col_map = {
                    '0km': 'alugadas_0km',
                    'Semi': 'alugadas_semi',
                    'Usada': 'alugadas_usada',
                    'Total': 'alugadas_total'
                }
                
                col_name = col_map[produto]
                
                # Linha do produto
                linha = [produto]
                
                for periodo in periodos:
                    # Pegar valor
                    mask = (df_grouped['filial'] == filial) & (df_grouped['periodo'] == periodo)
                    valor = df_grouped[mask][col_name].values
                    
                    if len(valor) > 0:
                        linha.append(int(valor[0]))
                    else:
                        linha.append(0)
                
                rows.append(linha)
            
            # Linha em branco entre filiais
            rows.append([''] * (len(periodos) + 1))
        
        # Criar DataFrame
        columns = [''] + periodos
        df_final = pd.DataFrame(rows, columns=columns)
        
        logger.info(f"✓ Planilha formatada com {len(rows)} linhas")
        
        return df_final, periodos
    
    def save_csv(self, df_final, periodos):
        """Salvar como CSV (mais rápido que XLSX)"""
        
        Path('data/csv').mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Salvando em: {self.output_path}")
        
        # Salvar como CSV
        df_final.to_csv(self.output_path, index=False, encoding='utf-8')
        
        logger.info(f"✓ CSV salvo")
        logger.info(f"✅ Salvo em: {self.output_path}")
        return self.output_path
    
    def run(self):
        """Executar pipeline completo"""
        
        print("\n" + "="*70)
        print("🚀 Gerando Planilha Formatada de Demanda")
        print("="*70 + "\n")
        
        if not self.load_data():
            logger.error("Falha ao carregar dados")
            return False
        
        if not self.prepare_data():
            logger.error("Falha ao preparar dados")
            return False
        
        df_final, periodos = self.format_planilha()
        self.save_csv(df_final, periodos)
        
        print("\n" + "="*70)
        print("✅ Planilha criada com sucesso!")
        print("="*70)
        print(f"\nAbra em Excel:")
        print(f"  open {self.output_path}\n")
        
        return True

def main():
    prep = DemandaFormatada()
    prep.run()

if __name__ == '__main__':
    main()
