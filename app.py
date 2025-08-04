import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta, date
import time

st.set_page_config(layout="wide")

# Configurações
REFRESH_INTERVAL_MS = 100

# Inicializa estados
if "data_atual" not in st.session_state:
    st.session_state["data_atual"] = date(2025, 8, 1)
if "data_anterior" not in st.session_state:
    st.session_state["data_anterior"] = st.session_state["data_atual"] - timedelta(days=1)

for fase in ["A", "B", "C"]:
    if f"df_{fase}" not in st.session_state:
        df = pd.read_csv(f"fase_{fase}.csv")
        df = df[df["Data"] == st.session_state["data_atual"].strftime("%d/%m/%Y")].copy()
        df["Timestamp"] = pd.to_datetime(df["Data"] + ' ' + df["Hora"])
        st.session_state[f"df_{fase}"] = df
    if f"index_{fase}" not in st.session_state:
        st.session_state[f"index_{fase}"] = 0

# Função para atualizar os dados

def atualizar_dados_dia_atual(fase):
    df = st.session_state[f"df_{fase}"]
    index = st.session_state[f"index_{fase}"]

    if index >= len(df):
        if fase == "C":
            st.session_state["data_anterior"] = st.session_state["data_atual"]
            st.session_state["data_atual"] += timedelta(days=1)
            for f in ["A", "B", "C"]:
                st.session_state[f"index_{f}"] = 0
                df_novo = pd.read_csv(f"fase_{f}.csv")
                df_novo = df_novo[df_novo["Data"] == st.session_state["data_atual"].strftime("%d/%m/%Y")].copy()
                df_novo["Timestamp"] = pd.to_datetime(df_novo["Data"] + ' ' + df_novo["Hora"])
                st.session_state[f"df_{f}"] = df_novo
            st.rerun()
        return pd.DataFrame()

    st.session_state[f"index_{fase}"] += 1
    return df.iloc[:st.session_state[f"index_{fase}"]]

# Sidebar
st.sidebar.title("Configurações")
grafico_selecionado = st.sidebar.selectbox("Selecione o gráfico:", ["Corrente", "Tensão"])

# Layout
col1, col2 = st.columns(2)

for fase, col in zip(["A", "B", "C"], [col1, col2, st]):
    dados = atualizar_dados_dia_atual(fase)

    if dados.empty:
        continue

    fig = go.Figure()
    if grafico_selecionado == "Corrente":
        fig.add_trace(go.Scatter(x=dados["Timestamp"], y=dados["Corrente"], mode="lines", name=f"Fase {fase}"))
        fig.update_yaxes(title_text="Corrente (A)")
    else:
        fig.add_trace(go.Scatter(x=dados["Timestamp"], y=dados["Tensao"], mode="lines", name=f"Fase {fase}"))
        fig.update_yaxes(title_text="Tensão (V)")

    fig.update_layout(
        title=f"{grafico_selecionado} - Fase {fase} - Data: {st.session_state['data_atual'].strftime('%d/%m/%Y')}",
        xaxis_title="Tempo",
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    col.plotly_chart(fig, use_container_width=True)

# Alarme
st.markdown("---")
colA, colB = st.columns(2)
colA.metric("Data Atual", st.session_state["data_atual"].strftime("%d/%m/%Y"))
colB.metric("Data Anterior", st.session_state["data_anterior"].strftime("%d/%m/%Y"))

# Auto refresh
st.experimental_rerun() if REFRESH_INTERVAL_MS else time.sleep(0.1)
