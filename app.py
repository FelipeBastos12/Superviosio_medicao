import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
PATHS = {
    "A": "Medicoes_FASEA.csv",
    "B": "Medicoes_FASEB.csv",
    "C": "Medicoes_FASEC.csv"
}
REFRESH_INTERVAL_MS = 500

# --- NOMES DAS COLUNAS POR FASE ---
colunas = {
    "A": {
        "tensao": "Tensao_Fase_A",
        "corrente": "Corrente_Fase_A",
        "potencia": "Potencia_Ativa_Fase_A",
        "frequencia": "Frequencia_Fase_A"
    },
    "B": {
        "tensao": "Tensao_Fase_B",
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
    try:
        df = pd.read_csv(path)
        df = df[df["Data"] == "23/05/2025"].copy()
        
        if df.empty:
            return pd.DataFrame()
            
        for col in df.columns:
            if col in ["Data", "Horário"]:
                continue
            df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
            try:
                df[col] = df[col].astype(float)
            except ValueError:
                pass
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Horário'], format='%d/%m/%Y %H:%M:%S')
        df = df.sort_values(by='Timestamp').reset_index(drop=True)
        return df
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {path}")
        return pd.DataFrame()

dfs = {fase: load_and_clean_csv(path) for fase, path in PATHS.items()}

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Supervisório LAT Trifásico", layout="wide")

# --- AUTOREFRESH (agora sempre ativo) ---
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- INICIALIZAÇÃO DE SESSION STATE ---
for fase in ["A", "B", "C"]:
    if f"index_{fase}" not in st.session_state:
        st.session_state[f"index_{fase}"] = 0
    if f"valores_{fase}" not in st.session_state:
        st.session_state[f"valores_{fase}"] = {
            "tensao": [], "corrente": [], "potencia": [], "timestamp": []
        }
    if f"corrente_anterior_{fase}" not in st.session_state:
        st.session_state[f"corrente_anterior_{fase}"] = 0.0

# --- Layout com logo e título lado a lado ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("FDJ_engenharia.jpg", width=500)
with col_titulo:
    st.markdown("<h1 style='padding-top: 90px;'>Supervisório de Medição Elétrica</h1>", unsafe_allow_html=True)

# --- FUNÇÃO PARA ATUALIZAR DADOS DO DIA ATUAL (sempre ativa) ---
def atualizar_dados_dia_atual(fase, df):
    if df.empty:
        return
    
    if st.session_state[f"index_{fase}"] >= len(df):
        # Reinicia o index e limpa os dados para simular um novo dia
        st.session_state[f"index_{fase}"] = 0
        st.session_state[f"valores_{fase}"]["tensao"] = []
        st.session_state[f"valores_{fase}"]["corrente"] = []
        st.session_state[f"valores_{fase}"]["potencia"] = []
        st.session_state[f"valores_{fase}"]["timestamp"] = []
        
    idx = st.session_state[f"index_{fase}"]
    row = df.iloc[idx]
    st.session_state[f"index_{fase}"] += 1

    tensao = row.get(colunas[fase]["tensao"], None)
    corrente = row.get(colunas[fase]["corrente"], None)
    potencia = row.get(colunas[fase]["potencia"], None)
    timestamp = row.get("Timestamp", None)

    if corrente == 0:
        corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
    else:
        st.session_state[f"corrente_anterior_{fase}"] = corrente

    if tensao is not None:
        st.session_state[f"valores_{fase}"]["tensao"].append(float(tensao))
    if corrente is not None:
        st.session_state[f"valores_{fase}"]["corrente"].append(float(corrente))
    if potencia is not None:
        st.session_state[f"valores_{fase}"]["potencia"].append(float(potencia))
    if timestamp is not None:
        st.session_state[f"valores_{fase}"]["timestamp"].append(timestamp)

# --- ATUALIZANDO DADOS DO DIA ATUAL EM TODAS AS FASES ---
for fase in ["A", "B", "C"]:
    atualizar_dados_dia_atual(fase, dfs[fase])

# --- SELETOR DE DIA ---
dia_escolhido = st.radio("Selecionar dia para visualização:", ("Dia Atual", "Dia Anterior"))

# --- PEGANDO VALORES PARA EXIBIÇÃO ---
valores_tensao = {}
valores_corrente = {}
valores_potencia = {}
valores_frequencia = {}

for fase in ["A", "B", "C"]:
    df = dfs[fase]
    
    if df.empty:
        tensao, corrente, potencia, frequencia = 0.0, 0.0, 0.0, 0.0
    else:
        if dia_escolhido == "Dia Atual":
            dados_sessao = st.session_state[f"valores_{fase}"]
            if dados_sessao["timestamp"]:
                last_idx = len(dados_sessao["timestamp"]) - 1
                tensao = dados_sessao["tensao"][last_idx]
                corrente = dados_sessao["corrente"][last_idx]
                potencia = dados_sessao["potencia"][last_idx]
                frequencia = df.iloc[st.session_state[f"index_{fase}"] - 1].get(colunas[fase]["frequencia"], 0)
            else:
                tensao, corrente, potencia, frequencia = 0.0, 0.0, 0.0, 0.0
        else:  # Dia Anterior
            tensao = float(df[colunas[fase]["tensao"]].iloc[-1])
            corrente = float(df[colunas[fase]["corrente"]].iloc[-1])
            potencia = float(df[colunas[fase]["potencia"]].iloc[-1])
            frequencia = float(df[colunas[fase]["frequencia"]].iloc[-1])

    valores_tensao[fase] = float(tensao)
    valores_corrente[fase] = float(corrente)
    valores_potencia[fase] = float(potencia)
    valores_frequencia[fase] = float(frequencia)

# --- VISOR PERSONALIZADO ---
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

# --- EXIBIÇÃO AGRUPADA EM GRADE 2x2 ---
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

# --- GRÁFICOS DINÂMICOS ---
grafico_selecionado = st.radio("", ("Tensão", "Corrente", "Potência Ativa"))

fig = go.Figure()
cores = {"A": "#2980b9", "B": "#e67e22", "C": "#27ae60"}

grafico_key_map = {
    "Tensão": "tensao",
    "Corrente": "corrente",
    "Potência Ativa": "potencia"
}

plotted = False
for fase in ["A", "B", "C"]:
    if dia_escolhido == "Dia Atual":
        dados = st.session_state[f"valores_{fase}"]
        x_values = dados.get("timestamp", [])
        y_key = grafico_key_map.get(grafico_selecionado)
        if y_key and dados.get(y_key):
            y_data = dados[y_key]
            modo = "lines+markers"
            plotted = True
        else:
            continue
    else: # Dia Anterior
        df = dfs[fase]
        if not df.empty:
            y_key = grafico_key_map.get(grafico_selecionado)
            if y_key:
                x_values = df["Timestamp"].tolist() + [None]
                y_data = df[colunas[fase][y_key]].tolist() + [None]
                modo = "lines"
                plotted = True
            else:
                continue
        else:
            continue

    if plotted:
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_data,
            mode=modo,
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))

if plotted:
    if grafico_selecionado == "Tensão":
        fig.update_layout(
            title="Tensão nas Fases",
            yaxis_title="Tensão (V)",
            yaxis=dict(range=[200, 250])
        )
    elif grafico_selecionado == "Corrente":
        fig.update_layout(title="Corrente nas Fases", yaxis_title="Corrente (A)")
    elif grafico_selecionado == "Potência Ativa":
        fig.update_layout(title="Potência Ativa nas Fases", yaxis_title="Potência Ativa (W)")
    
    date_23_05 = datetime(2025, 5, 23)
    fig.update_layout(
        xaxis_title="Horário",
        xaxis_tickformat='%H:%M',
        xaxis=dict(
            tickmode='array',
            tickvals=[date_23_05 + timedelta(hours=h) for h in range(25)],
            ticktext=[f'{h:02d}:00' for h in range(25)],
            range=[date_23_05, date_23_05 + timedelta(days=1)],
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        height=450,
        template="simple_white"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"Não há dados para exibir no gráfico de {grafico_selecionado}.")

