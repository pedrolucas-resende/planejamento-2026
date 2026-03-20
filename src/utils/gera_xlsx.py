import pandas as pd
import glob
import os

def gerar_relatorio_final(input_path='data/csv/*.csv', output_file='data/xlsx/relatorio_final.xlsx'):
    # Garante que o diretório de saída existe
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Busca todos os arquivos .csv na pasta data
    csv_files = glob.glob(input_path)
    
    if not csv_files:
        print("⚠️ Nenhum arquivo CSV encontrado para consolidar.")
        return

    # Usa o XlsxWriter como engine para permitir formatações extras se necessário
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for file in csv_files:
            # Define o nome da aba como o nome do arquivo (sem extensão)
            sheet_name = os.path.basename(file).replace('.csv', '')[:31] # Limite de 31 caracteres do Excel
            
            print(f"Reading: {file} -> Sheet: {sheet_name}")
            df = pd.read_csv(file)
            
            # Converte para Excel
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Estética: Ajusta a largura das colunas automaticamente
            worksheet = writer.sheets[sheet_name]
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)

    print(f"✅ Arquivo consolidado com sucesso: {output_file}")

if __name__ == "__main__":
    gerar_relatorio_final()
