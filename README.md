# Forecast de Vendas S&OP (Motos 0km, Semi e Usadas)

Este repositório contém as ferramentas e scripts para a projeção de vendas de 12 meses da frota (0km, seminovas e usadas) da Mottu. O projeto integra dados do **BigQuery** e processamento em **Python** para alimentar o planejamento de demanda.

## 1. Objetivo do Projeto

Automatizar e padronizar a projeção de vendas anual por categoria de veículo, fornecendo subsídios para o planejamento estratégico de Sales and Operations Planning (S&OP).

---

## 2. Configuração do Ambiente

### Requisitos Técnicos

- **Python:** 3.12 (Versão recomendada para estabilidade das libs de Data Science)
- **Google Cloud SDK (gcloud):** Instalado e configurado.
- **Projeto BigQuery:** `dm-mottu-aluguel`

### Instalação e Autenticação

Siga os passos abaixo para preparar o ambiente local no macOS:

```bash
# 1. Criar o ambiente virtual
python3.12 -m venv .venv

# 2. Ativar o ambiente
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Autenticação Google Cloud (Obrigatório para acesso aos dados)
# Isso configura as Application Default Credentials (ADC)
gcloud auth application-default login
```

---

## 3. Estrutura do Repositório

```
├── src/
│   ├── forecast_ago_2025_fev_2026.py    # Script de projeção principal
│   ├── input_o.py                        # Processamento de entradas específicas
│   └── utils/                            # Utilitários de conexão (Client do BigQuery)
├── queries/                              # Arquivos .sql com regras de negócio
├── data/xlsx/                            # Armazena overview_sales.xlsx
├── zzz/                                  # Arquivos legados (scripts antigos)
└── README.md                             # Este arquivo
```

### Detalhamento

- **`src/`:** Scripts de extração e modelagem de forecast.
  - `forecast_ago_2025_fev_2026.py` – Script de projeção principal.
  - `input_o.py` – Processamento de entradas específicas.
  - `utils/` – Utilitários de conexão (Client do BigQuery).

- **`queries/`:** Arquivos `.sql` com as regras de negócio para extração no BigQuery.

- **`data/xlsx/`:** Armazena o arquivo `overview_sales.xlsx`, repositório final dos dados.

- **`zzz/`:** Pasta de arquivos legados (scripts antigos e consultas descontinuadas).

---

## 4. Fluxo de Trabalho

1. **Extração:** O script consome dados do projeto `dm-mottu-aluguel` via BigQuery utilizando as queries em `/queries`.

2. **Processamento:** Os arquivos em `src/` processam os dados brutos e realizam o cálculo de forecast.

3. **Consolidação:** Atualmente, os resultados são gerados em arquivos intermediários e consolidados manualmente no `overview_sales.xlsx` (etapa em processo de automação).

---

## 5. Notas de Manutenção

- Sempre que houver alteração nas queries SQL, verifique a compatibilidade com os scripts Python.
- Mantenha o arquivo `requirements.txt` atualizado com as dependências do projeto.
- Consulte o arquivo `.gitignore` para garantir que credenciais e arquivos sensíveis não sejam commitados.

---

## 6. Próximos Passos

- [ ] Automatizar consolidação dos dados no `overview_sales.xlsx`
- [ ] Documentar métricas de erro e validação de dados

---

**Versão:** 1.0  
**Última atualização:** Março/2026
