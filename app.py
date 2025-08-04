import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    layout="wide",
    page_title="Dashboard de Monitoramento"
)

# Dicionário de nomes de colunas atualizado
colunas = {
    "FASEA": {
        "tensao": "Tensao_Fase_A",
        "corrente": "Corrente_Fase_A"
    },
    "FASEB": {
        "tensao": "Tensao_Fase_B",
        "corrente": "Corrente_Fase_B"
    },
    "FASEC": {
        "tensao": "Tensao_Fase_C",
        "corrente": "Corrente_Fase_C"
    }
}

# Função para carregar e limpar dados do CSV
@st.cache_data
def load_and_clean_csv(file_path):
    df = pd.read_csv(
        file_path,
        sep=','
    )
    df["Data_Hora"] = pd.to_datetime(df["Data"] + " " + df["Horário"], format="%d/%m/%Y %H:%M:%S")
    return df

# Função para obter os dados de cada fase
def get_dados(fase, dia_escolhido):
    # Dicionário de caminhos de arquivo
    file_paths = {
        "FASEA": "Medicoes_FASEA.csv",
        "FASEB": "Medicoes_FASEB.csv",
        "FASEC": "Medicoes_FASEC.csv"
    }

    try:
        df = load_and_clean_csv(file_paths[fase])
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {file_paths[fase]}")
        return [], [], []

    dia_formatado = dia_escolhido.strftime("%d/%m/%Y")
    df_dia = df[df["Data"] == dia_formatado].copy()

    if df_dia.empty:
        return [], [], []

    df_dia = df_dia.sort_values(by="Data_Hora")
    
    # Use os nomes de colunas corrigidos
    tensao = df_dia[colunas[fase]["tensao"]].astype(str).str.replace(",", ".").astype(float).tolist()
    corrente = df_dia[colunas[fase]["corrente"]].astype(str).str.replace(",", ".").astype(float).tolist()
    horarios = df_dia["Horário"].tolist()
    return tensao, corrente, horarios

# Título do dashboard
st.title("Supervisório de Medição")

# Seleção da fase
fase = st.selectbox(
    "Selecione a Fase",
    ["FASEA", "FASEB", "FASEC"]
)

# Seleção do dia
dia_atual = datetime.date.today()
radio_options = ["Dia Atual", "Dia Anterior"]
dia_radio = st.radio(
    "Selecione o Dia para Análise",
    radio_options,
    horizontal=True
)

# Definição do dia escolhido
if dia_radio == "Dia Atual":
    dia_escolhido = dia_atual
    _ = get_dados(fase, dia_escolhido)
    tensao_data = st.session_state.get(f"valores_{fase}", {}).get("tensao", [])
    corrente_data = st.session_state.get(f"valores_{fase}", {}).get("corrente", [])
    horarios_data = st.session_state.get(f"valores_{fase}", {}).get("horarios", [])
    
    # Acesso seguro ao último índice
    last_idx = len(tensao_data) - 1
    if last_idx >= 0:
        tensao = tensao_data[last_idx]
        corrente = corrente_data[last_idx]
        hora_ultima_medicao = horarios_data[last_idx]
    else:
        tensao = "N/A"
        corrente = "N/A"
        hora_ultima_medicao = "N/A"
        
    st.markdown(f"**Última medição ({hora_ultima_medicao}):**")
    st.metric("Tensão", f"{tensao} V")
    st.metric("Corrente", f"{corrente} A")

elif dia_radio == "Dia Anterior":
    dia_escolhido = dia_atual - datetime.timedelta(days=1)
    tensao_data, corrente_data, horarios_data = get_dados(fase, dia_escolhido)

# Salvar dados no session_state para plots
st.session_state[f"valores_{fase}"] = {
    "tensao": tensao_data,
    "corrente": corrente_data,
    "horarios": horarios_data
}

# --- Visualização de Gráficos ---

st.header(f"Dados da {fase}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Gráfico de Tensão")
    if tensao_data:
        df_tensao = pd.DataFrame({
            "Horário": horarios_data,
            "Tensão (V)": tensao_data
        })
        st.line_chart(df_tensao.set_index("Horário"))
    else:
        st.warning("Não há dados de tensão para o dia selecionado.")

with col2:
    st.subheader("Gráfico de Corrente")
    if corrente_data:
        df_corrente = pd.DataFrame({
            "Horário": horarios_data,
            "Corrente (A)": corrente_data
        })
        st.line_chart(df_corrente.set_index("Horário"))
    else:
        st.warning("Não há dados de corrente para o dia selecionado.")
