# A linha abaixo deve ser a PRIMEIRA instrução do script
import streamlit as st
st.set_page_config(page_title="Planilha de Produção Científica - UESC", layout="wide")

import requests
import pandas as pd
import json
from io import BytesIO

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
        if type(x) is dict:
            for a in x:
                flatten(x[a], f'{name}{a}_')
        elif type(x) is list:
            for i, a in enumerate(x):
                flatten(a, f'{name}{i}_')
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

# Campo para inserir pesos
st.subheader("⚖️ Atribuição de Pesos")
pesos = {}
for coluna in df.columns:
    if coluna != "Nome":
        pesos[coluna] = st.number_input(f"Peso para {coluna}", value=1.0, step=0.1, key=f"peso_{coluna}")

# Cálculo da pontuação total para todos os docentes
try:
    colunas_numericas = [col for col in df.columns if col != "Nome"]
    df["Pontuação Total"] = df[colunas_numericas].apply(
        lambda row: sum(float(row[col]) * float(pesos.get(col, 0)) for col in colunas_numericas), axis=1
    )
except Exception as e:
    st.error(f"Erro no cálculo da pontuação total: {e}")

# Exibe resultado final
st.subheader("📊 Pontuação Final por Docente")
if "Pontuação Total" in df.columns:
    st.dataframe(df[["Nome", "Pontuação Total"]].sort_values(by="Pontuação Total", ascending=False), use_container_width=True)
else:
    st.warning("⚠️ Não foi possível calcular a pontuação total. Verifique os dados e os pesos atribuídos.")

# Botão para download da planilha completa
# Também salvar os pesos usados
pesos_df = pd.DataFrame(list(pesos.items()), columns=["Indicador", "Peso"])

# Cria planilha com duas abas
with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name="Produção")
    pesos_df.to_excel(writer, index=False, sheet_name="Pesos")

towrite.seek(0)
st.download_button("📥 Baixar planilha Excel completa", towrite, file_name="producao_cientifica_completa.xlsx")
