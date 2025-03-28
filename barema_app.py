import streamlit as st
import requests
import pandas as pd
import json
from io import BytesIO

st.set_page_config(page_title="Dashboard Produção Docente - UESC", layout="wide")
st.title("📊 Dashboard de Produção Científica - UESC (Teste)")

# Dados de entrada (simulados neste exemplo)
dados_docentes = [
    {"CPF": "78209587749", "Nome": "andre", "DataNascimento": "01011970"},
    {"CPF": "03733046765", "Nome": "bruno", "DataNascimento": "01021970"},
    {"CPF": "16752072833", "Nome": "fernanda", "DataNascimento": "01011972"}
]

st.sidebar.header("🎓 Seleção de Docente")
nomes_docentes = [docente["Nome"].capitalize() for docente in dados_docentes]
docente_selecionado = st.sidebar.selectbox("Escolha um docente:", nomes_docentes)

# Dados da API
docente_info = next(d for d in dados_docentes if d["Nome"].capitalize() == docente_selecionado)

url = 'https://www.stelaexperta.com.br/ws/totaiscv'
headers = {'Content-Type': 'application/json'}

payload = {
    "chave": "84030e4c-adf4-11ed-afa1-0242ac120002",
    "cpf": docente_info["CPF"],
    "nome": docente_info["Nome"],
    "dataNascimento": docente_info["DataNascimento"],
    "paisNascimento": "Brasil",
    "nacionalidade": "brasileira",
    "filtro": {
        "areaAvaliacaoQualis": 1,
        "anoInicio": 2021,
        "anoFim": 2025,
        "educacaoPopularizacaoCeT": 1
    },
    "downloadXml": 0
}

with st.spinner(f"🔍 Buscando dados para {docente_selecionado}..."):
    response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    data = response.json()
    st.success("✅ Dados carregados com sucesso!")

    st.subheader("📄 Dados completos retornados pelo WS:")
    st.json(data)

    st.download_button(
        label="📥 Baixar JSON",
        data=json.dumps(data, indent=2),
        file_name=f"dados_{docente_selecionado.lower()}.json",
        mime="application/json"
    )

else:
    st.error(f"Erro {response.status_code} ao consultar a API: {response.text}")
