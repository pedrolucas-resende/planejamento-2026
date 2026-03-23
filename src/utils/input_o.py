import pandas as pd
from bigquery_client import get_client


# 📁 Paths
QUERY_PATH = "queries/input_o.sql"
OUTPUT_PATH = "data/csv/input_o.csv"


# 🔹 Executa SQL
def run_query(client, query_path):
    with open(query_path, "r") as file:
        query = file.read()

    df = client.query(query).to_dataframe()
    return df

# 🔹 MAIN
def main():
    client = get_client()

    print("🔄 Rodando query...")
    df = run_query(client, QUERY_PATH)

    print("💾 Salvando CSV...")
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    
    print(f"✅ Salvo em: {OUTPUT_PATH}")
    print(f"   Registros: {len(df):,}")
    print(f"   Colunas: {list(df.columns)}")
    print(f"   Exemplo:\n{df.head(3)}")

if __name__ == "__main__":
    main()
