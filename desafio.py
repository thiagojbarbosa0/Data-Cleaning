import pandas as pd

df = pd.read_csv("Database.csv")

#Remover espaços
df.columns = df.columns.str.strip()

for col in df.select_dtypes(include=['object', 'str']):
    df[col] = df[col].str.strip()

#Remover linhas vazias e duplicadas
df = df.dropna(how="all").drop_duplicates()

#Linhas da coluna cpf que estão vazias viram Não Informado
df.loc[df["CPF_Cliente"].isna(), "CPF_Cliente"] = "Não informado"

#Tirar tudo que não é número dos CPF's válidos
df["CPF_Cliente"] = df["CPF_Cliente"].astype(str).str.replace(r"\D", "", regex=True)
df.loc[df["CPF_Cliente"] == "", "CPF_Cliente"] = "Não informado"

#Colocar CPF's padronizados
filtro = (df["CPF_Cliente"] != "Não informado") & (df["CPF_Cliente"].str.len() == 11)

df.loc[filtro, "CPF_Cliente"] = df.loc[filtro, "CPF_Cliente"].astype(str).str.replace(
     r"(\d{3})(\d{3})(\d{3})(\d{2})", 
     r"\1.\2.\3-\4", 
     regex=True
)

#Corrigir data e corrigir ambiguidades com base na moeda fiduciária usada
filtro_moeda = df["Moeda"].eq("USD")
df["Data_Transacao"] = df["Data_Transacao"].astype(object)
df["Data_Transacao"] = df["Data_Transacao"].str.replace('.', '-', regex=False)

df.loc[filtro_moeda, "Data_Transacao"] = pd.to_datetime(
    df.loc[filtro_moeda, "Data_Transacao"],
    errors="coerce",
    dayfirst=False
)

df.loc[~filtro_moeda, "Data_Transacao"] = pd.to_datetime(
    df.loc[~filtro_moeda, "Data_Transacao"],
    errors="coerce",
    format='mixed', 
    dayfirst=True 
)

# Padronizar data
df["Data_Transacao"] = pd.to_datetime(df["Data_Transacao"], errors='coerce')
df["Data_Transacao"] = df["Data_Transacao"].dt.strftime('%Y-%m-%d')


#Manter só números, vírgula, ponto e "-"
df["Valor_Transacao"] = df["Valor_Transacao"].astype(str).str.replace(r"[^\d,.\-]", "", regex=True)

#Remove os pontos de milhar
df["Valor_Transacao"] = df["Valor_Transacao"].str.replace(".", "", regex=False)

# Padronizar com ponto (padrão internacional e entendível em python)
df["Valor_Transacao"] = (
    df["Valor_Transacao"]
    .str.replace(",", ".", regex=False)
    .astype(float)
)

# Converter pra BRL conforme moeda da coluna A
cambio = {
    "USD": 5.0,
    "EUR": 5.5,
    "GBP" : 6.3,
    "BRL": 1.0
}

df["Valor_Transacao"] = df["Valor_Transacao"] * df["Moeda"].map(cambio)

df["Moeda"] = "BRL"

#Remover outliers e substituir eles pela mediana
Q1 = df["Valor_Transacao"].quantile(0.25)
Q3 = df["Valor_Transacao"].quantile(0.75)
IQR = Q3 - Q1

limite_inferior = Q1 - 1.5 * IQR
limite_superior = Q3 + 1.5 * IQR

df["Valor_Transacao"] = df["Valor_Transacao"].where(
    (df["Valor_Transacao"] >= limite_inferior) & (df["Valor_Transacao"] <= limite_superior),
    None
)
df.loc[df["Valor_Transacao"].isna(), "Valor_Transacao"] = df["Valor_Transacao"].quantile(0.50)

#Ajeitar o tipo de Transação
df["Tipo_Transacao"] = df["Tipo_Transacao"].str.lower()
df.loc[df["Tipo_Transacao"].str.contains(r"p.*i.*x", na=False), "Tipo_Transacao"] = "PIX"
df.loc[df["Tipo_Transacao"].str.contains(r"ted|doc|transf", na=False), "Tipo_Transacao"] = "Transferência"
df.loc[df["Tipo_Transacao"].str.contains(r"pgto|pag|boleto", na=False), "Tipo_Transacao"] = "Pagamento"
df.loc[df["Tipo_Transacao"].str.contains(r"dep", na=False), "Tipo_Transacao"] = "Depósito"
df.loc[df["Tipo_Transacao"].str.contains(r"resgate|retirada|saque", na=False), "Tipo_Transacao"] = "Saque"

# Preencher nulos com a moda
df.loc[df["Tipo_Transacao"].isna(), "Tipo_Transacao"] = df["Tipo_Transacao"].mode()[0]

#Ajeitar situação
df["Status_Transacao"] = df["Status_Transacao"].str.lower()
df.loc[df["Status_Transacao"].str.contains(r"aprov|autorizada", na=False), "Status_Transacao"] = "Aprovada"
df.loc[df["Status_Transacao"].str.contains(r"recus|bloq|negada", na=False), "Status_Transacao"] = "Recusada"
df.loc[df["Status_Transacao"].str.contains(r"pend|em processamento|aguardando", na=False), "Status_Transacao"] = "Pendente"

#Limpar os nomes duplicados
df["Nome_Cliente"] = (
    df["Nome_Cliente"]
    .str.strip()
    .str.replace("_", " ") 
    .str.replace(r"[^A-Za-zÀ-ÿ\s]", " ", regex=True)                            
    .str.replace(r"\s+", " ", regex=True)     
    .str.title()                             
    .apply(lambda x: " ".join(dict.fromkeys(str(x).split())))
)

#Organizar número de parcelas
df["Num_Parcelas"] = df["Num_Parcelas"].astype(str).str.extract(r'(\d+)').fillna(1).astype(int)

# Organizar taxas
df["Taxa_Servico"] = pd.to_numeric(df["Taxa_Servico"], errors="coerce").abs()
media = df["Taxa_Servico"].mean()
df["Taxa_Servico"] = df["Taxa_Servico"].fillna(media)
df["Taxa_Servico"] = df["Taxa_Servico"].astype(int)

#Corrigir Valor Final
df.loc[(df["Valor_Final"] < df["Valor_Transacao"]) | (df["Valor_Final"].isna()), "Valor_Final"] = df["Valor_Transacao"] + df["Taxa_Servico"]

#Salvar
df.to_csv("Database.csv", index=False)

# Ajuste na data
datas_temp = pd.to_datetime(df["Data_Transacao"])

# Resumo com ajuste no print para remover os nomes das colunas
resumo = f"""
VISÃO GERAL
- Total de registros: {len(df)}
- Período: {datas_temp.min().strftime('%Y-%m-%d')} até {datas_temp.max().strftime('%Y-%m-%d')}

VALORES
- Soma total movimentada: R$ {df["Valor_Transacao"].sum():,.2f}
- Ticket médio: R$ {df["Valor_Transacao"].mean():,.2f}
- Maior valor: R$ {df["Valor_Transacao"].max():,.2f}

STATUS
{df["Status_Transacao"].value_counts().to_string(header=False)}

TIPOS DE TRANSAÇÃO
{df["Tipo_Transacao"].value_counts().to_string(header=False)}

CATEGORIAS
{df["Categoria"].value_counts().to_string(header=False) if "Categoria" in df.columns else "Coluna 'Categoria' não encontrada"}

TOP CLIENTES
{df.groupby("Nome_Cliente")["Valor_Transacao"].sum().sort_values(ascending=False).head(5).to_string(header=False)}

BANCOS MAIS USADOS
{df["Banco"].value_counts().head(5).to_string(header=False)}

INSIGHTS AUTOMÁTICOS
- Cliente com maior volume: {df.groupby("Nome_Cliente")["Valor_Transacao"].sum().idxmax()}
- Banco dominante: {df["Banco"].value_counts().idxmax()}
- Percentual de transações concluídas: {(df["Status_Transacao"].eq("Aprovada").mean()*100):.1f}%
"""
