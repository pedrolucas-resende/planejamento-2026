"""
Transforma input_o.csv em planning_mensal.csv
Filtro: janeiro de 2026 (hardcoded para validação)
Estrutura final: 1 linha por data, métricas somadas
"""
import pandas as pd

INPUT_FILE  = "data/csv/input_o.csv"
OUTPUT_FILE = "data/csv/planning_mensal.csv"

AGG_COLUMNS = [
    # 1 COLUNA
    # "qtd_produzidas",
    "qtd_internas",

    # "pronta_total",
    # "pronta_0km",
    # "pronta_semi",
    # "pronta_usada",

    # "venda_total",
    # "qtd_vendas_0km",
    # "qtd_vendas_semi",
    # "qtd_vendas_usada",

    # 2 COLUNA
    # "alugadas_0km",
    # "alugadas_semi",
    # "alugadas_usada",
    
    # "manutencao_total",
    # "manutencao_0km",
    # "manutencao_semi",
    # "manutencao_usada",
    # "mec_total",
    # "mec_presentes",
    # "mec_na_rampa",
    # "alugadas_total",
    # "frota_op_total",
    # "frota_op_0km",
    # "frota_op_semi",
    # "frota_op_usada",
]

# ----------------------------------------------------------------------------

print(f"📁 lendo: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
print(f"✅ {len(df)} linhas carregadas")

# checar colunas faltando
missing = [col for col in AGG_COLUMNS if col not in df.columns]
if missing:
    print(f"⚠️  colunas faltando no CSV: {missing}")
else:
    print("✅ todas as colunas encontradas")

# converter data
df["dataValor"] = pd.to_datetime(df["dataValor"], errors="coerce")

# filtrar janeiro 2026
df = df[(df["dataValor"].dt.month == 1) & (df["dataValor"].dt.year == 2026)]
print(f"🗓️  após filtro jan/2026: {len(df)} linhas")

# colunas que realmente existem (evitar erro se faltar alguma)
colunas_ok = [col for col in AGG_COLUMNS if col in df.columns]

# agregar: 1 linha por data
# df = df.groupby("dataValor", as_index=False)[colunas_ok].sum()
df = df.sort_values("qtd_internas", ascending=False)
# df = df.sort_values("dataValor")

# métricas derivadas (calculadas depois da agregação)
frota = df["frota_op_total"].replace(0, pd.NA)
# df["razao_utilizacao"]  = (df["alugadas_total"]   / frota).round(4)
# df["indice_manutencao"] = (df["manutencao_total"] / frota).round(4)
# df["indice_pronta"]     = (df["pronta_total"]     / frota).round(4)
df = df[["dataValor"] + colunas_ok]

# salvar
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
print(f"\n✅ salvo em: {OUTPUT_FILE}")
print(f"   {len(df)} linhas | {len(df.columns)} colunas")
print("\n📋 preview:")
print(df.to_string())
