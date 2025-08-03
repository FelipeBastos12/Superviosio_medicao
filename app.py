import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from PIL import Image
import os

# --- CONFIGURAÇÕES ---
PATHS = {
    "A": "Planilha_242_LAT - FASEA.csv",
    "B": "Planilha_242_LAT - FASEB.csv",
    "C": "Planilha_242_LAT - FASEC.csv"
}

# --- TÍTULO E IMAGEM ---
st.set_page_config(layout="wide")
image = Image.open("6530_-_Eletrica_-_GRUPOS.jpg")
st.image(image, use_column_width=True)

st.title("Supervisão Elétrica - Medições LAT")
fase = st.selectbox("Selecione a fase:", ["A", "B", "C"])
tipo_visualizacao = st.radio("Mostrar:", ["Dia atual (tempo real)", "Dia anterior (completo)"])

# --- CARREGAR DADOS ---
dfs = {}
for key, path in PATHS.items():
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()  # Remove espaços extras
    if "Data/Hora" not in df.columns:
        st.error(f"A planilha da fase {key} não contém a coluna 'Data/Hora'. Colunas disponíveis: {df.columns.tolist()}")
        st.stop()
    df["Data/Hora"] = pd.to_datetime(df["Data/Hora"])
    df["Hora"] = df["Data/Hora"].dt.strftime("%H:%M:%S")
    dfs[key] = df

df_fase = dfs[fase]

# --- PLOT ---
if tipo_visualizacao == "Dia anterior (completo)":
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_fase["Hora"], y=df_fase["Tensão (V)"], name="Tensão (V)", line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df_fase["Hora"], y=df_fase["Corrente (A)"], name="Corrente (A)", line=dict(color='blue')))
    fig.update_layout(title=f"Gráfico completo do dia anterior - Fase {fase}",
                      xaxis_title="Hora",
                      yaxis_title="Valor",
                      xaxis=dict(tickangle=45),
                      height=500)
    st.plotly_chart(fig, use_container_width=True)

else:
    # DIA ATUAL (TEMPO REAL)
    st_autorefresh(interval=5000, key="refresh")

    if "index" not in st.session_state:
        st.session_state["index"] = 1

    idx = st.session_state["index"]
    df_parcial = df_fase.iloc[:idx]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_parcial["Hora"], y=df_parcial["Tensão (V)"], name="Tensão (V)", line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df_parcial["Hora"], y=df_parcial["Corrente (A)"], name="Corrente (A)", line=dict(color='blue')))
    fig.update_layout(title=f"Monitoramento em tempo real - Fase {fase}",
                      xaxis_title="Hora",
                      yaxis_title="Valor",
                      xaxis=dict(tickangle=45),
                      height=500)
    st.plotly_chart(fig, use_container_width=True)

    if idx < len(df_fase):
        st.session_state["index"] += 1
