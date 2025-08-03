import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAÇÕES ---
st.set_page_config(layout="wide")
st.title("Supervisão de Medições Elétricas")

# --- CARREGAMENTO DA IMAGEM DE TOPO ---
st.image("06cbe711-95b6-496a-904a-c3ca92eefff9.png", use_column_width=True)

# --- FUNÇÕES DE LEITURA ---
@st.cache_data
def carregar_dados():
    fases = ["A", "B", "C"]
    dfs = {}
    for fase in fases:
        df = pd.read_csv(f"Planilha_242_LAT - FASE{fase}.csv")
        df["Data"] = pd.to_datetime(df["Data"], errors='coerce').dt.date
        df["Horário"] = pd.to_datetime(df["Horário"], errors='coerce').dt.time
        df["Hora"] = pd.to_datetime(df["Horário"], format="%H:%M:%S", errors="coerce").apply(lambda x: x.strftime("%H:%M:%S") if pd.notnull(x) else "")
        dfs[fase] = df
    return dfs

dfs = carregar_dados()

# --- PARÂMETROS DE INTERFACE ---
modo = st.radio("Selecione o modo de exibição:", ["Tempo real (Dia atual)", "Dia anterior"], horizontal=True)

# --- CONFIGURAÇÃO DE TEMPO ---
hoje = datetime.now().date()
ontem = hoje - timedelta(days=1)

# --- LOOP PRINCIPAL ---
colunas = {
    "Tensão [V]": ["Tensao_Fase_ A", "Tensao_Fase_ B", "Tensao_Fase_C"],
    "Corrente [A]": ["Corrente_Fase_A", "Corrente_Fase_B", "Corrente_Fase_C"],
    "Potência Ativa [W]": ["Potencia_Ativa_Fase_A", "Potencia_Ativa_Fase_B", "Potencia_Ativa_Fase_C"],
    "Fator de Potência": ["fator_De_Potencia_Fase_A", "fator_De_Potencia_Fase_B", "fator_De_Potencia_Fase_C"]
}

# --- SELEÇÃO DE TEMPO ---
if modo == "Tempo real (Dia atual)":
    st_autorefresh(interval=5000, limit=100000, key="datarefresh")
    tempo_real = True
else:
    tempo_real = False

# --- VISUALIZAÇÃO EM 2x2 ---
graficos = list(colunas.keys())

row1 = st.columns(2)
row2 = st.columns(2)

for idx, (titulo, colunas_fase) in enumerate(colunas.items()):
    dataframes_plot = []
    for i, fase in enumerate(["A", "B", "C"]):
        df = dfs[fase].copy()
        if tempo_real:
            df = df[df["Data"] == hoje]
            x = df["Hora"]
        else:
            df = df[df["Data"] == ontem]
            x = df["Horário"].astype(str)

        y = df[colunas_fase[i]] if colunas_fase[i] in df.columns else None
        if y is not None:
            trace = go.Scatter(x=x, y=y, name=f"Fase {fase}", mode='lines')
            dataframes_plot.append(trace)

    layout = go.Layout(title=titulo, xaxis=dict(title="Hora"), yaxis=dict(title=titulo), height=350)
    fig = go.Figure(data=dataframes_plot, layout=layout)

    if idx < 2:
        row1[idx].plotly_chart(fig, use_container_width=True)
    else:
        row2[idx - 2].plotly_chart(fig, use_container_width=True)
