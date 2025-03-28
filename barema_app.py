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

# Carrega pesos e tipos do CSV (com correções)
PESOS_CACHE_PATH = "pesos_padrao.csv"
try:
    cache_df = pd.read_csv(PESOS_CACHE_PATH)
except FileNotFoundError:
    cache_df = pd.read_csv("https://raw.githubusercontent.com/fbrunoso/barema/refs/heads/main/pesos_tipos.csv")

# Normaliza os nomes dos indicadores e tipos
cache_df["Indicador"] = cache_df["Indicador"].astype(str).str.strip()
cache_df["Tipo"] = cache_df["Tipo"].fillna("0").apply(
    lambda x: str(int(float(x))) if str(x).replace('.', '', 1).isdigit() else "0"
)

# Cria dicionários de pesos e tipos
pesos = dict(zip(cache_df["Indicador"], cache_df["Peso"]))
tipos = dict(zip(cache_df["Indicador"], cache_df["Tipo"]))

# Diagnóstico visual
st.subheader("🧪 Diagnóstico de Indicadores")
st.write("📌 Colunas extraídas do DataFrame:", df.columns.tolist())
st.write("📌 Indicadores no CSV:", list(pesos.keys()))

# Mostra quais indicadores do CSV estão disponíveis no DataFrame
indicadores_validos = [col for col in df.columns if col in pesos]
st.subheader("🎯 Indicadores que serão utilizados no cálculo:")
st.write(indicadores_validos)

# Exibe o CSV carregado com pesos e tipos
st.subheader("📄 Pesos e Tipos Carregados")
st.dataframe(cache_df, use_container_width=True)

# Botão para cálculo
if st.button("🧮 Calcular Pontuação"):
    pesos_df = pd.DataFrame({
        "Indicador": indicadores_validos,
        "Peso": [pesos[k] for k in indicadores_validos],
        "Tipo": [tipos.get(k, "0") for k in indicadores_validos]
    })

    try:
        df["Pontuação Total"] = df[indicadores_validos].apply(
            lambda row: sum(float(row[col]) * float(pesos.get(col, 0)) for col in indicadores_validos), axis=1
        )

        st.subheader("📊 Pontuação Final por Docente")
        st.dataframe(df[["Nome", "Pontuação Total"]].sort_values(by="Pontuação Total", ascending=False), use_container_width=True)

        tipo_totais = []
        for tipo in ["1", "2", "3"]:
            tipo_cols = [row["Indicador"] for _, row in pesos_df.iterrows() if row["Tipo"] == tipo]
            if tipo_cols:
                tipo_label = f"Tipo {tipo} Total"
                df[tipo_label] = df[tipo_cols].apply(
                    lambda row: sum(float(row[col]) * float(pesos.get(col, 0)) for col in tipo_cols), axis=1
                )
                tipo_totais.append(tipo_label)

        if tipo_totais:
            st.subheader("📈 Totais por Tipo")
            cols_to_show = ["Nome"] + tipo_totais + ["Pontuação Total"]
            st.dataframe(df[cols_to_show].sort_values(by="Pontuação Total", ascending=False), use_container_width=True)
        else:
            st.info("ℹ️ Nenhum tipo relevante foi definido. Defina pelo menos um tipo (1, 2 ou 3) no CSV.")

    except Exception as e:
        st.error(f"Erro no cálculo da pontuação total: {e}")

    st.subheader("📤 Exportar Pesos, Tipos e Resultados")
    pesos_export = pd.DataFrame({
        "Indicador": list(pesos.keys()),
        "Peso": [pesos[k] for k in pesos.keys()],
        "Tipo": [tipos.get(k, "0") for k in pesos.keys()]
    })
    pesos_csv = pesos_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📁 Baixar pesos e tipos em CSV",
        data=pesos_csv,
        file_name="pesos_tipos.csv",
        mime="text/csv"
    )

    towrite = BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Produção")
        pesos_df.to_excel(writer, index=False, sheet_name="Pesos")
    towrite.seek(0)
    st.download_button("📥 Baixar planilha Excel completa", towrite, file_name="producao_cientifica_completa.xlsx")

    pesos_export.to_csv(PESOS_CACHE_PATH, index=False)
