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

# --- SELETOR DE DIA (AFETA SÓ O GRÁFICO) ---
dia_escolhido = st.radio("Selecionar dia para visualização do gráfico:", ("Dia Atual", "Dia Anterior"))

# --- AUTOREFRESH SEMPRE RODANDO PARA LEITURAS DOS VISORES ---
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- INICIALIZAÇÃO DO SESSION STATE ---
for fase in ["A", "B", "C"]:
    if f"index_{fase}" not in st.session_state:
        st.session_state[f"index_{fase}"] = 0
    if f"valores_{fase}" not in st.session_state:
        st.session_state[f"valores_{fase}"] = {"tensao": [], "corrente": [], "potencia": []}
    if f"corrente_anterior_{fase}" not in st.session_state:
        st.session_state[f"corrente_anterior_{fase}"] = 0.0

# --- Layout ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("FDJ_engenharia.jpg", width=500)
with col_titulo:
    st.markdown("<h1 style='padding-top: 90px;'>Supervisório de Medição Elétrica</h1>", unsafe_allow_html=True)

# --- Atualiza leituras e buffers para os visores (sempre rodando!) ---
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
        st.session_state[f"valores_{fase}"]["tensao"] = st.session_state[f"valores_{fase}"]["tensao"][-300:]
    if corrente is not None:
        st.session_state[f"valores_{fase}"]["corrente"].append(float(corrente))
        st.session_state[f"valores_{fase}"]["corrente"] = st.session_state[f"valores_{fase}"]["corrente"][-300:]
    if potencia is not None:
        st.session_state[f"valores_{fase}"]["potencia"].append(float(potencia))
        st.session_state[f"valores_{fase}"]["potencia"] = st.session_state[f"valores_{fase}"]["potencia"][-300:]

# --- Dados para o gráfico (depende só do seletor dia_escolhido) ---
def get_dados_para_grafico(fase, dia):
    if dia == "Dia Atual":
        # Usa o buffer do session_state
        return st.session_state[f"valores_{fase}"]
    else:
        # Dia Anterior: pega da planilha inteira e converte para listas
        df = dfs[fase]
        tensao = df[colunas[fase]["tensao"]].astype(float).tolist() if colunas[fase]["tensao"] in df.columns else []
        corrente = df[colunas[fase]["corrente"]].astype(float).tolist() if colunas[fase]["corrente"] in df.columns else []
        potencia = df[colunas[fase]["potencia"]].astype(float).tolist() if colunas[fase]["potencia"] in df.columns else []
        
        return {
            "tensao": tensao,
            "corrente": corrente,
            "potencia": potencia
        }

dados_grafico = {fase: get_dados_para_grafico(fase, dia_escolhido) for fase in ["A", "B", "C"]}

# --- Últimos valores para visores (sempre do dia atual) ---
valores_tensao = {}
valores_corrente = {}
valores_potencia = {}
valores_frequencia = {}

for fase in ["A", "B", "C"]:
    df = dfs[fase]
    idx = st.session_state[f"index_{fase}"] - 1
    if idx < 0:
        idx = 0
    row = df.iloc[idx]

    tensao = row.get(colunas[fase]["tensao"], 0)
    corrente = row.get(colunas[fase]["corrente"], 0)
    potencia = row.get(colunas[fase]["potencia"], 0)
    frequencia = row.get(colunas[fase]["frequencia"], 0)

    if corrente == 0:
        corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
    else:
        st.session_state[f"corrente_anterior_{fase}"] = corrente

    valores_tensao[fase] = float(tensao)
    valores_corrente[fase] = float(corrente)
    valores_potencia[fase] = float(potencia)
    valores_frequencia[fase] = float(frequencia)

# --- Função para exibir os visores agrupados ---
def visor_fases(label, valores_por_fase, unidade, cor_fundo="#2c3e50"):
    cores_texto = {
        "A": "#2ecc71" if (label == "Tensão" and valores_por_fase["A"] >= 210) or label != "Tensão" else "#c0392b",
        "B": "#2ecc71" if (label == "Tensão" and valores_por_fase["B"] >= 210) or label != "Tensão" else "#c0392b",
        "C": "#2ecc71" if (label == "Tensão" and valores_por_fase["C"] >= 210) or label != "Tensão" else "#c0392b",
    }
    st.markdown(f"""
    <div style='
        background-color: {cor_fundo};
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 15px;
    '>
        <h3 style='color:white; text-align:center;'>{label}</h3>
        <div style='display: flex; flex-direction: column; gap: 10px;'>
            <div style='
                background-color: #34495e;
                color: {cores_texto["A"]};
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                width: 100%;
            '>
                Fase A: {valores_por_fase["A"]:.2f} {unidade}
            </div>
            <div style='
                background-color: #34495e;
                color: {cores_texto["B"]};
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                width: 100%;
            '>
                Fase B: {valores_por_fase["B"]:.2f} {unidade}
            </div>
            <div style='
                background-color: #34495e;
                color: {cores_texto["C"]};
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                width: 100%;
            '>
                Fase C: {valores_por_fase["C"]:.2f} {unidade}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Exibe visores ---
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

# --- Gráfico dinâmico ---
grafico_selecionado = st.radio("Selecione grandeza para o gráfico:", ("Tensão", "Corrente", "Potência Ativa"))

fig = go.Figure()
cores = {"A": "#2980b9", "B": "#e67e22", "C": "#27ae60"}

# Mapeamento para evitar KeyError
chave_grafico = {
    "Tensão": "tensao",
    "Corrente": "corrente",
    "Potência Ativa": "potencia"
}

for fase in ["A", "B", "C"]:
    dados = dados_grafico[fase]
    chave = chave_grafico[grafico_selecionado]
    fig.add_trace(go.Scatter(
        y=dados[chave],
        mode='lines+markers' if dia_escolhido == "Dia Atual" else 'lines',
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
