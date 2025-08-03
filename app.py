import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
PATHS = {
    "A": "Planilha_242_LAT - FASEA.csv",
    "B": "Planilha_242_LAT - FASEB.csv",
    "C": "Planilha_242_LAT - FASEC.csv"
}
REFRESH_INTERVAL_MS = 500

# Atualiza a cada 0,5 segundo
st_autorefresh(interval=REFRESH_INTERVAL_MS, key="datarefresh")

# --- LAYOUT ---
st.title("Visores LAT")

# --- GRÁFICOS ---
abas = st.tabs(["Tensão (V)", "Corrente (A)", "Potência Ativa (kW)"])

# Loop por cada aba e tipo de dado
for aba, tipo_dado in zip(abas, ["tensão", "corrente", "potencia"]):
    with aba:
        dfs = {}
        for fase, path in PATHS.items():
            df = pd.read_csv(path, sep=";", encoding="latin1", decimal=",")
            df["Data"] = pd.to_datetime(df["Data"])
            df = df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))
            df["datetime"] = df["data"] + pd.to_timedelta(df["hora"])
            dfs[fase] = df

        agora = datetime.now()
        hoje = agora.date()
        ontem = hoje - timedelta(days=1)

        # --- GRÁFICO ---
        fig = go.Figure()
        for fase, df in dfs.items():
            df_filtrado = df[df["datetime"].dt.date == hoje]
            fig.add_trace(go.Scatter(
                x=df_filtrado["datetime"],
                y=df_filtrado[tipo_dado],
                mode='lines',
                name=f"Fase {fase}"
            ))

        fig.update_layout(
            xaxis_title="Tempo",
            yaxis_title=tipo_dado.capitalize(),
            height=400,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- SELETOR DE DIA ---
        opcao = st.radio(
            "Visualização",
            ["Dia Atual", "Dia Anterior"],
            horizontal=True,
            key=f"opcao_{tipo_dado}"
        )

        # Atualiza gráfico conforme opção selecionada
        fig = go.Figure()
        for fase, df in dfs.items():
            data_filtro = hoje if opcao == "Dia Atual" else ontem
            df_filtrado = df[df["datetime"].dt.date == data_filtro]
            fig.add_trace(go.Scatter(
                x=df_filtrado["datetime"],
                y=df_filtrado[tipo_dado],
                mode='lines',
                name=f"Fase {fase}"
            ))

        fig.update_layout(
            xaxis_title="Tempo",
            yaxis_title=tipo_dado.capitalize(),
            height=400,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
