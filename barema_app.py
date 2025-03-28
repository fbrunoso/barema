import streamlit as st
import requests
import pandas as pd
import json
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="Dashboard Produção Docente - UESC", layout="wide")
st.title("📊 Dashboard de Produção Científica - UESC (Teste)")

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
            "areaAvaliacaoQualis": 1,
            "anoInicio": 2000,
            "anoFim": 2025,
            "educacaoPopularizacaoCeT": 1
        },
        "downloadXml": 0
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

# Consulta dados de todos os docentes
dados_todos = []
for docente in dados_docentes:
    with st.spinner(f"🔍 Buscando dados para {docente['Nome'].capitalize()}..."):
        dados = consultar_dados(docente)
        dados["nome"] = docente["Nome"].capitalize()
        dados_todos.append(dados)
        st.expander(f"📄 JSON bruto - {docente['Nome'].capitalize()}").json(dados)

# Criação do DataFrame consolidado
linhas = []
for d in dados_todos:
    def extrair_total(dic, chave):
        val = dic.get(chave)
        if isinstance(val, dict):
            return val.get("total", 0)
        return val if isinstance(val, int) else 0

    prod_bib = d.get("producaoBibliografica", {})
    prod_tec = d.get("producaoTecnica", {})
    orient = d.get("orientacoes", {})
    proj = d.get("projetos", {})

    linhas.append({
        "Nome": d.get("nome", "-"),
        "Artigos em Periódicos": extrair_total(prod_bib, "artigosEmPeriodicos"),
        "Trabalhos em Anais": extrair_total(prod_bib, "trabalhosEmAnais"),
        "Livros": extrair_total(prod_bib, "livros"),
        "Capítulos": extrair_total(prod_bib, "capitulos"),
        "Software": extrair_total(prod_tec, "software"),
        "Patentes": extrair_total(prod_tec, "patente"),
        "Orientações Concluídas": extrair_total(orient, "concluidas"),
        "Projetos": proj.get("total", 0)
    })

df = pd.DataFrame(linhas)

st.subheader("📊 Comparativo de Produção Científica")
st.dataframe(df, use_container_width=True)

st.subheader("📈 Produção por Tipo")
coluna_selecionada = st.selectbox("Selecione o tipo de produção:", df.columns[1:])
fig = px.bar(df, x="Nome", y=coluna_selecionada, color="Nome", text_auto=True)
st.plotly_chart(fig, use_container_width=True)

# Botão de download do consolidado
towrite = BytesIO()
df.to_excel(towrite, index=False, sheet_name='ProducaoDocente')
towrite.seek(0)
st.download_button("📥 Baixar tabela consolidada", towrite, file_name="producao_docente_uesc.xlsx")
import streamlit as st
import requests
import pandas as pd
import json
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="Dashboard Produção Docente - UESC", layout="wide")
st.title("📊 Dashboard de Produção Científica - UESC (Teste)")

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
            "areaAvaliacaoQualis": 1,
            "anoInicio": 2000,
            "anoFim": 2025,
            "educacaoPopularizacaoCeT": 1
        },
        "downloadXml": 0
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

# Consulta dados de todos os docentes
dados_todos = []
for docente in dados_docentes:
    with st.spinner(f"🔍 Buscando dados para {docente['Nome'].capitalize()}..."):
        dados = consultar_dados(docente)
        dados["nome"] = docente["Nome"].capitalize()
        dados_todos.append(dados)
        st.expander(f"📄 JSON bruto - {docente['Nome'].capitalize()}").json(dados)

# Criação do DataFrame consolidado
linhas = []
for d in dados_todos:
    def extrair_total(dic, chave):
        val = dic.get(chave)
        if isinstance(val, dict):
            return val.get("total", 0)
        return val if isinstance(val, int) else 0

    prod_bib = d.get("producaoBibliografica", {})
    prod_tec = d.get("producaoTecnica", {})
    orient = d.get("orientacoes", {})
    proj = d.get("projetos", {})

    linhas.append({
        "Nome": d.get("nome", "-"),
        "Artigos em Periódicos": extrair_total(prod_bib, "artigosEmPeriodicos"),
        "Trabalhos em Anais": extrair_total(prod_bib, "trabalhosEmAnais"),
        "Livros": extrair_total(prod_bib, "livros"),
        "Capítulos": extrair_total(prod_bib, "capitulos"),
        "Software": extrair_total(prod_tec, "software"),
        "Patentes": extrair_total(prod_tec, "patente"),
        "Orientações Concluídas": extrair_total(orient, "concluidas"),
        "Projetos": proj.get("total", 0)
    })

df = pd.DataFrame(linhas)

st.subheader("📊 Comparativo de Produção Científica")
st.dataframe(df, use_container_width=True)

st.subheader("📈 Produção por Tipo")
coluna_selecionada = st.selectbox("Selecione o tipo de produção:", df.columns[1:])
fig = px.bar(df, x="Nome", y=coluna_selecionada, color="Nome", text_auto=True)
st.plotly_chart(fig, use_container_width=True)

# Botão de download do consolidado
towrite = BytesIO()
df.to_excel(towrite, index=False, sheet_name='ProducaoDocente')
towrite.seek(0)
st.download_button("📥 Baixar tabela consolidada", towrite, file_name="producao_docente_uesc.xlsx")
