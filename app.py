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

# --- NOMES DAS COLUNAS POR FASE ---
colunas = {
    "A": {
        "tensao": "Tensao_Fase_ A",
        "corrente": "Corrente_Fase_A",
        "potencia": "Potencia_Ativa_Fase_A",
        "frequencia": "Frequencia_Fase_A"
    },
    "B": {
        "tensao": "Tensao_Fase_ B",
        "corrente": "Corrente_Fase_B",
        "potencia": "Potencia_Ativa_Fase_B",
        "frequencia": "Frequencia_Fase_B"
    },
    "C": {
        "tensao": "Tensao_Fase_C",
        "corrente": "Corrente_Fase_C",
        "potencia": "Potencia_Ativa_Fase_C",
        "frequencia": "Frequencia_Fase_C"
    }
}

# --- LEITURA E LIMPEZA ---
@st.cache_data
def load_and_clean_csv(path):
    df = pd.read_csv(path)
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
        try:
            df[col] = df[col].astype(float)
        except ValueError:
            pass
    return df

dfs = {fase: load_and_clean_csv(path) for fase, path in PATHS.items()}

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Supervisório LAT Trifásico", layout="wide")

col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("FDJ_engenharia.jpg", width=500)
with col_titulo:
    st.markdown("<h1 style='padding-top: 90px;'>Supervisório de Medição Elétrica</h1>", unsafe_allow_html=True)

# --- SELETOR DE DIA ---
modo = st.radio("Selecione o dia:", ["Tempo real", "Dia anterior"], horizontal=True)

if modo == "Tempo real":
    st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

    for fase in ["A", "B", "C"]:
        if f"index_{fase}" not in st.session_state:
            st.session_state[f"index_{fase}"] = 0
        if f"valores_{fase}" not in st.session_state:
            st.session_state[f"valores_{fase}"] = {
                "tensao": [], "corrente": [], "potencia": []
            }

    for fase in ["A", "B", "C"]:
        df = dfs[fase]
        idx = st.session_state[f"index_{fase}"]
        if idx >= len(df):
            st.session_state[f"index_{fase}"] = 0
            idx = 0
            st.success(f"Reiniciando dados da fase {fase}")
        row = df.iloc[idx]
        st.session_state[f"index_{fase}"] += 1

        tensao = row.get(colunas[fase]["tensao"], None)
        corrente = row.get(colunas[fase]["corrente"], None)
        potencia = row.get(colunas[fase]["potencia"], None)
        frequencia = row.get(colunas[fase]["frequencia"], None)

        if corrente == 0:
            corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
        else:
            st.session_state[f"corrente_anterior_{fase}"] = corrente

        if tensao is not None:
            st.session_state[f"valores_{fase}"]["tensao"].append(float(tensao))
            st.session_state[f"valores_{fase}"]["tensao"] = st.session_state[f"valores_{fase}"]["tensao"][-50:]
        if corrente is not None:
            st.session_state[f"valores_{fase}"]["corrente"].append(float(corrente))
            st.session_state[f"valores_{fase}"]["corrente"] = st.session_state[f"valores_{fase}"]["corrente"][-50:]
        if potencia is not None:
            st.session_state[f"valores_{fase}"]["potencia"].append(float(potencia))
            st.session_state[f"valores_{fase}"]["potencia"] = st.session_state[f"valores_{fase}"]["potencia"][-50:]

    valores_tensao = {}
    valores_corrente = {}
    valores_potencia = {}
    valores_frequencia = {}

    for fase in ["A", "B", "C"]:
        df = dfs[fase]
        idx = st.session_state[f"index_{fase}"] - 1
        idx = max(idx, 0)
        row = df.iloc[idx]
        valores_tensao[fase] = float(row.get(colunas[fase]["tensao"], 0))
        valores_corrente[fase] = float(row.get(colunas[fase]["corrente"], 0))
        valores_potencia[fase] = float(row.get(colunas[fase]["potencia"], 0))
        valores_frequencia[fase] = float(row.get(colunas[fase]["frequencia"], 0))

    def visor_fases(label, valores_por_fase, unidade, cor_fundo="#2c3e50"):
        cores_texto = {
            "A": "#2ecc71" if (label == "Tensão" and valores_por_fase["A"] >= 210) or label != "Tensão" else "#c0392b",
            "B": "#2ecc71" if (label == "Tensão" and valores_por_fase["B"] >= 210) or label != "Tensão" else "#c0392b",
            "C": "#2ecc71" if (label == "Tensão" and valores_por_fase["C"] >= 210) or label != "Tensão" else "#c0392b",
        }
        st.markdown(f"""<div style='background-color: {cor_fundo}; padding: 15px; border-radius: 15px; margin-bottom: 15px;'>
            <h3 style='color:white; text-align:center;'>{label}</h3>
            <div style='display: flex; flex-direction: column; gap: 10px;'>""" +
            "".join([
                f"""<div style='background-color: #34495e; color: {cores_texto[fase]}; padding: 15px; border-radius: 10px;
                text-align: center; font-size: 20px; font-weight: bold;'>Fase {fase}: {valores_por_fase[fase]:.2f} {unidade}</div>"""
                for fase in ["A", "B", "C"]
            ]) + "</div></div>", unsafe_allow_html=True)

    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    with row1_col1:
        visor_fases("Tensão", valores_tensao, "V")
    with row1_col2:
        visor_fases("Corrente", valores_corrente, "A")
    with row2_col1:
        visor_fases("Potência Ativa", valores_potencia, "W")
    with row2_col2:
        visor_fases("Frequência", valores_frequencia, "Hz")

    grafico_selecionado = st.radio("", ("Tensão", "Corrente", "Potência Ativa"))
    fig = go.Figure()
    cores = {"A": "#2980b9", "B": "#e67e22", "C": "#27ae60"}

    for fase in ["A", "B", "C"]:
        dados = st.session_state[f"valores_{fase}"]
        y = dados[grafico_selecionado.lower().replace(" ", "")]
        fig.add_trace(go.Scatter(y=y, mode='lines+markers', name=f"Fase {fase}", line=dict(color=cores[fase])))

    fig.update_layout(title=f"{grafico_selecionado} nas Fases", yaxis_title=grafico_selecionado, xaxis_title="Amostras", height=450)
    st.plotly_chart(fig, use_container_width=True)

elif modo == "Dia anterior":
    st.subheader("Visualização do dia anterior (gráfico por hora)")
    grafico_selecionado = st.radio("Selecione o gráfico:", ("Tensão", "Corrente", "Potência Ativa"))

    fig = go.Figure()
    cores = {"A": "#2980b9", "B": "#e67e22", "C": "#27ae60"}

    for fase in ["A", "B", "C"]:
        df = dfs[fase].copy()
        df["Data"] = pd.to_datetime(df["Data"], errors='coerce').dt.date
        df["Hora"] = df["Horário"].astype(str)
        df = df[df["Data"] == ontem]  # só o dia anterior

        if df.empty:
            continue

        y = df[colunas[fase][grafico_selecionado.lower().replace(" ", "")]]
        fig.add_trace(go.Scatter(x=df["Hora"], y=y, mode='lines+markers', name=f"Fase {fase}", line=dict(color=cores[fase])))

    fig.update_layout(title=f"{grafico_selecionado} no dia {ontem}", xaxis_title="Hora", yaxis_title=grafico_selecionado, height=500)
    st.plotly_chart(fig, use_container_width=True)
