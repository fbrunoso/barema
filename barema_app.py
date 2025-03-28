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
    {"CPF": "16752072833", "Nome": "fernanda", "DataNascimento": "01011972"},
    {"CPF": "33405751268", "Nome": "jorge", "DataNascimento": "01011972"}
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
            if all(isinstance(i, (str, int, float)) for i in x):
                out[name[:-1]] = ', '.join(map(str, x))
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

# Consulta dados e gera planilha completa
campos_presentes = set()
linhas = []
for docente in dados_docentes:
    with st.spinner(f"🔍 Buscando dados para {docente['Nome'].capitalize()}..."):
        dados = consultar_dados(docente)
        flat = flatten_json(dados)
        campos_presentes.update(flat.keys())
        flat["Nome"] = docente["Nome"].capitalize()
        linhas.append(flat)

st.subheader("📋 Campos extraídos por docente")
for linha in linhas:
    nome = linha.get("Nome", "Desconhecido")
    st.markdown(f"**{nome}**: {len(linha.keys()) - 1} campos extraídos")
    with st.expander("🔍 Ver campos", expanded=False):
        st.write(sorted([k for k in linha.keys() if k != "Nome"]))

# Gera DataFrame
df = pd.DataFrame(linhas)
for campo in campos_presentes:
    if campo not in df.columns:
        df[campo] = 0
df = df.fillna(0)
colunas_ordenadas = ["Nome"] + [c for c in df.columns if c != "Nome"]
df = df[colunas_ordenadas]

st.success("✅ Planilha completa gerada com sucesso!")

# Interface de configuração de pesos e tipos
PESOS_CACHE_PATH = "pesos_padrao.csv"
pesos_cache = {}
tipos_cache = {}

try:
    cache_df = pd.read_csv(PESOS_CACHE_PATH)
except FileNotFoundError:
    cache_df = pd.read_csv("https://raw.githubusercontent.com/fbrunoso/barema/refs/heads/main/pesos_tipos.csv")

for _, row in cache_df.iterrows():
    pesos_cache[row["Indicador"]] = row["Peso"]
    tipos_cache[row["Indicador"]] = str(row.get("Tipo", "0")).strip()

st.subheader("⚙️ Configuração de Pesos e Tipos")
pesos = {}
tipos = {}
st.markdown("Defina abaixo o peso e o tipo (1, 2, 3) de cada indicador. Use 0 para indicadores sem tipo.")

opcoes_tipo = ["0", "1", "2", "3"]

for coluna in df.columns:
    if coluna != "Nome":
        cols = st.columns([0.6, 0.4])
        with cols[0]:
            pesos[coluna] = st.number_input(
                f"Peso - {coluna}",
                value=pesos_cache.get(coluna, 0.0),
                step=0.1,
                key=f"peso_{coluna}"
            )
        with cols[1]:
            tipo_padrao = str(tipos_cache.get(coluna, "0")).strip()
            if tipo_padrao not in opcoes_tipo:
                tipo_padrao = "0"
            tipos[coluna] = st.radio(
                f"Tipo - {coluna}",
                options=opcoes_tipo,
                horizontal=True,
                key=f"tipo_{coluna}",
                value=tipo_padrao
            )

if st.button("🧮 Calcular Pontuação"):
    pesos_df = pd.DataFrame({
        "Indicador": list(pesos.keys()),
        "Peso": [pesos[k] for k in pesos.keys()],
        "Tipo": [tipos.get(k, "0") for k in pesos.keys()]
    })
    try:
        colunas_numericas = [col for col in df.columns if col != "Nome" and pd.api.types.is_numeric_dtype(df[col])]
        df["Pontuação Total"] = df[colunas_numericas].apply(
            lambda row: sum(float(row[col]) * float(pesos.get(col, 0)) for col in colunas_numericas), axis=1
        )
        st.subheader("📊 Pontuação Final
