"""
Script para transformar input_o.csv em formato agregado:
Data, País, População, Produto, Vendas

Estrutura final:
- data: Data do registro
- pais: País da operação
- populacao: População agregada por país
- produto: Tipo de moto (0km, semi, usada, total)
- vendas: Quantidade total de motos vendidas
"""

import pandas as pd
from pathlib import Path

# ============================================================================
# 1. CONFIGURAÇÃO
# ============================================================================

INPUT_FILE = "data/csv/input_o.csv"
OUTPUT_FILE = "data/csv/pais_populacao_produto_vendas.csv"

# Colunas de vendas por tipo de veículo
VENDAS_COLUNAS = {
    "alugadas_0km": "0km",
    "alugadas_semi": "semi",
    "alugadas_usada": "usada",
    "alugadas_total": "total"
}

# ============================================================================
# 2. CARREGAMENTO E LIMPEZA
# ============================================================================

def load_and_clean(filepath):
    """Carrega e limpa o arquivo input_o.csv"""
    print(f"📁 Lendo arquivo: {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8-sig')  # Remove BOM se houver
    
    print(f"✅ Arquivo carregado: {len(df)} linhas, {len(df.columns)} colunas")
    
    return df

# ============================================================================
# 3. TRANSFORMAÇÃO PARA FORMATO AGREGADO
# ============================================================================

def transform_to_aggregated_format(df):
    """
    Transforma e agrega dados em nível País, População por Data e Produto:
    
    RESULTADO:
    | data       | pais   | populacao  | produto | vendas |
    | 2024-01-31 | Brasil | 215313498  | 0km     | 8000   |
    | 2024-01-31 | Brasil | 215313498  | semi    | 2500   |
    | 2024-01-31 | Brasil | 215313498  | usada   | 15000  |
    | 2024-01-31 | Brasil | 215313498  | total   | 25500  |
    | 2024-01-31 | México | 128932753  | 0km     | 2000   |
    ...
    """
    
    print("\n🔄 Agregando vendas por País e População...")
    
    # Selecionar apenas as colunas necessárias
    colunas_selecionadas = ['dataValor', 'pais', 'populacao'] + list(VENDAS_COLUNAS.keys())
    df_vendas = df[colunas_selecionadas].copy()
    
    # Converter dataValor para datetime
    df_vendas['dataValor'] = pd.to_datetime(df_vendas['dataValor'])
    
    # Converter população para número
    df_vendas['populacao'] = pd.to_numeric(df_vendas['populacao'], errors='coerce')
    
    # Agrupar por data, país e população, somar vendas
    df_agrupado = df_vendas.groupby(['dataValor', 'pais', 'populacao'])[list(VENDAS_COLUNAS.keys())].sum().reset_index()
    
    # Transformar para formato longo
    df_long = df_agrupado.melt(
        id_vars=['dataValor', 'pais', 'populacao'],
        value_vars=list(VENDAS_COLUNAS.keys()),
        var_name='tipo_original',
        value_name='vendas'
    )
    
    # Renomear colunas
    df_long['produto'] = df_long['tipo_original'].map(VENDAS_COLUNAS)
    df_long = df_long.rename(columns={'dataValor': 'data'})
    df_long = df_long.drop('tipo_original', axis=1)
    
    # Reordenar colunas
    df_long = df_long[['data', 'pais', 'populacao', 'produto', 'vendas']]
    
    # Converter vendas para inteiro e população para inteiro
    df_long['vendas'] = pd.to_numeric(df_long['vendas'], errors='coerce').fillna(0).astype(int)
    df_long['populacao'] = df_long['populacao'].fillna(0).astype(int)
    
    # Ordenar por data, país
    df_long = df_long.sort_values(['data', 'pais']).reset_index(drop=True)
    
    print(f"✅ Agregação concluída: {len(df_long)} registros")
    
    return df_long

# ============================================================================
# 4. ESTATÍSTICAS E VALIDAÇÃO
# ============================================================================

def print_statistics(df_agregado):
    """Exibe estatísticas do dataset agregado"""
    
    print("\n" + "="*70)
    print("📊 ESTATÍSTICAS DO DATASET (POR PAÍS E POPULAÇÃO)")
    print("="*70)
    
    print(f"\n✓ Total de registros: {len(df_agregado)}")
    print(f"✓ Período: {df_agregado['data'].min().date()} até {df_agregado['data'].max().date()}")
    print(f"✓ Datas únicas: {df_agregado['data'].nunique()}")
    print(f"✓ Países: {list(df_agregado['pais'].unique())}")
    print(f"✓ Produtos: {list(df_agregado['produto'].unique())}")
    
    print(f"\n✓ População por País:")
    pop_por_pais = df_agregado[['pais', 'populacao']].drop_duplicates().sort_values('pais')
    for _, row in pop_por_pais.iterrows():
        print(f"   - {row['pais']:15}: {row['populacao']:>15,}")
    
    print(f"\n✓ Vendas por País (total no período):")
    vendas_por_pais = df_agregado[df_agregado['produto'] != 'total'].groupby('pais')['vendas'].sum().sort_values(ascending=False)
    for pais, valor in vendas_por_pais.items():
        print(f"   - {pais:15}: {valor:>15,}")
    
    print(f"\n✓ Vendas por Produto (total no período):")
    vendas_por_produto = df_agregado[df_agregado['produto'] != 'total'].groupby('produto')['vendas'].sum().sort_values(ascending=False)
    for produto, valor in vendas_por_produto.items():
        print(f"   - {produto:10}: {valor:>15,}")
    
    print(f"\n✓ Total de vendas (período inteiro):")
    total_sem_duplicacao = df_agregado[df_agregado['produto'] != 'total']['vendas'].sum()
    print(f"   {total_sem_duplicacao:>15,}")
    
    # Vendas per capita
    print(f"\n✓ Vendas per capita (período inteiro):")
    for pais in df_agregado['pais'].unique():
        vendas_pais = df_agregado[(df_agregado['pais'] == pais) & (df_agregado['produto'] != 'total')]['vendas'].sum()
        pop_pais = df_agregado[df_agregado['pais'] == pais]['populacao'].iloc[0]
        per_capita = vendas_pais / pop_pais if pop_pais > 0 else 0
        print(f"   - {pais:15}: {per_capita:>15.6f} vendas/habitante")

# ============================================================================
# 5. EXPORTAÇÃO
# ============================================================================

def export_csv(df_agregado, output_filepath):
    """Exporta dataset agregado para CSV"""
    
    print(f"\n💾 Exportando para: {output_filepath}")
    df_agregado.to_csv(output_filepath, index=False, encoding='utf-8')
    print(f"✅ Arquivo exportado com sucesso!")
    print(f"   Colunas: {', '.join(df_agregado.columns)}")
    print(f"\n   Primeiras linhas:")
    print(df_agregado.head(15).to_string(index=False))

# ============================================================================
# 6. EXECUÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal"""
    
    print("\n" + "="*70)
    print("🚀 TRANSFORMAÇÃO: input_o → pais_populacao_produto_vendas")
    print("="*70)
    
    # Carregar dados
    df = load_and_clean(INPUT_FILE)
    
    # Transformar para formato agregado
    df_agregado = transform_to_aggregated_format(df)
    
    # Exibir estatísticas
    print_statistics(df_agregado)
    
    # Exportar resultado
    export_csv(df_agregado, OUTPUT_FILE)
    
    print("\n" + "="*70)
    print("✨ Processo concluído com sucesso!")
    print("="*70)
    
    return df_agregado

# ============================================================================

if __name__ == "__main__":
    # Executar transformação
    df_resultado = main()
