import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAÇÕES ---
CSV_PATH = "Planilha_242_LAT - FASEA.csv"
REFRESH_INTERVAL_MS = 500  # milissegundos para o st_autorefresh

# --- LEITURA E LIMPEZA DO CSV ---
@st.cache_data
def load_and_clean_csv(path):
    df = pd.read_csv(path)
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
        try:
            df[col] = df[col].astype(float)
        except ValueError:
            pass
    return df

# --- ESTILOS ---
def visor(valor, label, cor_fundo, cor_texto):
    st.markdown(f"""
    <div style='
        background-color: {cor_fundo};
        color: {cor_texto};
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    '>
        {label}: {valor}
    </div>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Supervisório LAT", layout="wide")
# st.title("🔌 Supervisório LAT - Visual Dinâmico")

# --- VERIFICA SE O ARQUIVO EXISTE ---
if not os.path.exists(CSV_PATH):
    st.error("Arquivo CSV não encontrado.")
    st.stop()

# --- CARREGA OS DADOS ---
df = load_and_clean_csv(CSV_PATH)

# --- CONTROLE DO INDEX COM SESSION STATE ---
if "index" not in st.session_state:
    st.session_state.index = 0

# --- AUTOREFRESH A CADA 0.5 SEGUNDOS ---
count = st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- LÊ A LINHA ATUAL ---
if st.session_state.index >= len(df):
    st.success("Simulação concluída.")
    st.stop()

row = df.iloc[st.session_state.index]
st.session_state.index += 1

# --- EXTRAI OS VALORES ---
tensao = row.get("Tensao_Fase_ A", None)
frequencia = row.get("Frequencia_Fase_A", None)
corrente = row.get("Corrente_Fase_A", None)

# --- EXIBE OS VISUAIS ---
col1, col2, col3 = st.columns(3)

with col1:
    if tensao is not None:
        tensao_valor = float(tensao)
        cor_fundo = "#c0392b" if tensao_valor < 210 else "#2c3e50"
        cor_texto = "#ffffff" if tensao_valor < 210 else "#2ecc71"
        visor(f"{tensao_valor:.1f} V", "V", cor_fundo, cor_texto)

with col2:
    if frequencia is not None:
        freq_valor = float(frequencia)
        visor(f"{freq_valor:.1f} Hz", "F", "#2c3e50", "#2ecc71")

with col3:
    if corrente is not None:
        corrente_valor = float(corrente)
        visor(f"{corrente_valor:.1f} A", "I", "#2c3e50", "#2ecc71")

# --- PLOT DA TENSÃO ---
if "tensoes" not in st.session_state:
    st.session_state.tensoes = []

if tensao is not None:
    st.session_state.tensoes.append(float(tensao))
    st.session_state.tensoes = st.session_state.tensoes[-50:]  # Janela deslizante

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=st.session_state.tensoes,
        mode='lines+markers',
        line=dict(color="#2980b9", width=2),
        name="Tensão"
    ))
    fig.update_layout(
        title="Tensão Fase A (V)",
        xaxis_title="Amostras",
        yaxis_title="Tensão (V)",
        height=400,
        template="simple_white"
    )
    st.plotly_chart(fig, use_container_width=True)
