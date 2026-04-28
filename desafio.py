import pandas as pd

df_original = pd.read_csv("Database.csv")

#Cópia dos Dados
df = df_original.copy()

#Remover os espaços
for col in df.select_dtypes(include=['object']):
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
mask_usd = df["Moeda"].eq("USD")
df["Data_Transacao"] = df["Data_Transacao"].astype(object)
df["Data_Transacao"] = df["Data_Transacao"].str.replace('.', '', regex=False)

df.loc[mask_usd, "Data_Transacao"] = pd.to_datetime(
    df.loc[mask_usd, "Data_Transacao"],
    errors="coerce",
    dayfirst=False
)

df.loc[~mask_usd, "Data_Transacao"] = pd.to_datetime(
    df.loc[~mask_usd, "Data_Transacao"],
    errors="coerce",
    dayfirst=True
)

df["Data_Transacao"] = pd.to_datetime(df["Data_Transacao"], errors='coerce')
df["Data_Transacao"] = df["Data_Transacao"].dt.strftime('%Y/%m/%d')


#Manter só números, vírgula, ponto e "-"
df["Valor_Transacao"] = df["Valor_Transacao"].str.replace(r"[^\d,.\-]", "", regex=True)

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
    pd.NA
)
df.loc[df["Valor_Transacao"].isna(), "Valor_Transacao"] = df["Valor_Transacao"].quantile(0.50)

#Ajeitar o tipo de Transação
df["Tipo_Transacao"] = df["Tipo_Transacao"].str.lower()

df.loc[df["Tipo_Transacao"].str.contains(r"p. *i. *x", na=False), "Tipo_Transacao"] = "PIX"

df.loc[df["Tipo_Transacao"].str.contains(r"ted|doc|transf", na=False), "Tipo_Transacao"] = "Transferência"

df.loc[df["Tipo_Transacao"].str.contains(r"p. *g. *t|boleto", na=False), "Tipo_Transacao"] = "Pagamento"

df.loc[df["Tipo_Transacao"].str.contains(r"d. *e. *p", na=False), "Tipo_Transacao"] = "Depósito"

df.loc[df["Tipo_Transacao"].str.contains(r"resgate|retirada|saque", na=False), "Tipo_Transacao"] = "Saque"

df.loc[df["Tipo_Transacao"].isna(), "Tipo_Transacao"] = df["Tipo_Transacao"].value_counts().idxmax()

#Ajeitar situação
df["Status_Transacao"] = df["Status_Transacao"].str.lower()
df.loc[df["Status_Transacao"].str.contains(r"aprov|autorizada", na=False), "Status_Transacao"] = "Aprovada"
df.loc[df["Status_Transacao"].str.contains(r"recus|bloq|negada", na=False), "Status_Transacao"] = "Recusada"
df.loc[df["Status_Transacao"].str.contains(r"pend|em processamento|aguardando", na=False), "Status_Transacao"] = "Pendente"

#Limpar os nomes duplicados
df["Nome_Cliente"] = (
    df["Nome_Cliente"]
    .str.strip()  
    .str.replace(r"[^A-Za-zÀ-ÿ\s]", " ", regex=True)                            
    .str.replace(r"\s+", " ", regex=True)     
    .str.title()                             
    .apply(lambda x: " ".join(dict.fromkeys(str(x).split()))) # <-- AQUI A MUDANÇA
)

#Organizar número de parcelas
df["Num_Parcelas"] = df["Num_Parcelas"].astype(str).str.extract(r'(\d+)').fillna(1).astype(int)

# Organizar taxas
df["Taxa_Servico"] = pd.to_numeric(df["Taxa_Servico"], errors="coerce").abs()
media = df["Taxa_Servico"].mean()
df["Taxa_Servico"] = df["Taxa_Servico"].fillna(media)
df["Taxa_Servico"] = df["Taxa_Servico"].astype(int)

#Corrigir Valor Final
df.loc[df["Valor_Final"] < df["Valor_Transacao"], "Valor_Final"] = df["Valor_Transacao"] + df["Taxa_Servico"]

print(df)