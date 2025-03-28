# A linha abaixo deve ser a PRIMEIRA instrução do script
import streamlit as st
st.set_page_config(page_title="Planilha de Produção Científica - UESC", layout="wide")

import requests
import pandas as pd
import json
from io import BytesIO
import os

st.title("📄 Planilha Completa de Produção Científica - UESC")

# Dados de entrada
dados_docentes = [
    {"CPF": "78209587749", "Nome": "andre", "DataNascimento": "01011970"},
    {"CPF": "03733046765", "Nome": "bruno", "DataNascimento": "01021970"},
    {"CPF": "16752072833", "Nome": "fernanda", "DataNascimento": "01011972"}
]

# Função para buscar dados da API
def consultar_dados(docente):
    url = 'https://www.stelaexperta.com.br/ws/totaiscv'
    headers = {'Content-Type': 'application/json'}

    payload = {
        "chave": "84030e4c-adf4-11ed-afa1-0242ac120002",
        "cpf": docente["CPF"],
        "nome": docente["Nome"],
        "dataNascimento": docente["DataNascimento"],
        "paisNascimento": "Brasil",
        "nacionalidade": "brasileira",
        "filtro": {
            "anoInicio": 2000,
            "anoFim": 2025
        },
        "downloadXml": 0
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

# Função para achatar recursivamente o JSON
def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], f'{name}{a}_')
        elif isinstance(x, list):
            # Se for lista de valores simples, concatena como string
            if all(isinstance(i, (str, int, float)) for i in x):
                out[name[:-1]] = ', '.join(map(str, x))
            else:
                # Ignora listas complexas (como listas de dicionários)
                pass
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

# Consulta dados e gera planilha completa
linhas = []
for docente in dados_docentes:
    with st.spinner(f"🔍 Buscando dados para {docente['Nome'].capitalize()}..."):
        dados = consultar_dados(docente)
        flat = flatten_json(dados)
        flat["Nome"] = docente["Nome"].capitalize()
        linhas.append(flat)

# Gera DataFrame a partir dos dados achatados
df = pd.DataFrame(linhas).fillna(0)
colunas_ordenadas = ["Nome"] + [c for c in df.columns if c != "Nome"]
df = df[colunas_ordenadas]

st.success("✅ Planilha completa gerada com sucesso!")

# Interface de configuração de pesos
st.subheader("⚙️ Configuração de Pesos")
st.markdown("Você pode carregar pesos de um arquivo ou definir manualmente abaixo.")

pesos = {}
pesos_default = {col: 0.0 for col in df.columns if col != "Nome"}

uploaded_pesos = st.file_uploader("📤 Importar planilha de pesos (.csv ou .xlsx)", type=["csv", "xlsx"])
if uploaded_pesos:
    if uploaded_pesos.name.endswith(".csv"):
        pesos_df = pd.read_csv(uploaded_pesos)
    else:
        pesos_df = pd.read_excel(uploaded_pesos)
    for _, row in pesos_df.iterrows():
        pesos[row["Indicador"]] = row["Peso"]
else:
    for coluna in df.columns:
        if coluna != "Nome":
            pesos[coluna] = st.number_input(f"Peso para {coluna}", value=0.0, step=0.1, key=f"peso_{coluna}")

# Botão para calcular
if st.button("🧮 Calcular Pontuação"):
    try:
        colunas_numericas = [col for col in df.columns if col != "Nome" and pd.api.types.is_numeric_dtype(df[col])]
        df["Pontuação Total"] = df[colunas_numericas].apply(
            lambda row: sum(float(row[col]) * float(pesos.get(col, 0)) for col in colunas_numericas), axis=1
        )
        st.subheader("📊 Pontuação Final por Docente")
        st.dataframe(df[["Nome", "Pontuação Total"]].sort_values(by="Pontuação Total", ascending=False), use_container_width=True)
    except Exception as e:
        st.error(f"Erro no cálculo da pontuação total: {e}")

    # Botão para download da planilha completa
    pesos_df = pd.DataFrame(list(pesos.items()), columns=["Indicador", "Peso"])
    towrite = BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Produção")
        pesos_df.to_excel(writer, index=False, sheet_name="Pesos")
    towrite.seek(0)
    st.download_button("📥 Baixar planilha Excel completa", towrite, file_name="producao_cientifica_completa.xlsx")
