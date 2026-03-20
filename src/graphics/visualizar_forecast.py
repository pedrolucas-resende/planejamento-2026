import pandas as pd
import altair as alt

def gerar_dashboard_forecast(path_historico, path_forecast):
    # 1. Carga dos dados
    df_hist = pd.read_csv(path_historico)
    df_fore = pd.read_csv(path_forecast)

    ano_passado = pd.Timestamp.now().year - 1
    
    # 2. Padronização para o Formato "Longo" (Tidy Data)
    df_hist['data'] = pd.to_datetime(df_hist['data'])
    df_hist = df_hist[df_hist['data'] >= f'{ano_passado}-01-01']
    df_hist = df_hist[['data', 'filial', 'produto', 'vendas']].rename(columns={'vendas': 'valor'})
    df_hist['cenario'] = 'Realizado'

    df_fore['mes_referencia'] = pd.to_datetime(df_fore['mes_referencia'])
    df_fore = df_fore[['mes_referencia', 'filial', 'produto', 'venda_estimada']].rename(
        columns={'mes_referencia': 'data', 'venda_estimada': 'valor'}
    )
    df_fore['cenario'] = 'Forecast'

    # Unificar bases
    df_final = pd.concat([df_hist, df_fore], ignore_index=True)

    # 3. Interatividade: Dropdown para selecionar a Filial
    filiais = sorted(df_final['filial'].unique().tolist())
    select_filial = alt.binding_select(options=filiais, name='Filial: ')
    selection = alt.selection_point(fields=['filial'], bind=select_filial, value=filiais[0])

    # 4. Construção do Gráfico Corrigido
    line = alt.Chart(df_final).mark_line(point=True).encode(
        x=alt.X('data:T', title='Mês'),
        y=alt.Y('valor:Q', title='Qtd Motos'),
        color=alt.Color('produto:N', title='Produto'),
        # Forçamos o 'Realizado' a ser linha contínua [] e 'Forecast' a ser tracejada [5, 5]
        strokeDash=alt.StrokeDash('cenario:N', 
            title='Cenário',
            scale=alt.Scale(domain=['Realizado', 'Forecast'], range=[[], [5, 5]]),
            legend=alt.Legend(symbolType='stroke', symbolStrokeWidth=2) # Garante linha na legenda
        ),
        tooltip=[
            alt.Tooltip('data:T', format='%b %Y', title='Data'),
            alt.Tooltip('filial:N', title='Filial'),
            alt.Tooltip('produto:N', title='Produto'),
            alt.Tooltip('valor:Q', format='.2f', title='Valor'),
            alt.Tooltip('cenario:N', title='Tipo')
        ]
    ).add_params(
        selection
    ).transform_filter(
        selection
    ).properties(
        width=800,
        height=500,
        title='S&OP Mottu: Realizado vs Forecast 12 Meses'
    ).configure_legend(
        symbolType='stroke' # Reforça que a legenda use o estilo da linha
    ).interactive()

    # Salvar como HTML para abrir no navegador
    output_path = 'dashboard_forecast_mottu.html'
    line.save(output_path)
    print(f"✨ Gráfico gerado com sucesso: {output_path}")

if __name__ == "__main__":
    gerar_dashboard_forecast(
        'data/csv/filial_produto_vendas_historico.csv', 
        'data/csv/forecast_12_meses_mottu.csv'
    )
