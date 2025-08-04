import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta, date
import os

st.set_page_config(layout="wide")
st.title("Supervisório de Leitura de Corrente e Tensão")

# Intervalo de atualização
REFRESH_INTERVAL_MS = 100

# Inicializa controle de data atual
if "data_atual" not in st.session_state:
    st.session_state["data_atual"] = date(2025, 8, 1)
if "data_anterior" not in st.session_state:
    st.session_state["data_anterior"] = st.session_state["data_atual"] - timedelta(days=1)

# Checagem de arquivos
for fase in ["A", "B", "C"]:
    caminho = f"fase_{fase}.csv"
    if not os.path.exists(caminho):
        st.error(f"Arquivo {caminho} não encontrado.")
        st.stop()

# Carrega dados e filtra pela data atual
data_formatada = st.session_state["data_atual"].strftime("%d/%m/%Y")
dados = {}
for fase in ["A", "B", "C"]:
    df = pd.read_csv(f"fase_{fase}.csv")
    df = df[df["Data"] == data_formatada].copy()
    df.reset_index(drop=True, inplace=True)
    dados[fase] = df

    # Inicializa índice da leitura
    if f"index_{fase}" not in st.session_state:
        st.session_state[f"index_{fase}"] = 0

# Inicializa gráficos
if "valores_A" not in st.session_state:
    for fase in ["A", "B", "C"]:
        st.session_state[f"valores_{fase}"] = []
        st.session_state[f"tempos_{fase}"] = []

# Sidebar para seleção de gráfico
grafico_selecionado = st.sidebar.radio("Selecione o gráfico", ("Corrente", "Tensão"))

# Função de atualização por fase
def atualizar_dados_dia_atual(fase):
    idx = st.session_state[f"index_{fase}"]
    df = dados[fase]

    if idx < len(df):
        linha = df.iloc[idx]
        tempo = linha["Hora"]
        valor = linha["Corrente"] if grafico_selecionado == "Corrente" else linha["Tensão"]

        st.session_state[f"tempos_{fase}"].append(tempo)
        st.session_state[f"valores_{fase}"].append(valor)

        st.session_state[f"index_{fase}"] += 1
    else:
        if fase == "C":  # só muda o dia uma vez ao final
            st.session_state["data_anterior"] = st.session_state["data_atual"]
            st.session_state["data_atual"] += timedelta(days=1)
            for fase_ in ["A", "B", "C"]:
                st.session_state[f"index_{fase_}"] = 0
                st.session_state[f"valores_{fase_}"] = []
                st.session_state[f"tempos_{fase_}"] = []
            st.rerun()

# Atualiza dados
for fase in ["A", "B", "C"]:
    atualizar_dados_dia_atual(fase)

# Criação do gráfico
fig = go.Figure()
cores = {"A": "red", "B": "green", "C": "blue"}

for fase in ["A", "B", "C"]:
    fig.add_trace(go.Scatter(x=st.session_state[f"tempos_{fase}"],
                             y=st.session_state[f"valores_{fase}"],
                             mode='lines+markers',
                             name=f"Fase {fase}",
                             line=dict(color=cores[fase])))

data_str = st.session_state["data_atual"].strftime("%d/%m/%Y")
fig.update_layout(title=f"{grafico_selecionado} por Fase - {data_str}",
                  xaxis_title="Tempo (s)",
                  yaxis_title=f"{grafico_selecionado} (A/V)",
                  legend_title="Fases")

st.plotly_chart(fig, use_container_width=True)

# Atualização automática
st.experimental_rerun() if REFRESH_INTERVAL_MS > 0 else None
