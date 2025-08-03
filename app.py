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
    # Filtra só dados do dia 23/05/2025
    df = df[df["Data"] == "23/05/2025"].copy()
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
        try:
            df[col] = df[col].astype(float)
        except ValueError:
            pass
    # Combina 'Data' e 'Horário' para criar um timestamp
    df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Horário'], format='%d/%m/%Y %H:%M:%S')
    return df

dfs = {fase: load_and_clean_csv(path) for fase, path in PATHS.items()}

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Supervisório LAT Trifásico", layout="wide")

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

# --- SELETOR DE DIA ---
dia_escolhido = st.radio("Selecionar dia para visualização:", ("Dia Atual", "Dia Anterior"))

# --- AUTOREFRESH (só para Dia Atual) ---
if dia_escolhido == "Dia Atual":
    st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- FUNÇÃO PARA PEGAR OS DADOS SEGUNDO O DIA SELECIONADO ---
def get_dados(fase, dia):
    df = dfs[fase]
    if dia == "Dia Atual":
        idx = st.session_state[f"index_{fase}"]
        if idx >= len(df):
            st.session_state[f"index_{fase}"] = 0
            idx = 0
            st.success(f"Reiniciando dados da fase {fase}")
        row = df.iloc[idx]
        st.session_state[f"index_{fase}"] += 1

        # Extrai dados linha a linha
        tensao = row.get(colunas[fase]["tensao"], None)
        corrente = row.get(colunas[fase]["corrente"], None)
        potencia = row.get(colunas[fase]["potencia"], None)
        timestamp = row.get("Timestamp", None)

        # Corrente zero → mantém anterior
        if corrente == 0:
            corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
        else:
            st.session_state[f"corrente_anterior_{fase}"] = corrente

        # Atualiza buffers para gráfico
        if tensao is not None:
            st.session_state[f"valores_{fase}"]["tensao"].append(float(tensao))
        if corrente is not None:
            st.session_state[f"valores_{fase}"]["corrente"].append(float(corrente))
        if potencia is not None:
            st.session_state[f"valores_{fase}"]["potencia"].append(float(potencia))
        if timestamp is not None:
            st.session_state[f"valores_{fase}"]["timestamp"].append(timestamp)

        return {
            "tensao": st.session_state[f"valores_{fase}"]["tensao"],
            "corrente": st.session_state[f"valores_{fase}"]["corrente"],
            "potencia": st.session_state[f"valores_{fase}"]["potencia"],
            "timestamp": st.session_state[f"valores_{fase}"]["timestamp"]
        }
    else:  # Dia Anterior - retorna todos os dados da planilha (já filtrados no load)
        tensao = df[colunas[fase]["tensao"]].astype(float).tolist()
        corrente = df[colunas[fase]["corrente"]].astype(float).tolist()
        potencia = df[colunas[fase]["potencia"]].astype(float).tolist()
        timestamp = df["Timestamp"].tolist()

        # Atualiza session_state para evitar erros futuros
        st.session_state[f"valores_{fase}"]["tensao"] = tensao
        st.session_state[f"valores_{fase}"]["corrente"] = corrente
        st.session_state[f"valores_{fase}"]["potencia"] = potencia
        st.session_state[f"valores_{fase}"]["timestamp"] = timestamp

        return {
            "tensao": tensao,
            "corrente": corrente,
            "potencia": potencia,
            "timestamp": timestamp
        }

# --- PEGANDO OS DADOS SEGUNDO DIA SELECIONADO ---
for fase in ["A", "B", "C"]:
    _ = get_dados(fase, dia_escolhido)

# --- PEGANDO ÚLTIMOS VALORES PARA VISOR AGRUPADO ---
valores_tensao = {}
valores_corrente = {}
valores_potencia = {}
valores_frequencia = {}

for fase in ["A", "B", "C"]:
    df = dfs[fase]
    if dia_escolhido == "Dia Atual":
        # Se os dados já estão no buffer de sessão, pega o último. Se não, usa o primeiro da planilha.
        if st.session_state[f"valores_{fase}"]["timestamp"]:
            last_idx = len(st.session_state[f"valores_{fase}"]["timestamp"]) - 1
            tensao = st.session_state[f"valores_{fase}"]["tensao"][last_idx]
            corrente = st.session_state[f"valores_{fase}"]["corrente"][last_idx]
            potencia = st.session_state[f"valores_{fase}"]["potencia"][last_idx]
            # Frequência não está no session state, pega do dataframe original
            row_idx_original = st.session_state[f"index_{fase}"] - 1
            if row_idx_original < 0:
                row_idx_original = 0
            frequencia = df.iloc[row_idx_original].get(colunas[fase]["frequencia"], 0)
        else:
            # Caso o buffer esteja vazio, pega a primeira linha para evitar erro
            row = df.iloc[0]
            tensao = row.get(colunas[fase]["tensao"], 0)
            corrente = row.get(colunas[fase]["corrente"], 0)
            potencia = row.get(colunas[fase]["potencia"], 0)
            frequencia = row.get(colunas[fase]["frequencia"], 0)

        # Corrente zero → mantém anterior
        if corrente == 0:
            corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
        else:
            st.session_state[f"corrente_anterior_{fase}"] = corrente

        valores_tensao[fase] = float(tensao)
        valores_corrente[fase] = float(corrente)
        valores_potencia[fase] = float(potencia)
        valores_frequencia[fase] = float(frequencia)

    else:  # Dia Anterior pega o último valor para exibir no visor
        valores_tensao[fase] = float(df[colunas[fase]["tensao"]].iloc[-1])
        valores_corrente[fase] = float(df[colunas[fase]["corrente"]].iloc[-1])
        valores_potencia[fase] = float(df[colunas[fase]["potencia"]].iloc[-1])
        valores_frequencia[fase] = float(df[colunas[fase]["frequencia"]].iloc[-1])

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

# Cria um intervalo de tempo para as 24h para o Dia Atual
date_23_05 = datetime(2025, 5, 23)
horarios_24h = [date_23_05 + timedelta(hours=h) for h in range(25)]

for fase in ["A", "B", "C"]:
    dados = st.session_state[f"valores_{fase}"]
    
    # Lógica para o eixo X
    if dia_escolhido == "Dia Atual":
        x_values = dados["timestamp"]
        y_values = dados[grafico_selecionado.lower().replace(" ", "_")]
        mode = "lines+markers"
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode=mode,
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))
    else:  # Dia Anterior
        x_values = dfs[fase]["Timestamp"]
        y_values = dfs[fase][colunas[fase][grafico_selecionado.lower().replace(" ", "_")]]
        mode = "lines"
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode=mode,
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))

    # Configura o layout do gráfico
    if grafico_selecionado == "Tensão":
        fig.update_layout(title="Tensão nas Fases", yaxis_title="Tensão (V)", yaxis=dict(range=[200, 250]))
    elif grafico_selecionado == "Corrente":
        fig.update_layout(title="Corrente nas Fases", yaxis_title="Corrente (A)")
    elif grafico_selecionado == "Potência Ativa":
        fig.update_layout(title="Potência Ativa nas Fases", yaxis_title="Potência Ativa (W)")

fig.update_layout(
    xaxis_title="Horário",
    xaxis_tickformat='%H:%M',
    xaxis=dict(
        tickmode='array',
        tickvals=horarios_24h,
        ticktext=[f'{h.hour:02d}:00' for h in horarios_24h],
        range=[date_23_05, date_23_05 + timedelta(days=1)],
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)'
    ),
    height=450,
    template="simple_white"
)

st.plotly_chart(fig, use_container_width=True)
