import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAÇÕES ---
CSV_PATH = "Planilha_242_LAT - FASEA.csv"
REFRESH_INTERVAL_MS = 500  # milissegundos para o st_autorefresh

# --- LEITURA E LIMPEZA DO CSV ---
@st.cache_data
def load_and_clean_csv(path):
    df = pd.read_csv(path, sep=",", decimal=",")
    df['DataHora'] = pd.to_datetime(df['Data'] + " " + df['Horário'], dayfirst=True)
    return df

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Supervisório LAT", layout="wide")

# --- CARREGA OS DADOS ---
df = load_and_clean_csv(CSV_PATH)

# --- CONTROLE DO INDEX COM SESSION STATE ---
if "index" not in st.session_state:
    st.session_state.index = 0

# --- AUTOREFRESH A CADA 0.5 SEGUNDOS ---
count = st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- LÊ A LINHA ATUAL ---
if st.session_state.index >= len(df):
    st.session_state.index = 0  # Reinicia a leitura
    st.success("Reiniciando a leitura dos dados.")

row = df.iloc[st.session_state.index]
st.session_state.index += 1

# --- EXTRAI OS VALORES ---
tensao = row.get("Tensao_Fase_A", None)
frequencia = row.get("Frequencia_Fase_A", None)
corrente = row.get("Corrente_Fase_A", None)

# --- SUBSTITUI VALORES ZERO NA CORRENTE PELO VALOR ANTERIOR ---
if corrente == 0:
    corrente = st.session_state.get("corrente_anterior", corrente)
else:
    st.session_state["corrente_anterior"] = corrente

# --- EXIBE OS VISUAIS ---
col1, col2, col3 = st.columns(3)

with col1:
    if tensao is not None:
        tensao_valor = float(tensao)
        cor_fundo = "#c0392b" if tensao_valor < 210 else "#2c3e50"
        cor_texto = "#ffffff" if tensao_valor < 210 else "#2ecc71"
        st.markdown(f"<div style='background-color: {cor_fundo}; color: {cor_texto}; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold;'>V: {tensao_valor:.1f} V</div>", unsafe_allow_html=True)

with col2:
    if frequencia is not None:
        freq_valor = float(frequencia)
        st.markdown(f"<div style='background-color: #2c3e50; color: #2ecc71; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold;'>F: {freq_valor:.1f} Hz</div>", unsafe_allow_html=True)

with col3:
    if corrente is not None:
        corrente_valor = float(corrente)
        st.markdown(f"<div style='background-color: #2c3e50; color: #2ecc71; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold;'>I: {corrente_valor:.1f} A</div>", unsafe_allow_html=True)

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
