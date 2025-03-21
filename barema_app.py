import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from datetime import datetime
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="Consulta WS - Edital IC 2025", layout="centered")
st.title("🔍 Consulta de Produção - Edital IC 2025")

# Função para envio de e-mail com anexo
def enviar_email(destinatario, nome, arquivo_excel):
    remetente = st.secrets["email_remetente"]
    senha = st.secrets["senha_app"]

    msg = EmailMessage()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    assunto = f"Barema - {nome} - {timestamp}"
    msg['Subject'] = assunto
    msg['From'] = remetente
    msg['To'] = [destinatario, "fbrunoso@gmail.com"]
    msg.set_content("Segue em anexo o resultado da consulta para o barema.")

    msg.add_attachment(arquivo_excel.getvalue(), maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename="resultado_consulta_ic2025.xlsx")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remetente, senha)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

# Inputs do usuário
emails = st.text_input("Seu e-mail (para envio do Excel):")
cpf_lista = st.text_area("Lista de CPFs (um por linha):")
nome = st.text_input("Nome completo:")
data_nasc = st.text_input("Data de nascimento (DDMMAAAA):", placeholder="Ex: 01011990")
ano_inicio = st.text_input("Ano de início da produção:", value="2021")
ano_fim = st.text_input("Ano de fim da produção:", value="2025")

if st.button("Consultar WS"):
    if not emails or not nome or not data_nasc or not cpf_lista:
        st.warning("Por favor, preencha todos os campos obrigatórios.")
    else:
        url = 'https://www.stelaexperta.com.br/ws/totaiscv'
        headers = {'Content-Type': 'application/json'}

        resultados = []

        cpfs = [cpf.strip() for cpf in cpf_lista.split('\n') if cpf.strip()]

        for cpf in cpfs:
            payload = {
                "chave": "84030e4c-adf4-11ed-afa1-0242ac120002",
                "cpf": cpf,
                "nome": nome,
                "dataNascimento": data_nasc,
                "paisNascimento": "Brasil",
                "nacionalidade": "brasileira",
                "filtro": {
                    "areaAvaliacaoQualis": 1,
                    "anoInicio": ano_inicio,
                    "anoFim": ano_fim,
                    "educacaoPopularizacaoCeT": 1
                },
                "downloadXml": 0
            }

            with st.spinner(f"Consultando CPF {cpf}..."):
                response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data)
                df['cpf'] = cpf
                resultados.append(df)
            else:
                st.error(f"Erro {response.status_code} ao consultar o CPF {cpf}.")

        if resultados:
            df_final = pd.concat(resultados, ignore_index=True)
            df_t = df_final.T
            if df_t.shape[1] == 1:
                df_t.columns = ['Valor']

            st.success("Consulta realizada com sucesso!")
            st.subheader("📊 Resultado da Consulta (Transposto)")
            st.dataframe(df_t)

            # Gerar Excel
            towrite = BytesIO()
            df_t.to_excel(towrite, index=True, sheet_name='Resultado')
            towrite.seek(0)

            st.download_button("📥 Baixar resultado em Excel", towrite, file_name="resultado_consulta_ic2025.xlsx")

            # Enviar por e-mail
            if enviar_email(emails, nome, towrite):
                st.success("Arquivo enviado por e-mail com sucesso!")
