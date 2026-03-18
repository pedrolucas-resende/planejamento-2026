# bigquery_client.py
import warnings
warnings.filterwarnings('ignore')

from google.cloud import bigquery

PROJETO = "dm-mottu-aluguel"

def get_client(project: str = PROJETO):
    return bigquery.Client(project=PROJETO)

def rodar_query(query: str, project: str = PROJETO):
    cliente = get_client(project)
    return cliente.query(query).to_dataframe()

def estimar_query(query: str, project: str = PROJETO):
    cliente = get_client(project)
    job_config = bigquery.QueryJobConfig(dry_run=True)
    job = cliente.query(query, job_config=job_config)
    gb = job.total_bytes_processed / 1e9
    print(f"⚠️ Estimativa: {gb:.2f} GB processados")

def listar_schemas(project: str = PROJETO):
    query = f"""
    SELECT
      table_schema,
      table_name,
      column_name,
      data_type
    FROM
      `{project}.region-us.INFORMATION_SCHEMA.COLUMNS`
    ORDER BY
      table_schema,
      table_name,
      ordinal_position
    """
    return rodar_query(query)
