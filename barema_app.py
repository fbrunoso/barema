# A linha abaixo deve ser a PRIMEIRA instrução do script
import streamlit as st
st.set_page_config(page_title="Barema - UESC", layout="wide")

import requests
import pandas as pd
from io import BytesIO
from pathlib import Path
from fpdf import FPDF
import datetime
import os

st.title("📄 Barema - Produção Científica - UESC")

# === Lista de docentes (base para testes)
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

# === Carregamento de pesos e tipos ===
PESOS_PATH = "pesos_tipos_corrigido.csv"
pesos_df = pd.read_csv(PESOS_PATH)
pesos = dict(zip(pesos_df["Indicador"], pesos_df["Peso"]))
tipos = dict(zip(pesos_df["Indicador"], pesos_df["Tipo"].astype(str)))

# === Geração de relatório individual em PDF
def gerar_relatorio_pdf(flat, pesos, tipos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Relatório Individual de Avaliação - UESC", ln=1, align="C")

    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Nome: {flat.get('nomeCurriculo', 'N/A')}", ln=1)
    pdf.cell(0, 10, f"CPF: {flat.get('cpf', 'N/A')}", ln=1)
    pdf.cell(0, 10, f"Ano Início: {flat.get('filtro_anoInicio', '2000')} - Ano Fim: {flat.get('filtro_anoFim', '2025')}", ln=1)
    pdf.cell(0, 10, f"Data Atualização Currículo: {flat.get('dataAtualizacaoCurriculo', 'N/A')}", ln=1)
    pdf.cell(0, 10, f"Link Lattes: {flat.get('urlLattes', 'N/A')}", ln=1)
    pdf.cell(0, 10, f"Link XML: {flat.get('urlDownloadXmlPdf', 'N/A')}", ln=1)

    totais_tipo = {"1": 0, "2": 0, "3": 0}
    total_geral = 0

    for tipo in ["1", "2", "3"]:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, f"Tipo {tipo}", ln=1)

        pdf.set_font("Arial", size=10)
        pdf.cell(100, 8, "Indicador", border=1)
        pdf.cell(25, 8, "Valor", border=1)
        pdf.cell(25, 8, "Peso", border=1)
        pdf.cell(25, 8, "Pontos", border=1, ln=1)

        for indicador, t in tipos.items():
            if t == tipo and indicador in flat:
                valor = pd.to_numeric(flat.get(indicador), errors='coerce')
                valor = 0 if pd.isna(valor) else float(valor)
                peso = float(pesos.get(indicador, 0))
                pontos = valor * peso
                totais_tipo[tipo] += pontos
                pdf.cell(100, 8, indicador, border=1)
                pdf.cell(25, 8, str(valor), border=1)
                pdf.cell(25, 8, str(peso), border=1)
                pdf.cell(25, 8, f"{pontos:.2f}", border=1, ln=1)

        pdf.cell(150, 8, "Subtotal", border=1)
        pdf.cell(25, 8, f"{totais_tipo[tipo]:.2f}", border=1, ln=1)
        total_geral += totais_tipo[tipo]

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(150, 10, "Pontuação Total", border=1)
    pdf.cell(25, 10, f"{total_geral:.2f}", border=1, ln=1)

    return pdf.output(dest='S').encode('latin1')

# === TESTE PDF ===
st.sidebar.subheader("🧪 Testar Avaliação Individual")
cpf_teste = st.sidebar.text_input("Informe o CPF do docente para gerar PDF", value="03733046765")

docente_teste = next((d for d in dados_docentes if d["CPF"] == cpf_teste), None)

if docente_teste and st.sidebar.button("📄 Gerar PDF de Avaliação"):
    with st.spinner("Consultando e gerando relatório..."):
        dados = consultar_dados(docente_teste)
        flat = flatten_json(dados)
        pdf_bytes = gerar_relatorio_pdf(flat, pesos=pesos, tipos=tipos)
        st.sidebar.success("✅ PDF gerado com sucesso!")
        st.sidebar.download_button("📥 Baixar PDF", data=pdf_bytes, file_name="avaliacao_individual.pdf", mime="application/pdf")

# === Geração em lote para todos os docentes ===
st.subheader("📦 Gerar PDFs para todos os docentes")
if st.button("📁 Gerar e baixar todos os relatórios PDF"):
    with st.spinner("Gerando relatórios em lote..."):
        arquivos = []
        for docente in dados_docentes:
            dados = consultar_dados(docente)
            flat = flatten_json(dados)
            pdf_bytes = gerar_relatorio_pdf(flat, pesos=pesos, tipos=tipos)
            arquivos.append((docente['Nome'], pdf_bytes))

        from zipfile import ZipFile
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zipf:
            for nome, content in arquivos:
                zipf.writestr(f"{nome}_avaliacao.pdf", content)
        zip_buffer.seek(0)

        st.success("✅ Todos os PDFs foram gerados!")
        st.download_button("📦 Baixar ZIP com os relatórios", data=zip_buffer, file_name="avaliacoes_uesc.zip", mime="application/zip")
