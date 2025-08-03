import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAÇÕES ---
PATHS = {
    "A": "Planilha_242_LAT - FASEA.csv",
    "B": "Planilha_242_LAT - FASEB.csv",
    "C": "Planilha_242_LAT - FASEC.csv"
}

# --- LEITURA DOS DADOS ---
dfs = {}
for fase, path in PATHS.items():
    df = pd.read_csv(path)
    df["DataCompleta"] = pd.to_datetime(df["Data"] + " " + df["Horário"], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    df = df.dropna(subset=["DataCompleta"])
    df["Hora"] = df["DataCompleta"].dt.strftime("%H:%M:%S")
    dfs[fase] = df

# --- INTERFACE ---
st.set_page_config(layout="wide")
st.title("Supervisão de Medições Elétricas")

dia = st.radio("Selecione o dia", ["Dia atual", "Dia anterior"], horizontal=True)

if dia == "Dia atual":
    st_autorefresh(interval=60000, key="atualiza")  # Atualiza a cada 60s
    for i, (fase, df) in enumerate(dfs.items()):
        col = st.columns(2)[i % 2]

        with col:
            ultima = df.iloc[-1]
            tensao = ultima.filter(like="Tensao").values[0]
            corrente = ultima.filter(like="Corrente").values[0]
            potencia = ultima.filter(like="Potencia_Ativa").values[0]

            st.markdown(f"### Fase {fase}")
            st.metric("Tensão (V)", f"{tensao:.1f}")
            st.metric("Corrente (A)", f"{corrente:.1f}")
            st.metric("Potência Ativa (W)", f"{potencia:.1f}")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Hora"].tail(20), y=df.filter(like="Tensao").iloc[:, 0].tail(20),
                                     mode="lines+markers", name="Tensão"))
            fig.update_layout(title=f"Tensão - Fase {fase}", xaxis_title="Hora", yaxis_title="Tensão (V)")
            st.plotly_chart(fig, use_container_width=True)

else:  # Dia anterior
    for i, (fase, df) in enumerate(dfs.items()):
        col = st.columns(2)[i % 2]

        with col:
            st.markdown(f"### Fase {fase} - Dia Anterior")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Hora"], y=df.filter(like="Tensao").iloc[:, 0], mode="lines", name="Tensão"))
            fig.update_layout(title=f"Tensão - Fase {fase}", xaxis_title="Hora", yaxis_title="Tensão (V)")
            st.plotly_chart(fig, use_container_width=True)
