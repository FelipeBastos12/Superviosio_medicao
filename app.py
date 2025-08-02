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

# --- AUTOREFRESH ---
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- INICIALIZAÇÃO DE SESSION STATE ---
for fase in ["A", "B", "C"]:
    if f"index_{fase}" not in st.session_state:
        st.session_state[f"index_{fase}"] = 0
    if f"valores_{fase}" not in st.session_state:
        st.session_state[f"valores_{fase}"] = {
            "tensao": [], "corrente": [], "potencia": []
        }

# --- FUNÇÃO DE VISOR ---
def visor(valor, label, cor_fundo, cor_texto):
    st.markdown(f"""
    <div style='
        background-color: {cor_fundo};
        color: {cor_texto};
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    '>
        {label}: {valor}
    </div>
    """, unsafe_allow_html=True)

# --- MOSTRA INFORMAÇÕES DE CADA FASE ---
for fase in ["A", "B", "C"]:
    df = dfs[fase]
    idx = st.session_state[f"index_{fase}"]
    if idx >= len(df):
        st.session_state[f"index_{fase}"] = 0
        idx = 0
        st.success(f"Reiniciando dados da fase {fase}")
    row = df.iloc[idx]
    st.session_state[f"index_{fase}"] += 1

    # Extrai variáveis
    tensao = row.get(f"Tensao_Fase_ {fase}", None)
    corrente = row.get(f"Corrente_Fase_{fase}", None)
    potencia_ativa = row.get(f"Potencia_Ativa_Fase_{fase}", None)
    frequencia = row.get(f"Frequencia_Fase_{fase}", None)

    # Corrente zero → mantém anterior
    if corrente == 0:
        corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
    else:
        st.session_state[f"corrente_anterior_{fase}"] = corrente

    # Guarda valores para gráficos
    if tensao is not None:
        st.session_state[f"valores_{fase}"]["tensao"].append(float(tensao))
        st.session_state[f"valores_{fase}"]["tensao"] = st.session_state[f"valores_{fase}"]["tensao"][-50:]
    if corrente is not None:
        st.session_state[f"valores_{fase}"]["corrente"].append(float(corrente))
        st.session_state[f"valores_{fase}"]["corrente"] = st.session_state[f"valores_{fase}"]["corrente"][-50:]
    if potencia_ativa is not None:
        st.session_state[f"valores_{fase}"]["potencia"].append(float(potencia_ativa))
        st.session_state[f"valores_{fase}"]["potencia"] = st.session_state[f"valores_{fase}"]["potencia"][-50:]

# --- VISUALIZAÇÃO EM COLUNAS ---
col_a, col_b, col_c = st.columns(3)

for col, fase in zip([col_a, col_b, col_c], ["A", "B", "C"]):
    with col:
        st.subheader(f"Fase {fase}")
        dados = st.session_state[f"valores_{fase}"]
        idx = st.session_state[f"index_{fase}"] - 1
        row = dfs[fase].iloc[idx]

        tensao = row.get(f"Tensao_Fase_ {fase}", None)
        corrente = row.get(f"Corrente_Fase_{fase}", None)
        potencia_ativa = row.get(f"Potencia_Ativa_Fase_{fase}", None)
        frequencia = row.get(f"Frequencia_Fase_{fase}", None)

        if tensao is not None:
            tensao = float(tensao)
            visor(f"{tensao:.1f} V", "Tensão", "#2c3e50", "#2ecc71" if tensao >= 210 else "#c0392b")

        if corrente is not None:
            corrente = float(corrente)
            visor(f"{corrente:.1f} A", "Corrente", "#2c3e50", "#2ecc71")

        if potencia_ativa is not None:
            potencia = float(potencia_ativa)
            visor(f"{potencia:.2f} W", "Potência Ativa", "#2c3e50", "#2ecc71")

        if frequencia is not None:
            frequencia = float(frequencia)
            visor(f"{frequencia:.2f} Hz", "Frequência", "#2c3e50", "#2ecc71")

# --- GRÁFICOS ---
grafico_selecionado = st.radio("Selecione o gráfico a ser exibido", ("Tensão", "Corrente", "Potência Ativa"))

fig = go.Figure()
cores = {"A": "#2980b9", "B": "#e67e22", "C": "#27ae60"}
for fase in ["A", "B", "C"]:
    valores = st.session_state[f"valores_{fase}"]
    if grafico_selecionado == "Tensão":
        fig.add_trace(go.Scatter(
            y=valores["tensao"],
            mode='lines+markers',
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))
        fig.update_layout(title="Tensão Fase (V)", yaxis_title="Tensão (V)")
    elif grafico_selecionado == "Corrente":
        fig.add_trace(go.Scatter(
            y=valores["corrente"],
            mode='lines+markers',
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))
        fig.update_layout(title="Corrente Fase (A)", yaxis_title="Corrente (A)")
    elif grafico_selecionado == "Potência Ativa":
        fig.add_trace(go.Scatter(
            y=valores["potencia"],
            mode='lines+markers',
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))
        fig.update_layout(title="Potência Ativa (W)", yaxis_title="Potência Ativa (W)")

fig.update_layout(
    xaxis_title="Amostras",
    height=450,
    template="simple_white"
)
st.plotly_chart(fig, use_container_width=True)
