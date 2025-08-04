import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import numpy as np
import collections

# --- CONFIGURAÇÕES ---
# O user subiu arquivos com '(3)' no nome. Assumimos que essa é a convenção
PATHS = {
    "A": "Planilha_242_LAT - FASEA (3).csv",
    "B": "Planilha_242_LAT - FASEB (3).csv",
    "C": "Planilha_242_LAT - FASEC (3).csv"
}
REFRESH_INTERVAL_MS = 500

# --- LIMITES DE OPERAÇÃO ---
TENSÃO_MIN = 200.0  # Volts
TENSÃO_MAX = 250.0  # Volts
CORRENTE_MAX = 50.0 # Amperes
POTENCIA_APARENTE_MAX = 4500.0      # VA (por fase)
POTENCIA_APARENTE_TOTAL_MAX = 12000.0 # VA (total)
FREQUENCIA_MIN = 58.9 # Hz (para sistema 60Hz)
FREQUENCIA_MAX = 62.0 # Hz (para sistema 60Hz)
FATOR_POTENCIA_MIN = 0.85 # Mínimo recomendado
DEMANDA_MAXIMA = 10000.0 # Exemplo de limite de demanda máxima (W)

# --- NOMES DAS COLUNAS POR FASE ---
colunas = {
    "A": {
        "tensao": "Tensao_Fase_A",
        "corrente": "Corrente_Fase_A",
        "potencia": "Potencia_Aparente_Fase_A",
        "frequencia": "Frequencia_Fase_A",
        "fator_de_potencia": "fator_De_Potencia_Fase_A",
        "consumo": "C (kWh)",
        "potencia_ativa": "Potencia_Ativa_Fase_A",
        "potencia_reativa": "Potencia_Reativa_Fase_A"
    },
    "B": {
        "tensao": "Tensao_Fase_B",
        "corrente": "Corrente_Fase_B",
        "potencia": "Potencia_Aparente_Fase_B",
        "frequencia": "Frequencia_Fase_B",
        "fator_de_potencia": "fator_De_Potencia_Fase_B",
        "consumo": "C (kWh)",
        "potencia_ativa": "Potencia_Ativa_Fase_B",
        "potencia_reativa": "Potencia_Reativa_Fase_B"
    },
    "C": {
        "tensao": "Tensao_Fase_C",
        "corrente": "Corrente_Fase_C",
        "potencia": "Potencia_Aparente_Fase_C",
        "frequencia": "Frequencia_Fase_C",
        "fator_de_potencia": "fator_De_Potencia_Fase_C",
        "consumo": "C (kWh)",
        "potencia_ativa": "Potencia_Ativa_Fase_C",
        "potencia_reativa": "Potencia_Reativa_Fase_C"
    }
}

# --- LEITURA E LIMPEZA ---
@st.cache_data
def load_and_clean_csv(path):
    try:
        df = pd.read_csv(path)
        
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

# Carregar os dados de todas as fases
dfs_raw = {fase: load_and_clean_csv(path) for fase, path in PATHS.items()}

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Supervisório LAT Trifásico", layout="wide")

# --- LÓGICA DE SELEÇÃO DE DATA DINÂMICA ---
# Encontrar a data mais recente nos dados, se houver
combined_timestamps = pd.concat([df['Timestamp'] for df in dfs_raw.values() if not df.empty])
unique_dates = sorted(combined_timestamps.dt.floor('D').unique(), reverse=True)

if not unique_dates:
    st.error("Não há dados para exibir. Por favor, verifique os arquivos CSV.")
    st.stop()

# Define o dia atual e anterior com base nos dados disponíveis
dia_atual_ts = unique_dates[0]
dia_anterior_ts = unique_dates[1] if len(unique_dates) > 1 else unique_dates[0]

# Cria os dataframes filtrados para o dia atual e anterior
dfs = {}
for fase, df_raw in dfs_raw.items():
    if not df_raw.empty:
        dfs[fase] = df_raw
    else:
        dfs[fase] = pd.DataFrame()

# --- AUTOREFRESH (agora sempre ativo) ---
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- INICIALIZAÇÃO DE SESSION STATE ---
for fase in ["A", "B", "C"]:
    if f"index_{fase}" not in st.session_state:
        st.session_state[f"index_{fase}"] = 0
    if f"valores_{fase}" not in st.session_state:
        st.session_state[f"valores_{fase}"] = {
            "tensao": [], "corrente": [], "potencia": [], "timestamp": [],
            "potencia_ativa": [], "potencia_reativa": []
        }
    if f"corrente_anterior_{fase}" not in st.session_state:
        st.session_state[f"corrente_anterior_{fase}"] = 0.0

if "grafico_selecionado" not in st.session_state:
    st.session_state["grafico_selecionado"] = "Tensão"

# Inicializa o log de erros como uma deque para limitar o tamanho
if "log_erros" not in st.session_state:
    st.session_state["log_erros"] = collections.deque(maxlen=10)


# --- Layout com logo e título lado a lado ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("FDJ_engenharia.jpg", width=500)
with col_titulo:
    st.markdown("<h1 style='padding-top: 90px;'>Supervisório de Medição Elétrica</h1>", unsafe_allow_html=True)

# --- FUNÇÃO PARA ATUALIZAR DADOS DO DIA ATUAL (sempre ativa) ---
def atualizar_dados_dia_atual(fase, df):
    df_dia_atual = df[df['Timestamp'].dt.date == dia_atual_ts.date()]
    if df_dia_atual.empty:
        return
    
    if st.session_state[f"index_{fase}"] >= len(df_dia_atual):
        st.session_state[f"index_{fase}"] = 0
        st.session_state[f"valores_{fase}"]["tensao"] = []
        st.session_state[f"valores_{fase}"]["corrente"] = []
        st.session_state[f"valores_{fase}"]["potencia"] = []
        st.session_state[f"valores_{fase}"]["timestamp"] = []
        st.session_state[f"valores_{fase}"]["potencia_ativa"] = []
        st.session_state[f"valores_{fase}"]["potencia_reativa"] = []
        
    idx = st.session_state[f"index_{fase}"]
    row = df_dia_atual.iloc[idx]
    st.session_state[f"index_{fase}"] += 1

    tensao = row.get(colunas[fase]["tensao"], None)
    corrente = row.get(colunas[fase]["corrente"], None)
    potencia = row.get(colunas[fase]["potencia"], None)
    potencia_ativa = row.get(colunas[fase]["potencia_ativa"], None)
    potencia_reativa = row.get(colunas[fase]["potencia_reativa"], None)
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
    if potencia_ativa is not None:
        st.session_state[f"valores_{fase}"]["potencia_ativa"].append(float(potencia_ativa))
    if potencia_reativa is not None:
        st.session_state[f"valores_{fase}"]["potencia_reativa"].append(float(potencia_reativa))
    if timestamp is not None:
        st.session_state[f"valores_{fase}"]["timestamp"].append(timestamp)

# --- ATUALIZANDO DADOS DO DIA ATUAL EM TODAS AS FASES ---
for fase in ["A", "B", "C"]:
    atualizar_dados_dia_atual(fase, dfs[fase])

# --- SELETOR DE DIA ---
dia_escolhido_str = st.radio("Selecionar dia para visualização:", (dia_atual_ts.strftime('%d/%m/%Y') + " (Dia Atual)", dia_anterior_ts.strftime('%d/%m/%Y') + " (Dia Anterior)"))
if dia_escolhido_str.endswith(" (Dia Atual)"):
    dia_escolhido = dia_atual_ts.date()
else:
    dia_escolhido = dia_anterior_ts.date()

# --- PEGANDO VALORES PARA EXIBIÇÃO ---
valores_tensao = {}
valores_corrente = {}
valores_potencia = {}
valores_frequencia = {}
valores_fator_potencia = {}
valores_consumo = {}
valores_potencia_ativa = {}
valores_potencia_reativa = {}

for fase in ["A", "B", "C"]:
    df = dfs[fase]
    df_filtrado = df[df['Timestamp'].dt.date == dia_escolhido]
    
    if df_filtrado.empty:
        tensao, corrente, potencia, frequencia, fator_potencia, consumo = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        potencia_ativa, potencia_reativa = 0.0, 0.0
    else:
        if dia_escolhido == dia_atual_ts.date():
            dados_sessao = st.session_state[f"valores_{fase}"]
            if dados_sessao["timestamp"]:
                last_idx = len(dados_sessao["timestamp"]) - 1
                tensao = dados_sessao["tensao"][last_idx]
                corrente = dados_sessao["corrente"][last_idx]
                potencia = dados_sessao["potencia"][last_idx]
                potencia_ativa = dados_sessao["potencia_ativa"][last_idx]
                potencia_reativa = dados_sessao["potencia_reativa"][last_idx]
                row = df_filtrado.iloc[len(dados_sessao["timestamp"]) - 1]
                frequencia = row.get(colunas[fase]["frequencia"], 0)
                fator_potencia = row.get(colunas[fase]["fator_de_potencia"], 0)
                consumo = row.get(colunas[fase]["consumo"], 0)
            else:
                tensao, corrente, potencia, frequencia, fator_potencia, consumo = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                potencia_ativa, potencia_reativa = 0.0, 0.0
        else:  # Dia Anterior
            row = df_filtrado.iloc[-1]
            tensao = row[colunas[fase]["tensao"]]
            corrente = row[colunas[fase]["corrente"]]
            potencia = row[colunas[fase]["potencia"]]
            frequencia = row[colunas[fase]["frequencia"]]
            fator_potencia = row[colunas[fase]["fator_de_potencia"]]
            consumo = row[colunas[fase]["consumo"]]
            potencia_ativa = row[colunas[fase]["potencia_ativa"]]
            potencia_reativa = row[colunas[fase]["potencia_reativa"]]

    valores_tensao[fase] = float(tensao)
    valores_corrente[fase] = float(corrente)
    valores_potencia[fase] = float(potencia)
    valores_frequencia[fase] = float(frequencia)
    valores_fator_potencia[fase] = float(fator_potencia)
    valores_consumo[fase] = float(consumo)
    valores_potencia_ativa[fase] = float(potencia_ativa)
    valores_potencia_reativa[fase] = float(potencia_reativa)

# Obtém o timestamp do último dado para usar no log
timestamp_ultimo_dado = st.session_state["valores_A"]["timestamp"][-1] if st.session_state["valores_A"]["timestamp"] and dia_escolhido == dia_atual_ts.date() else datetime.now()


# --- VISOR PERSONALIZADO ---
def visor_fases(label, valores_por_fase, unidade, timestamp_erro):
    cor_fundo_default = "#2c3e50"
    cor_fundo_alerta = "#c0392b"
    cor_fundo_atual = cor_fundo_default
    
    # Define as cores do texto e verifica alarmes
    cores_texto = {}
    for fase in ["A", "B", "C"]:
        valor = valores_por_fase[fase]
        if label == "Tensão":
            if TENSÃO_MIN <= valor <= TENSÃO_MAX:
                cores_texto[fase] = "#2ecc71" # Verde
            else:
                cores_texto[fase] = "#c0392b" # Vermelho
                cor_fundo_atual = cor_fundo_alerta # Aciona o alarme de fundo
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Tensão na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Corrente":
            cores_texto[fase] =  "#2ecc71" # Verde
            if valor > CORRENTE_MAX:
                cores_texto[fase] = "#c0392b" # Vermelho
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Corrente na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Potência Aparente":
            cores_texto[fase] =  "#2ecc71" # Verde
            if valor > POTENCIA_APARENTE_MAX:
                cores_texto[fase] = "#c0392b" # Vermelho
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Potência na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Frequência":
            cores_texto[fase] =  "#2ecc71" # Verde
            if not (FREQUENCIA_MIN <= valor <= FREQUENCIA_MAX):
                cores_texto[fase] = "#c0392b" # Vermelho
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Frequência na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Fator de Potência":
            cores_texto[fase] =  "#2ecc71" # Verde
            if valor < FATOR_POTENCIA_MIN:
                cores_texto[fase] = "#c0392b" # Vermelho
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Fator de Potência na Fase {fase}: {valor:.2f}")
        else:
            cores_texto[fase] =  "#2ecc71" # Verde
    
    st.markdown(f"""
    <div style='
        background-color: {cor_fundo_atual};
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

# --- VISOR PERSONALIZADO PARA VALORES TOTAIS ---
def visor_total(label, valor_total, unidade, timestamp_erro, limite_superior=None, limite_inferior=None):
    cor_fundo_default = "#2c3e50"
    cor_fundo_alerta = "#c0392b"
    cor_fundo_atual = cor_fundo_default
    
    alarme_acionado = False
    
    cor_texto_
