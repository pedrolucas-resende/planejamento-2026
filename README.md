# Planejamento 2026 - S&OP Mottu

Sistema de planejamento e análise de demanda para previsão de frota da Mottu em 2025-2026.

## 📋 Estrutura do Repositório

```
planejamento-2026/
├── README.md                          # Este arquivo
├── LICENSE                            # Licença do projeto
├── requirements.txt                   # Dependências Python
│
├── data/                              # Dados e saídas
│   ├── csv/                           # Arquivos CSV processados
│   │   ├── venda_filial_mes.csv      # Demanda por filial e mês
│   │   ├── venda_total_mes.csv       # Demanda total por mês
│   │   └── vendas.csv                # Dados brutos de vendas
│   ├── images/                        # Gráficos e visualizações
│   │   └── (gráficos exportados do Excel)
│   └── xlsx/                          # Arquivos Excel
│       ├── overview_sales.xlsx        # Pivot tables e análises
│       └── ~$overview_sales.xlsx      # Arquivo temporário
│
├── queries/                           # Queries SQL
│   ├── demanda.sql                   # Query base de demanda
│   ├── venda_filial_mes.sql          # Demanda agregada por filial/mês
│   ├── venda_total_mes.sql           # Demanda total mensal
│   └── vendas.sql                    # Dados brutos de vendas
│
└── src/                               # Código Python
    ├── utils/
    │   ├── __pycache__/
    │   └── bigquery_client.py        # Cliente para BigQuery
    ├── venda_filial_mes.py           # Script: extrai demanda por filial
    ├── venda_total_mes.py            # Script: extrai demanda total
    ├── vendas.py                     # Script: extrai dados brutos
    └── export_charts.py              # Script: exporta gráficos do Excel
```

## 🚀 Começando

### Pré-requisitos

- Python 3.8+
- Google Cloud SDK instalado
- Acesso ao BigQuery da Mottu
- Excel (para visualizações)

### Setup Inicial

1. **Clone o repositório:**
```bash
git clone https://github.com/pedrolucas-resende/planejamento-2026.git
cd planejamento-2026
```

2. **Crie um ambiente virtual:**
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure autenticação com Google Cloud:**
```bash
gcloud auth application-default login
```

Este comando abrirá seu navegador para autenticar. Isso permite que os scripts Python acessem o BigQuery.

## 📊 Fluxo de Trabalho

### 1. Extrair Dados do BigQuery

```bash
# Extrair demanda total por mês
python src/venda_total_mes.py

# Extrair demanda por filial e mês
python src/venda_filial_mes.py

# Extrair dados brutos de vendas
python src/vendas.py
```

**Saída:** Arquivos CSV em `data/csv/`

### 2. Análise no Excel

1. Abra `data/xlsx/overview_sales.xlsx`
2. Crie Pivot Tables na aba "OVERVIEW" com:
   - Séries temporais de demanda
   - Breakdown por produto (0km, Semi, Usada)
   - Análises por filial, capital/interior, estado, população

3. Exporte os gráficos (veja próxima seção)

### 3. Exportar Gráficos

```bash
python src/export_charts.py
```

**Instruções manuais:**
1. Abra `data/xlsx/overview_sales.xlsx`
2. Vá para a aba "OVERVIEW"
3. Para cada gráfico:
   - Clique direito → "Copiar"
   - Abra um editor de imagem (Paint, Preview, etc)
   - Cole (Ctrl+V ou Cmd+V)
   - Salve em `data/images/` com nome descritivo

**Exemplos de nomes de imagens:**
- `demanda_filial_temporal.png`
- `demanda_produto_0km.png`
- `demanda_capital_interior.png`
- `demanda_estado_consolidado.png`

## 📈 Análises Solicitadas

Conforme levantamento com liderança:

### ✅ Montar Histórico de Demanda por Filial
- [ ] Separado em 3 produtos: 0km, Semi, Usada
- [ ] Agregado por mês
- [ ] Gráfico de série temporal

### ✅ Quebras de Demanda
- [ ] Por **População** (Megalópole, Metrópole, Capital Regional, etc)
- [ ] Por **Localização** (Interior vs Capital)
- [ ] Por **Estado**
- [ ] Tabelas consolidadas e gráficos

### ✅ Histórico de Disponibilidade
- [ ] Identificar o que significa "ter disponibilidade"
- [ ] Correlacionar demanda com disponibilidade de frota
- [ ] Agregar por mês
- [ ] Gráfico de série temporal

### ✅ Projeção com Média Móvel
- [ ] Calcular média móvel de 3 e 6 meses
- [ ] Projetar demanda para 2025-2026
- [ ] Gráfico com série histórica + projeção
- [ ] Identificar tendências (crescimento, estabilização, sazonalidade)

## 📁 Arquivo de Configuração

Exemplo de `requirements.txt`:
```
google-cloud-bigquery==3.14.0
pandas==2.0.3
openpyxl==3.1.2
pillow==10.0.0
python-dotenv==1.0.0
```

## 🔧 Scripts Disponíveis

| Script | Descrição | Saída |
|--------|-----------|-------|
| `src/vendas.py` | Extrai dados brutos de vendas | `data/csv/vendas.csv` |
| `src/venda_total_mes.py` | Demanda total agregada por mês | `data/csv/venda_total_mes.csv` |
| `src/venda_filial_mes.py` | Demanda por filial e mês | `data/csv/venda_filial_mes.csv` |
| `src/export_charts.py` | Exporta gráficos do Excel | `data/images/*.png` |

## 📊 Queries SQL

Todas as queries estão em `queries/`:

- **demanda.sql** - Query base com todas as dimensões disponíveis
- **venda_filial_mes.sql** - Agregação por filial e mês
- **venda_total_mes.sql** - Agregação total mensal
- **vendas.sql** - Dados brutos sem agregação

## 🎯 Próximos Passos

1. **Consolidar análises iniciais** ✓
   - [x] Setup do repositório
   - [ ] Executar scripts de extração
   - [ ] Montar Pivot Tables no Excel
   - [ ] Exportar gráficos

2. **Análise detalhada de demanda**
   - [ ] Entender padrão de demanda por filial
   - [ ] Identificar sazonalidade
   - [ ] Análise de capital vs interior
   - [ ] Breakdown por produto (0km, Semi, Usada)

3. **Disponibilidade e correlação**
   - [ ] Definir métrica de "disponibilidade"
   - [ ] Correlacionar com demanda
   - [ ] Identificar gaps

4. **Forecasting**
   - [ ] Implementar média móvel
   - [ ] Testar modelos (linear regression, Holt-Winters, ARIMA)
   - [ ] Projetar demanda 2025-2026
   - [ ] Documentar acurácia das previsões

5. **Documentação final**
   - [ ] Criar dashboard com principais KPIs
   - [ ] Documentar metodologia
   - [ ] Preparar apresentação para liderança

## 📝 Notas Técnicas

### Autenticação BigQuery

A autenticação usa Application Default Credentials (ADC) do Google Cloud:

```bash
gcloud auth application-default login
```

Isso salva credenciais em `~/.config/gcloud/application_default_credentials.json`

Os scripts buscam por essas credenciais automaticamente.

### Estrutura de Dados

Dimensões disponíveis:
- **Temporal:** Data, Mês, Trimestre, Ano
- **Geográfica:** Filial, Cidade, Estado, Região (Capital/Interior)
- **Produto:** 0km, Semi, Usada
- **Operacional:** Tipo de Operação (ASP vs Filial Mottu)

### Performance

Para datasets grandes, as queries usam:
- Agregações no BigQuery (antes de trazer para Python)
- Particionamento por data
- Índices em chaves de groupby

## 🤝 Contribuindo

Para adicionar novas análises:

1. Adicione a query em `queries/`
2. Crie um script em `src/` para executar
3. Atualize este README
4. Commit com mensagem descritiva

## 📞 Contato

**Responsável:** Pedro Lucas Resende  
**GitHub:** [@pedrolucas-resende](https://github.com/pedrolucas-resende)  
**Email:** [seu email]

## 📄 Licença

Este projeto está sob licença [confira LICENSE](LICENSE)

---

**Última atualização:** Março 2026  
**Status:** Em desenvolvimento 🚀
