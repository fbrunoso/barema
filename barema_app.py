import streamlit as st
import requests
import pandas as pd
import json
from io import BytesIO

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
            "anoInicio": 2021,
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
        st.expander(f"📄 JSON bruto - {docente['Nome'].capitalize()}").json(dados)
        dados["nome"] = docente["Nome"].capitalize()
        dados_todos.append(dados)

# Criação do DataFrame consolidado
linhas = []
for d in dados_todos:
    linhas.append({
        "Nome": d.get("nome", "-"),
        "Artigos em Periódicos": d.get("producaoBibliografica", {}).get("artigosEmPeriodicos", 0),
        "Trabalhos em Anais": d.get("producaoBibliografica", {}).get("trabalhosEmAnais", 0),
        "Livros": d.get("producaoBibliografica", {}).get("livros", 0),
        "Capítulos": d.get("producaoBibliografica", {}).get("capitulos", 0),
        "Software": d.get("producaoTecnica", {}).get("software", 0),
        "Patentes": d.get("producaoTecnica", {}).get("patente", 0),
        "Orientações Concluídas": d.get("orientacoes", {}).get("concluidas", 0),
        "Projetos": d.get("projetos", {}).get("total", 0)
    })

df = pd.DataFrame(linhas)

st.subheader("📊 Comparativo de Produção Científica")
st.dataframe(df, use_container_width=True)

# Gráfico interativo
import plotly.express as px

st.subheader("📈 Produção por Tipo")
coluna_selecionada = st.selectbox("Selecione o tipo de produção:", df.columns[1:])
fig = px.bar(df, x="Nome", y=coluna_selecionada, color="Nome", text_auto=True)
st.plotly_chart(fig, use_container_width=True)

# Botão de download do consolidado
towrite = BytesIO()
df.to_excel(towrite, index=False, sheet_name='ProducaoDocente')
towrite.seek(0)
st.download_button("📥 Baixar tabela consolidada", towrite, file_name="producao_docente_uesc.xlsx")
