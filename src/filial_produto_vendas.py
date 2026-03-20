"""
Script para transformar input_o.csv em formato:
(País, Filial), Produto, Vendas

Estrutura final:
- pais: País da filial
- filial: Nome da filial
- produto: Tipo de moto (0km, semi, usada, total)
- vendas: Quantidade de motos vendidas
"""

import pandas as pd
from pathlib import Path

# ============================================================================
# 1. CONFIGURAÇÃO
# ============================================================================

INPUT_FILE = "data/csv/input_o.csv"
OUTPUT_FILE = "data/csv/filial_produto_vendas.csv"

# Colunas de demanda por tipo de veículo
DEMANDA_COLUNAS = {
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
    print(f"   Colunas disponíveis: {list(df.columns[:10])}...")
    
    return df

# ============================================================================
# 3. TRANSFORMAÇÃO PARA FORMATO LONGO (UNPIVOT)
# ============================================================================

def transform_to_long_format(df):
    """
    Transforma de formato WIDE para LONG:
    
    ANTES (wide):
    | dataValor | pais | filial | alugadas_0km | alugadas_semi | alugadas_usada | alugadas_total |
    
    DEPOIS (long):
    | data | pais | filial | produto | vendas |
    | 2024-01-31 | Brasil | Mottu SP | 0km | 100 |
    | 2024-01-31 | Brasil | Mottu SP | semi | 50 |
    | 2024-01-31 | Brasil | Mottu SP | usada | 200 |
    | 2024-01-31 | Brasil | Mottu SP | total | 350 |
    """
    
    print("\n🔄 Transformando para formato longo...")
    
    # Selecionar apenas as colunas necessárias
    colunas_selecionadas = ['dataValor', 'pais', 'filial'] + list(DEMANDA_COLUNAS.keys())
    df_selecionado = df[colunas_selecionadas].copy()
    
    # Converter dataValor para datetime
    df_selecionado['dataValor'] = pd.to_datetime(df_selecionado['dataValor'])
    
    # Unpivot (melt): transformar colunas em linhas
    df_long = df_selecionado.melt(
        id_vars=['dataValor', 'pais', 'filial'],
        value_vars=list(DEMANDA_COLUNAS.keys()),
        var_name='tipo_original',
        value_name='vendas'
    )
    
    # Renomear tipo de veículo
    df_long['produto'] = df_long['tipo_original'].map(DEMANDA_COLUNAS)
    df_long = df_long.drop('tipo_original', axis=1)
    
    # Renomear coluna de data
    df_long = df_long.rename(columns={'dataValor': 'data'})
    
    # Reordenar colunas
    df_long = df_long[['data', 'pais', 'filial', 'produto', 'vendas']]
    
    # Converter vendas para número (remover NaN)
    df_long['vendas'] = pd.to_numeric(df_long['vendas'], errors='coerce').fillna(0)
    
    # Ordenar por data
    df_long = df_long.sort_values('data').reset_index(drop=True)
    
    print(f"✅ Transformação concluída: {len(df_long)} registros")
    
    return df_long

# ============================================================================
# 4. ESTATÍSTICAS E VALIDAÇÃO
# ============================================================================

def print_statistics(df_long):
    """Exibe estatísticas do dataset transformado"""
    
    print("\n" + "="*70)
    print("📊 ESTATÍSTICAS DO DATASET")
    print("="*70)
    
    print(f"\n✓ Total de registros: {len(df_long)}")
    print(f"✓ Período: {df_long['data'].min().date()} até {df_long['data'].max().date()}")
    print(f"✓ Datas únicas: {df_long['data'].nunique()}")
    print(f"✓ Países únicos: {df_long['pais'].nunique()} → {list(df_long['pais'].unique())}")
    print(f"✓ Filiais únicas: {df_long['filial'].nunique()}")
    print(f"✓ Produtos: {list(df_long['produto'].unique())}")
    
    print(f"\n✓ Total de motos vendidas por produto:")
    vendas_por_produto = df_long.groupby('produto')['vendas'].sum().sort_values(ascending=False)
    for produto, valor in vendas_por_produto.items():
        print(f"   - {produto}: {valor:,.0f}")
    
    print(f"\n✓ Top 10 filiais por total de vendas:")
    top_filiais = df_long.groupby(['pais', 'filial'])['vendas'].sum().sort_values(ascending=False).head(10)
    for (pais, filial), vendas in top_filiais.items():
        print(f"   {pais:10} | {filial:40} | {vendas:>10,.0f}")
    
    print(f"\n✓ Vendas por país:")
    vendas_por_pais = df_long.groupby('pais')['vendas'].sum().sort_values(ascending=False)
    for pais, vendas in vendas_por_pais.items():
        print(f"   {pais:15}: {vendas:>12,.0f}")

# ============================================================================
# 5. EXPORTAÇÃO
# ============================================================================

def export_csv(df_long, output_filepath):
    """Exporta dataset transformado para CSV"""
    
    print(f"\n💾 Exportando para: {output_filepath}")
    df_long.to_csv(output_filepath, index=False, encoding='utf-8')
    print(f"✅ Arquivo exportado com sucesso!")
    print(f"   Colunas: {', '.join(df_long.columns)}")
    print(f"   Primeiras 10 linhas:")
    print(df_long.head(10).to_string(index=False))

# ============================================================================
# 6. EXECUÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal"""
    
    print("\n" + "="*70)
    print("🚀 TRANSFORMAÇÃO: input_o → filial_produto_demanda")
    print("="*70)
    
    # Carregar dados
    df = load_and_clean(INPUT_FILE)
    
    # Transformar para formato longo
    df_long = transform_to_long_format(df)
    
    # Exibir estatísticas
    print_statistics(df_long)
    
    # Exportar resultado
    export_csv(df_long, OUTPUT_FILE)
    
    print("\n" + "="*70)
    print("✨ Processo concluído com sucesso!")
    print("="*70)
    
    return df_long

# ============================================================================
# EXEMPLOS DE USO ADICIONAL (comentado)
# ============================================================================

def exemplos_uso(df_long):
    """
    Exemplos de análises que você pode fazer com o dataset transformado
    """
    
    # 1. Vendas por filial e produto
    print("\n📊 Vendas por Filial e Produto:")
    pivot = df_long.pivot_table(
        index='filial', 
        columns='produto', 
        values='vendas', 
        aggfunc='sum'
    )
    print(pivot.head(10))
    
    # 2. Filtrar apenas motos usadas
    print("\n🏍️ Apenas motos USADAS:")
    motos_usadas = df_long[df_long['produto'] == 'usada'].copy()
    print(f"Total de motos usadas vendidas: {motos_usadas['vendas'].sum():,.0f}")
    
    # 3. Agrupar por país e produto
    print("\n🌎 Vendas por País e Produto:")
    pais_produto = df_long.groupby(['pais', 'produto'])['vendas'].sum().unstack(fill_value=0)
    print(pais_produto)

# ============================================================================

if __name__ == "__main__":
    # Executar transformação
    df_resultado = main()
    
    # Descomente a linha abaixo para ver exemplos adicionais
    # exemplos_uso(df_resultado)
