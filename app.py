import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- CONFIGURAÇÕES ---
PATHS = {
    "A": "Planilha_242_LAT - FASEA.csv",
    "B": "Planilha_242_LAT - FASEB.csv",
    "C": "Planilha_242_LAT - FASEC.csv"
}
REFRESH_INTERVAL_MS = 500
# ---

# --- ATUALIZAÇÃO AUTOMÁTICA ---
st_autorefresh(interval=REFRESH_INTERVAL_MS, key="refresh")

# --- TÍTULO ---
st.title("Monitoramento de Tensões e Correntes")

# --- SELEÇÃO DE FASE ---
fase = st.selectbox("Selecione a fase", options=["A", "B", "C"], index=0)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=1)
def carregar_dados(path):
    try:
        df = pd.read_csv(path, sep=";")
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y %H:%M:%S")
        df = df.sort_values("Data")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados(PATHS[fase])

if df.empty:
    st.stop()

# --- SELEÇÃO DE VARIÁVEL A SER EXIBIDA ---
opcoes_grafico = {
    "Tensão": ["V_AB", "V_BC", "V_CA"],
    "Corrente": ["I_A", "I_B", "I_C"],
    "Potência Ativa": ["P_A", "P_B", "P_C"]
}
grafico_selecionado = st.selectbox("Selecione a variável", list(opcoes_grafico.keys()))

# --- FILTRAGEM DE DADOS (com base na hora atual) ---
agora = datetime.now()
data_atual = agora.date()
data_ontem = data_atual - pd.Timedelta(days=1)

dados_dia_atual = df[df["Data"].dt.date == data_atual]
dados_dia_anterior = df[df["Data"].dt.date == data_ontem]

# --- PLOTAGEM ---
fig = go.Figure()

cores = {"A": "orange", "B": "blue", "C": "green"}
variaveis = opcoes_grafico[grafico_selecionado]

for var in variaveis:
    if grafico_selecionado == "Tensão":
        nome_legenda = f"{var}"
    elif grafico_selecionado == "Corrente":
        nome_legenda = f"{var}"
    else:
        nome_legenda = f"{var}"

    fig.add_trace(go.Scatter(
        x=dados_dia_atual["Data"],
        y=dados_dia_atual[var],
        mode="lines",
        name=nome_legenda,
        line=dict(color=cores.get(var[-1], "black"))
    ))

fig.update_layout(
    title=f"{grafico_selecionado} - Fase {fase}",
    xaxis_title="Horário",
    yaxis_title=grafico_selecionado,
    height=500,
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- SELETOR DE DIA (AGORA ABAIXO DO GRÁFICO) ---
dia_escolhido = st.radio("Selecionar dia para visualização:", ("Dia Atual", "Dia Anterior"), horizontal=True)
