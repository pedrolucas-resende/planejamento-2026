import pandas as pd
from datetime import timedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from utils.bigquery_client import get_client


# 📁 Paths
QUERY_PATH = "queries/venda_filial_mes.sql"
OUTPUT_PATH = "data/csv/venda_filial_mes.csv"


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

    print("💾 Salvando CSV original...")
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
