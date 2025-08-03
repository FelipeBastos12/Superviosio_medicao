import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Supervisório LAT Trifásico", layout="wide")

# Layout com logo e título
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("6530_-_Eletrica_-_GRUPOS.jpg", width=130)
with col_titulo:
    st.markdown("<h1 style='padding-top: 20px;'>Supervisório de Medição Elétrica</h1>", unsafe_allow_html=True)

# --- CAMINHOS DOS ARQUIVOS ---
PATHS = {
    "A": "Planilha_242_LAT - FASEA.csv",
    "B": "Planilha_242_LAT - FASEB.csv",
    "C": "Planilha_242_LAT - FASEC.csv"
}

# --- SELEÇÃO DE DIA ---
dia_selecionado = st.radio("Selecionar dia:", ["Dia Atual", "Dia Anterior"], horizontal=True)

# --- REFRESH AUTOMÁTICO SE DIA ATUAL ---
if dia_selecionado == "Dia Atual":
    st_autorefresh(interval=5000, key="datarefresh")

# --- LEITURA DOS DADOS ---
dfs = {}
for fase, path in PATHS.items():
    dfs[fase] = pd.read_csv(path)
    dfs[fase]["Hora"] = pd.to_datetime(dfs[fase]["Data/Hora"]).dt.strftime("%H:%M:%S")

# --- DADOS DO DIA SELECIONADO ---
if dia_selecionado == "Dia Atual":
    for fase in dfs:
        dfs[fase] = dfs[fase].tail(1)
else:
    for fase in dfs:
        dfs[fase]["Hora"] = pd.to_datetime(dfs[fase]["Data/Hora"]).dt.strftime("%H:%M")

# --- OBTÉM VALORES ATUAIS (SE DIA ATUAL) ---
valores_atuais = {}
if dia_selecionado == "Dia Atual":
    for fase in dfs:
        linha = dfs[fase].iloc[0]
        valores_atuais[fase] = {
            "Tensão": linha["Tensão [V]"],
            "Corrente": linha["Corrente [A]"],
            "Potência": linha["Potência Ativa [W]"],
            "FP": linha["Fator de Potência"]
        }

# --- FUNÇÃO PARA CRIAR BLOCOS DE INFORMAÇÃO ---
def bloco_info(titulo, valores, unidade):
    fases = ["A", "B", "C"]
    cores = ["#d35400", "#2980b9", "#16a085"]
    traces = []
    for i, fase in enumerate(fases):
        if dia_selecionado == "Dia Atual":
            valor = valores[fase]
            traces.append(go.Indicator(
                mode="number",
                value=valor,
                title={"text": f"Fase {fase}"},
                domain={"row": 0, "column": i},
                number={"suffix": f" {unidade}"},
            ))
        else:
            traces.append(go.Scatter(
                x=dfs[fase]["Hora"],
                y=dfs[fase][titulo + " [" + unidade + "]"],
                mode="lines",
                name=f"Fase {fase}",
                line=dict(color=cores[i])
            ))

    if dia_selecionado == "Dia Atual":
        fig = go.Figure(traces)
        fig.update_layout(grid={"rows": 1, "columns": 3}, height=150, margin=dict(t=20, b=20))
    else:
        fig = go.Figure(traces)
        fig.update_layout(title=titulo, xaxis_title="Hora", yaxis_title=f"{titulo} [{unidade}]")

    return fig

# --- LAYOUT DOS GRÁFICOS EM 2x2 ---
col1, col2 = st.columns(2)
with col1:
    if dia_selecionado == "Dia Atual":
        tensoes = {f: valores_atuais[f]["Tensão"] for f in PATHS}
    fig_tensao = bloco_info("Tensão", tensoes, "V")
    st.plotly_chart(fig_tensao, use_container_width=True)

with col2:
    if dia_selecionado == "Dia Atual":
        correntes = {f: valores_atuais[f]["Corrente"] for f in PATHS}
    fig_corrente = bloco_info("Corrente", correntes, "A")
    st.plotly_chart(fig_corrente, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    if dia_selecionado == "Dia Atual":
        potencias = {f: valores_atuais[f]["Potência"] for f in PATHS}
    fig_potencia = bloco_info("Potência Ativa", potencias, "W")
    st.plotly_chart(fig_potencia, use_container_width=True)

with col4:
    if dia_selecionado == "Dia Atual":
        fps = {f: valores_atuais[f]["FP"] for f in PATHS}
    fig_fp = bloco_info("Fator de Potência", fps, "")
    st.plotly_chart(fig_fp, use_container_width=True)
