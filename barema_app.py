# A linha abaixo deve ser a PRIMEIRA instrução do script
import streamlit as st
st.set_page_config(page_title="Barema - UESC", layout="wide")

import requests
import pandas as pd
from io import BytesIO

st.title("📄 Barema - Produção Científica - UESC")

# === Lista de docentes
dados_docentes = [
    {"CPF": "78209587749", "Nome": "andre", "DataNascimento": "01011970"},
    {"CPF": "03733046765", "Nome": "bruno", "DataNascimento": "01021970"},
    {"CPF": "16752072833", "Nome": "fernanda", "DataNascimento": "01011972"},
    {"CPF": "33405751268", "Nome": "jorge", "DataNascimento": "01011972"}
]

# === Função para buscar dados da API
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
        "filtro": {"anoInicio": 2000, "anoFim": 2025},
        "downloadXml": 0
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json() if response.status_code == 200 else {}

# === Função para achatar JSON
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

# === Upload do CSV com pesos/tipos
st.subheader("📤 Envie o arquivo de Pesos e Tipos")
uploaded_file = st.file_uploader("CSV com as colunas: Indicador, Peso, Tipo", type="csv")

if not uploaded_file:
    st.warning("⚠️ Por favor, envie o arquivo CSV para continuar.")
    st.stop()

# === Carrega e limpa os dados do CSV
pesos_df = pd.read_csv(uploaded_file)
pesos_df.columns = pesos_df.columns.str.strip().str.lower()
pesos_df["tipo"] = (
    pd.to_numeric(pesos_df["tipo"], errors="coerce")
    .fillna(0)
    .astype(int)
    .astype(str)
)
pesos_df["peso"] = pd.to_numeric(pesos_df["peso"], errors="coerce").fillna(0)

# === Busca dados da API
st.subheader("🔍 Coleta de Dados da API")
campos_presentes = set()
linhas = []
for docente in dados_docentes:
    with st.spinner(f"Buscando dados para {docente['Nome'].capitalize()}..."):
        dados = consultar_dados(docente)
        flat = flatten_json(dados)
        campos_presentes.update(flat.keys())
        flat["Nome"] = docente["Nome"].capitalize()
        linhas.append(flat)

# === Criação do DataFrame principal
df = pd.DataFrame(linhas)
for campo in campos_presentes:
    if campo not in df.columns:
        df[campo] = 0
df = df.fillna(0)
colunas_ordenadas = ["Nome"] + [c for c in df.columns if c != "Nome"]
df = df[colunas_ordenadas]

st.success("✅ Planilha gerada com sucesso!")

# === Interface de configuração de pesos e tipos
st.subheader("⚙️ Configuração de Pesos e Tipos")
pesos = {}
tipos = {}
opcoes_tipo = ["0", "1", "2", "3"]

for _, row in pesos_df.iterrows():
    indicador = row["indicador"]
    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        pesos[indicador] = st.number_input(
            f"Peso - {indicador}", value=float(row["peso"]), step=0.1, key=f"peso_{indicador}"
        )
    with col2:
        tipo_padrao = row["tipo"] if row["tipo"] in opcoes_tipo else "0"
        tipos[indicador] = st.radio(
            f"Tipo - {indicador}", options=opcoes_tipo,
            index=opcoes_tipo.index(tipo_padrao), horizontal=True, key=f"tipo_{indicador}"
        )

# === Cálculo robusto
if st.button("🧮 Calcular Pontuação"):
    indicadores_validos = list(set(df.columns) & set(pesos.keys()))

    # Diagnóstico útil
    st.subheader("🧪 Diagnóstico de Indicadores")
    st.markdown(f"- 🔢 **Indicadores no DataFrame**: `{len(df.columns)}`")
    st.markdown(f"- 🎯 **Indicadores no CSV**: `{len(pesos)}`")
    st.markdown(f"- ✅ **Indicadores utilizados no cálculo**: `{len(indicadores_validos)}`")

    def calcular_pontuacao(row):
        return sum(
            float(pd.to_numeric(row[col], errors="coerce") or 0) * float(pesos.get(col, 0))
            for col in indicadores_validos
        )

    df["Pontuação Total"] = df.apply(calcular_pontuacao, axis=1)

    st.subheader("📊 Pontuação Final por Docente")
    st.dataframe(df[["Nome", "Pontuação Total"]].sort_values(by="Pontuação Total", ascending=False), use_container_width=True)

    tipo_totais = []
    for tipo in ["1", "2", "3"]:
        tipo_cols = [k for k, v in tipos.items() if v == tipo and k in df.columns]
        if tipo_cols:
            tipo_label = f"Tipo {tipo} Total"
            df[tipo_label] = df[tipo_cols].apply(
                lambda row: sum(
                    float(pd.to_numeric(row[col], errors="coerce") or 0) * float(pesos.get(col, 0))
                    for col in tipo_cols
                ), axis=1
            )
            tipo_totais.append(tipo_label)

    if tipo_totais:
        st.subheader("📈 Totais por Tipo")
        cols_to_show = ["Nome"] + tipo_totais + ["Pontuação Total"]
        st.dataframe(df[cols_to_show].sort_values(by="Pontuação Total", ascending=False), use_container_width=True)
    else:
        st.info("ℹ️ Nenhum tipo relevante foi definido.")

    # Exportações
    st.subheader("📤 Exportar Resultados")
    pesos_export = pd.DataFrame({
        "Indicador": list(pesos.keys()),
        "Peso": [pesos[k] for k in pesos.keys()],
        "Tipo": [tipos[k] for k in tipos.keys()]
    })

    st.download_button("📁 Baixar pesos e tipos (CSV)", data=pesos_export.to_csv(index=False).encode('utf-8'),
                       file_name="pesos_tipos_atualizado.csv", mime="text/csv")

    towrite = BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Produção")
        pesos_export.to_excel(writer, index=False, sheet_name="Pesos")
    towrite.seek(0)
    st.download_button("📥 Baixar Excel completo", towrite, file_name="producao_uesc_completa.xlsx")
