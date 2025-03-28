# A linha abaixo deve ser a PRIMEIRA instrução do script
import streamlit as st
st.set_page_config(page_title="Dashboard Produção Docente - UESC", layout="wide")

import requests
import pandas as pd
import json
from io import BytesIO
import plotly.express as px

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

# Consulta dados de todos os docentes e transforma diretamente em linhas para DataFrame
def extrair_linha(nome, dados):
    linha = {"Nome": nome}
    campos = [
        ("Artigos em Periódicos", ["producaoBibliografica", "artigosEmPeriodicos"]),
        ("Trabalhos em Anais", ["producaoBibliografica", "trabalhosEmAnais"]),
        ("Livros", ["producaoBibliografica", "livros"]),
        ("Capítulos", ["producaoBibliografica", "capitulos"]),
        ("Software", ["producaoTecnica", "software"]),
        ("Patentes", ["producaoTecnica", "patente"]),
        ("Orientações Concluídas", ["orientacoes", "concluidas"]),
        ("Projetos", ["projetos"])
    ]
    for rotulo, caminho in campos:
        valor = dados
        for chave in caminho:
            valor = valor.get(chave, {}) if isinstance(valor, dict) else {}
        linha[rotulo] = valor.get("total", 0) if isinstance(valor, dict) else 0
    return linha

linhas = []
dados_todos = []
for docente in dados_docentes:
    with st.spinner(f"🔍 Buscando dados para {docente['Nome'].capitalize()}..."):
        dados = consultar_dados(docente)
        dados_todos.append({"nome": docente["Nome"].capitalize(), "dados": dados})
        st.expander(f"📄 JSON bruto - {docente['Nome'].capitalize()}").json(dados)
        linhas.append(extrair_linha(docente["Nome"].capitalize(), dados))

# Gera DataFrame a partir das linhas
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
