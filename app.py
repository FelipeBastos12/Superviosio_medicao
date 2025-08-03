import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAÇÕES ---
PATHS = {
    "A": "Planilha_242_LAT - FASEA.csv",
    "B": "Planilha_242_LAT - FASEB.csv",
    "C": "Planilha_242_LAT - FASEC.csv"
}
REFRESH_INTERVAL_MS = 500

# --- FUNÇÕES ---
@st.cache_data(ttl=60)
def carregar_dados():
    dados = {}
    for fase, caminho in PATHS.items():
        df = pd.read_csv(caminho)
        df = df.iloc[::-1].reset_index(drop=True)
        df["Data"] = pd.to_datetime(df["Data"])
        df["Hora"] = pd.to_datetime(df["Hora"], format="%H:%M:%S").dt.time
        dados[fase] = df
    return dados

def get_ultimo_valor(df, coluna):
    return df[coluna].iloc[0]

def get_dados_para_grafico(fase, dia):
    df = dados[fase]
    if dia == "Dia Atual":
        dia_atual = df["Data"].iloc[0]
        return df[df["Data"] == dia_atual].iloc[::-1].reset_index(drop=True)
    else:
        dia_atual = df["Data"].iloc[0]
        dia_anterior = df[df["Data"] < dia_atual]["Data"].max()
        return df[df["Data"] == dia_anterior].iloc[::-1].reset_index(drop=True)

# --- AUTOREFRESH ---
st_autorefresh(interval=REFRESH_INTERVAL_MS, key="datarefresh")

# --- LAYOUT ---
st.title("Monitoramento de Medições Elétricas LAT - 242")

dados = carregar_dados()

col1, col2, col3 = st.columns(3)
for i, fase in enumerate(["A", "B", "C"]):
    with [col1, col2, col3][i]:
        st.markdown(f"### Fase {fase}")
        tensao = get_ultimo_valor(dados[fase], "tensao")
        corrente = get_ultimo_valor(dados[fase], "corrente")
        potencia = get_ultimo_valor(dados[fase], "potencia")
        st.metric(label="Tensão (V)", value=f"{tensao:.1f}")
        st.metric(label="Corrente (A)", value=f"{corrente:.1f}")
        st.metric(label="Potência Ativa (W)", value=f"{potencia:.1f}")

st.markdown("---")

grafico_selecionado = st.selectbox("Selecionar gráfico para visualização:", ("Tensão", "Corrente", "Potência Ativa"))

col_grafico = st.container()

with col_grafico:
    dia_escolhido = st.radio("Selecionar dia para visualização do gráfico:", ("Dia Atual", "Dia Anterior"))

    dados_grafico = {fase: get_dados_para_grafico(fase, dia_escolhido) for fase in ["A", "B", "C"]}

    fig = go.Figure()
    cores = {"A": "#2980b9", "B": "#e67e22", "C": "#27ae60"}

    chave_grafico = {
        "Tensão": "tensao",
        "Corrente": "corrente",
        "Potência Ativa": "potencia"
    }

    for fase in ["A", "B", "C"]:
        dados = dados_grafico[fase]
        chave = chave_grafico[grafico_selecionado]
        modo = 'lines+markers' if dia_escolhido == "Dia Atual" else 'lines'
        fig.add_trace(go.Scatter(
            y=dados[chave],
            mode=modo,
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))

    fig.update_layout(
        title=f"{grafico_selecionado} nas Fases",
        yaxis_title=f"{grafico_selecionado} ({'V' if grafico_selecionado == 'Tensão' else 'A' if grafico_selecionado == 'Corrente' else 'W'})",
        xaxis_title="Amostras",
        yaxis=dict(range=[0, 500] if grafico_selecionado == "Tensão" else None),
        height=450,
        template="simple_white"
    )
    st.plotly_chart(fig, use_container_width=True)
