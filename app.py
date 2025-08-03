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
DATA_FIXA = pd.to_datetime("2025-05-23").date()  # <<< ALTERE AQUI CASO MUDE A DATA

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
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")
        df["Horario"] = pd.to_datetime(df["Horario"], format="%H:%M:%S").dt.time
        df["DataHora"] = df.apply(lambda row: datetime.combine(row["Data"].date(), row["Horario"]), axis=1)
        df = df.sort_values("DataHora")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados(PATHS[fase])

if df.empty:
    st.stop()

# --- FILTRA APENAS O DIA 23/05/2025 ---
df_filtrado = df[df["Data"].dt.date == DATA_FIXA]

if df_filtrado.empty:
    st.warning(f"Sem dados para {DATA_FIXA.strftime('%d/%m/%Y')}")
    st.stop()

# --- SELEÇÃO DE VARIÁVEL A SER EXIBIDA ---
opcoes_grafico = {
    "Tensão": ["Tensao_Fase_A", "Tensao_Fase_B", "Tensao_Fase_C"],
    "Corrente": ["Corrente_Fase_A", "Corrente_Fase_B", "Corrente_Fase_C"],
    "Potência Ativa": ["Potencia_Ativa_Fase_A", "Potencia_Ativa_Fase_B", "Potencia_Ativa_Fase_C"]
}
grafico_selecionado = st.selectbox("Selecione a variável", list(opcoes_grafico.keys()))

# --- PLOTAGEM ---
fig = go.Figure()
cores = {"A": "orange", "B": "blue", "C": "green"}
variaveis = opcoes_grafico[grafico_selecionado]

for var in variaveis:
    nome_fase = var.split("_")[-1]  # extrai A, B ou C do nome da coluna
    fig.add_trace(go.Scatter(
        x=df_filtrado["DataHora"],
        y=df_filtrado[var],
        mode="lines",
        name=f"{var}",
        line=dict(color=cores.get(nome_fase, "black"))
    ))

fig.update_layout(
    title=f"{grafico_selecionado} - Fase {fase} - {DATA_FIXA.strftime('%d/%m/%Y')}",
    xaxis_title="Horário",
    yaxis_title=grafico_selecionado,
    height=500,
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- SELETOR DE DIA (opcional, agora fixo) ---
st.info(f"Exibindo dados do dia: {DATA_FIXA.strftime('%d/%m/%Y')}")
