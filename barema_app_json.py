import streamlit as st
import requests
import json

st.set_page_config(page_title="Barema Orientador - Edital IC 2025", layout="centered")
st.title("🔍 Consulta de Produção - Edital IC 2025")

# Inputs do usuário
cpf = st.text_input("CPF (sem pontos ou traços):")
nome = st.text_input("Nome completo:")
data_nasc = st.text_input("Data de nascimento (DDMMAAAA):", placeholder="Ex: 01011990")
ano_inicio = st.text_input("Ano de início da produção:", value="2021")
ano_fim = st.text_input("Ano de fim da produção:", value="2025")

if st.button("Buscar dados Lattes"):
    if not cpf or not nome or not data_nasc:
        st.warning("Por favor, preencha todos os campos obrigatórios.")
    else:
        url = 'https://www.stelaexperta.com.br/ws/totaiscv'
        headers = {'Content-Type': 'application/json'}

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

        with st.spinner("Consultando base CNPq..."):
            response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            try:
                data = response.json()
                st.success("✅ Consulta realizada com sucesso!")

                st.subheader("📄 JSON completo retornado pelo WS:")
                st.json(data)

                # Botão opcional para baixar JSON
                st.download_button(
                    label="📥 Baixar JSON completo",
                    data=json.dumps(data, indent=2),
                    file_name="resultado_ic2025.json",
                    mime="application/json"
                )

            except Exception as e:
                st.error(f"Erro ao processar a resposta JSON: {e}")
        else:
            st.error(f"Erro {response.status_code} ao consultar o WS: {response.text}")

