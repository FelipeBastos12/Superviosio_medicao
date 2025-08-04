import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import numpy as np
import collections

# --- CONFIGURAÇÕES ---
PATHS = {
    "A": "Planilha_242_LAT - FASEA (3).csv",
    "B": "Planilha_242_LAT - FASEB (3).csv",
    "C": "Planilha_242_LAT - FASEC (3).csv"
}
REFRESH_INTERVAL_MS = 500

# --- LIMITES DE OPERAÇÃO ---
TENSÃO_MIN = 200.0     # Volts
TENSÃO_MAX = 250.0     # Volts
CORRENTE_MAX = 50.0    # Amperes
POTENCIA_APARENTE_MAX = 4500.0       # VA (por fase)
POTENCIA_APARENTE_TOTAL_MAX = 12000.0 # VA (total)
FREQUENCIA_MIN = 58.9 # Hz (para sistema 60Hz)
FREQUENCIA_MAX = 62.0 # Hz (para sistema 60Hz)
FATOR_POTENCIA_MIN = 0.85 # Mínimo recomendado
DEMANDA_MAXIMA = 10000.0 # Exemplo de limite de demanda máxima (W)

# --- TARIFAS BRASILEIRAS (EXEMPLO) ---
TARIFAS = {
    "TE": 0.60, # Tarifa de Energia (R$/kWh)
    "TUSD": 0.40, # Tarifa de Uso do Sistema de Distribuição (R$/kWh)
    "ICMS": 0.25, # Imposto sobre Circulação de Mercadorias e Serviços (%)
    "PIS": 0.0165, # Programa de Integração Social (%)
    "COFINS": 0.076, # Contribuição para o Financiamento da Seguridade Social (%)
    "BANDEIRAS": {
        "Verde": 0.00,
        "Amarela": 0.02, # Exemplo de custo extra por kWh
        "Vermelha 1": 0.05,
        "Vermelha 2": 0.08,
    }
}

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

dfs = {fase: load_and_clean_csv(path) for fase, path in PATHS.items()}

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Supervisório LAT Trifásico", layout="wide")

# --- AUTOREFRESH (agora sempre ativo) ---
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- INICIALIZAÇÃO DE SESSION STATE ---
if "dia_anterior" not in st.session_state:
    if not dfs["A"].empty:
        st.session_state["dia_anterior"] = dfs["A"]["Timestamp"].min().date()
        st.session_state["dia_atual"] = st.session_state["dia_anterior"] + timedelta(days=1)
    else:
        st.session_state["dia_anterior"] = datetime.now().date()
        st.session_state["dia_atual"] = datetime.now().date() + timedelta(days=1)
    
for fase in ["A", "B", "C"]:
    if f"index_{fase}" not in st.session_state:
        st.session_state[f"index_{fase}"] = 0
    if f"valores_{fase}" not in st.session_state:
        st.session_state[f"valores_{fase}"] = {
            "tensao": [], "corrente": [], "potencia": [], "timestamp": [],
            "potencia_ativa": [], "potencia_reativa": [], "consumo": []
        }
    if f"corrente_anterior_{fase}" not in st.session_state:
        st.session_state[f"corrente_anterior_{fase}"] = 0.0

if "grafico_selecionado" not in st.session_state:
    st.session_state["grafico_selecionado"] = "Tensão"

if "log_erros" not in st.session_state:
    st.session_state["log_erros"] = collections.deque(maxlen=10)

# --- Variáveis para a demanda máxima histórica e consumo acumulado ---
if "max_demanda_historica" not in st.session_state:
    st.session_state["max_demanda_historica"] = 0.0
if "dia_max_demanda_historica" not in st.session_state:
    st.session_state["dia_max_demanda_historica"] = ""
if "consumo_acumulado" not in st.session_state:
    # Definir o dia inicial para o cálculo do consumo acumulado
    dia_inicial_consumo = datetime(2025, 8, 1).date()
    consumo_inicial = 0.0
    
    # Calcular o consumo total do dia inicial (01/08/2025)
    df_dia_inicial_A = dfs["A"][dfs["A"]["Timestamp"].dt.date == dia_inicial_consumo]
    df_dia_inicial_B = dfs["B"][dfs["B"]["Timestamp"].dt.date == dia_inicial_consumo]
    df_dia_inicial_C = dfs["C"][dfs["C"]["Timestamp"].dt.date == dia_inicial_consumo]
    
    if not df_dia_inicial_A.empty and not df_dia_inicial_B.empty and not df_dia_inicial_C.empty:
        consumo_inicial = df_dia_inicial_A['C (kWh)'].iloc[-1] + df_dia_inicial_B['C (kWh)'].iloc[-1] + df_dia_inicial_C['C (kWh)'].iloc[-1]
    
    st.session_state["consumo_acumulado"] = consumo_inicial
    st.session_state["consumo_acumulado_temp"] = 0.0

# --- Função para calcular o consumo diário de forma segura
def calcular_consumo_diario(df_A, df_B, df_C):
    if df_A.empty or df_B.empty or df_C.empty or 'C (kWh)' not in df_A.columns:
        return 0.0
    
    consumo_A = df_A['C (kWh)'].iloc[-1] - df_A['C (kWh)'].iloc[0]
    consumo_B = df_B['C (kWh)'].iloc[-1] - df_B['C (kWh)'].iloc[0]
    consumo_C = df_C['C (kWh)'].iloc[-1] - df_C['C (kWh)'].iloc[0]
    
    return consumo_A + consumo_B + consumo_C

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
    
    df_dia_atual = df[df["Timestamp"].dt.date == st.session_state["dia_atual"]]
    
    if df_dia_atual.empty:
        return
        
    if st.session_state[f"index_{fase}"] >= len(df_dia_atual):
        # AQUI É ONDE O DIA MUDA - FIM DA SIMULAÇÃO DO DIA ANTERIOR
        if fase == "C":
            # Calcula e adiciona o consumo do dia anterior ao acumulado
            df_dia_anterior_A = dfs["A"][dfs["A"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]
            df_dia_anterior_B = dfs["B"][dfs["B"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]
            df_dia_anterior_C = dfs["C"][dfs["C"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]

            consumo_do_dia_anterior = calcular_consumo_diario(df_dia_anterior_A, df_dia_anterior_B, df_dia_anterior_C)
            st.session_state["consumo_acumulado"] += consumo_do_dia_anterior
            
            st.session_state["dia_anterior"] = st.session_state["dia_atual"]
            st.session_state["dia_atual"] += timedelta(days=1)
            df_dia_atual_prox = df[df["Timestamp"].dt.date == st.session_state["dia_atual"]]
            if df_dia_atual_prox.empty:
                st.session_state["dia_anterior"] = dfs["A"]["Timestamp"].min().date()
                st.session_state["dia_atual"] = st.session_state["dia_anterior"] + timedelta(days=1)
                
                # Reinicializar o consumo acumulado para o novo ciclo
                dia_inicial_consumo = dfs["A"]["Timestamp"].min().date()
                df_dia_inicial_A = dfs["A"][dfs["A"]["Timestamp"].dt.date == dia_inicial_consumo]
                df_dia_inicial_B = dfs["B"][dfs["B"]["Timestamp"].dt.date == dia_inicial_consumo]
                df_dia_inicial_C = dfs["C"][dfs["C"]["Timestamp"].dt.date == dia_inicial_consumo]
                
                if not df_dia_inicial_A.empty and not df_dia_inicial_B.empty and not df_dia_inicial_C.empty:
                    consumo_inicial = df_dia_inicial_A['C (kWh)'].iloc[-1] + df_dia_inicial_B['C (kWh)'].iloc[-1] + df_dia_inicial_C['C (kWh)'].iloc[-1]
                st.session_state["consumo_acumulado"] = consumo_inicial
                
                df_dia_atual_prox = df[df["Timestamp"].dt.date == st.session_state["dia_atual"]]
                if df_dia_atual_prox.empty:
                    return

        st.session_state[f"index_{fase}"] = 0
        st.session_state[f"valores_{fase}"]["tensao"] = []
        st.session_state[f"valores_{fase}"]["corrente"] = []
        st.session_state[f"valores_{fase}"]["potencia"] = []
        st.session_state[f"valores_{fase}"]["timestamp"] = []
        st.session_state[f"valores_{fase}"]["potencia_ativa"] = []
        st.session_state[f"valores_{fase}"]["potencia_reativa"] = []
        st.session_state[f"valores_{fase}"]["consumo"] = []
        
    idx = st.session_state[f"index_{fase}"]
    row = df_dia_atual.iloc[idx]
    st.session_state[f"index_{fase}"] += 1

    tensao = row.get(colunas[fase]["tensao"], None)
    corrente = row.get(colunas[fase]["corrente"], None)
    potencia = row.get(colunas[fase]["potencia"], None)
    potencia_ativa = row.get(colunas[fase]["potencia_ativa"], None)
    potencia_reativa = row.get(colunas[fase]["potencia_reativa"], None)
    consumo = row.get(colunas[fase]["consumo"], None)
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
    if consumo is not None:
        st.session_state[f"valores_{fase}"]["consumo"].append(float(consumo))
    if timestamp is not None:
        st.session_state[f"valores_{fase}"]["timestamp"].append(timestamp)

# --- ATUALIZANDO DADOS DO DIA ATUAL EM TODAS AS FASES ---
for fase in ["A", "B", "C"]:
    atualizar_dados_dia_atual(fase, dfs[fase])
    
st.markdown("---")

# --- SELETOR DE DIA ---
dia_escolhido = st.radio("Selecionar dia para visualização:", ("Dia Atual", "Dia Anterior"))

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
    
    if df.empty:
        tensao, corrente, potencia, frequencia, fator_potencia, consumo = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        potencia_ativa, potencia_reativa = 0.0, 0.0
    else:
        if dia_escolhido == "Dia Atual":
            df_dia_escolhido = df[df["Timestamp"].dt.date == st.session_state["dia_atual"]]
            dados_sessao = st.session_state[f"valores_{fase}"]

            if dados_sessao["timestamp"]:
                last_idx = len(dados_sessao["timestamp"]) - 1
                tensao = dados_sessao["tensao"][last_idx]
                corrente = dados_sessao["corrente"][last_idx]
                potencia = dados_sessao["potencia"][last_idx]
                potencia_ativa = dados_sessao["potencia_ativa"][last_idx]
                potencia_reativa = dados_sessao["potencia_reativa"][last_idx]
                
                if not df_dia_escolhido.empty and st.session_state[f"index_{fase}"] > 0:
                    row = df_dia_escolhido.iloc[st.session_state[f"index_{fase}"] - 1]
                    frequencia = row.get(colunas[fase]["frequencia"], 0)
                    fator_potencia = row.get(colunas[fase]["fator_de_potencia"], 0)
                    consumo = dados_sessao["consumo"][-1]
                else:
                    frequencia, fator_potencia, consumo = 0.0, 0.0, 0.0
            else:
                tensao, corrente, potencia, frequencia, fator_potencia, consumo = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                potencia_ativa, potencia_reativa = 0.0, 0.0
        else:  # Dia Anterior
            df_dia_escolhido = df[df["Timestamp"].dt.date == st.session_state["dia_anterior"]]
            if not df_dia_escolhido.empty:
                row = df_dia_escolhido.iloc[-1]
                tensao = row[colunas[fase]["tensao"]]
                corrente = row[colunas[fase]["corrente"]]
                potencia = row[colunas[fase]["potencia"]]
                frequencia = row[colunas[fase]["frequencia"]]
                fator_potencia = row[colunas[fase]["fator_de_potencia"]]
                consumo = row[colunas[fase]["consumo"]]
                potencia_ativa = row[colunas[fase]["potencia_ativa"]]
                potencia_reativa = row[colunas[fase]["potencia_reativa"]]
            else:
                tensao, corrente, potencia, frequencia, fator_potencia, consumo = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                potencia_ativa, potencia_reativa = 0.0, 0.0

    valores_tensao[fase] = float(tensao)
    valores_corrente[fase] = float(corrente)
    valores_potencia[fase] = float(potencia)
    valores_frequencia[fase] = float(frequencia)
    valores_fator_potencia[fase] = float(fator_potencia)
    valores_consumo[fase] = float(consumo)
    valores_potencia_ativa[fase] = float(potencia_ativa)
    valores_potencia_reativa[fase] = float(potencia_reativa)

timestamp_ultimo_dado = st.session_state["valores_A"]["timestamp"][-1] if st.session_state["valores_A"]["timestamp"] else datetime.now()


# --- VISOR PERSONALIZADO ---
def visor_fases(label, valores_por_fase, unidade, timestamp_erro):
    cor_fundo_default = "#2c3e50"
    cor_fundo_alerta = "#c0392b"
    cor_fundo_atual = cor_fundo_default
    
    cores_texto = {}
    for fase in ["A", "B", "C"]:
        valor = valores_por_fase[fase]
        if label == "Tensão":
            if TENSÃO_MIN <= valor <= TENSÃO_MAX:
                cores_texto[fase] = "#2ecc71"
            else:
                cores_texto[fase] = "#c0392b"
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Tensão na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Corrente":
            cores_texto[fase] =  "#2ecc71"
            if valor > CORRENTE_MAX:
                cores_texto[fase] = "#c0392b"
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Corrente na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Potência Aparente":
            cores_texto[fase] =  "#2ecc71"
            if valor > POTENCIA_APARENTE_MAX:
                cores_texto[fase] = "#c0392b"
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Potência na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Frequência":
            cores_texto[fase] =  "#2ecc71"
            if not (FREQUENCIA_MIN <= valor <= FREQUENCIA_MAX):
                cores_texto[fase] = "#c0392b"
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Frequência na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Fator de Potência":
            cores_texto[fase] =  "#2ecc71"
            if valor < FATOR_POTENCIA_MIN:
                cores_texto[fase] = "#c0392b"
                cor_fundo_atual = cor_fundo_alerta
                st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Fator de Potência na Fase {fase}: {valor:.2f}")
        else:
            cores_texto[fase] =  "#2ecc71"
    
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
    
    cor_texto_default = "#2ecc71"
    cor_texto_alerta = "#c0392b"
    cor_texto_atual = cor_texto_default

    if limite_superior is not None and valor_total > limite_superior:
        alarme_acionado = True
    if limite_inferior is not None and valor_total < limite_inferior:
        alarme_acionado = True
    
    if alarme_acionado:
        cor_fundo_atual = cor_fundo_alerta
        cor_texto_atual = cor_texto_alerta
        st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME Total de {label}: {valor_total:.2f} {unidade}")

    st.markdown(f"""
    <div style='
        background-color: {cor_fundo_atual};
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 15px;
    '>
        <h3 style='color:white; text-align:center;'>{label}</h3>
        <div style='
            background-color: #34495e;
            color: {cor_texto_atual};
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            width: 100%;
        '>
            Total: {valor_total:.2f} {unidade}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- EXIBIÇÃO AGRUPADA EM GRADE (3 colunas, depois 3 colunas) ---
st.markdown("<h3>Grandezas por Fase</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    visor_fases("Tensão", valores_tensao, "V", timestamp_ultimo_dado)
with col2:
    visor_fases("Corrente", valores_corrente, "A", timestamp_ultimo_dado)
with col3:
    visor_fases("Frequência", valores_frequencia, "Hz", timestamp_ultimo_dado)

col4, col5, col6 = st.columns(3)

with col4:
    visor_fases("Potência Aparente", valores_potencia, "VA", timestamp_ultimo_dado)
with col5:
    visor_fases("Fator de Potência", valores_fator_potencia, "", timestamp_ultimo_dado)
with col6:
    visor_fases("Consumo", valores_consumo, "kWh", timestamp_ultimo_dado)


# --- CÁLCULOS DOS VALORES TOTAIS E DEMANDA ---
P_total_inst = sum(valores_potencia_ativa.values())
Q_total_inst = sum(valores_potencia_reativa.values())
S_total_inst = np.sqrt(P_total_inst**2 + Q_total_inst**2)
FP_total_inst = P_total_inst / S_total_inst if S_total_inst != 0 else 0

demand_window = 5 # 5 pontos de 3min = 15 minutos

# --- CÁLCULO DA DEMANDA MÁXIMA DO DIA ATUAL EM TEMPO REAL ---
if dia_escolhido == "Dia Atual":
    potencia_ativa_faseA = st.session_state["valores_A"]["potencia_ativa"]
    potencia_ativa_faseB = st.session_state["valores_B"]["potencia_ativa"]
    potencia_ativa_faseC = st.session_state["valores_C"]["potencia_ativa"]

    min_len_p_ativa = min(len(potencia_ativa_faseA), len(potencia_ativa_faseB), len(potencia_ativa_faseC))
    
    demanda_maxima_dia_atual = 0.0
    if min_len_p_ativa >= demand_window:
        total_potencia_ativa_historico = [sum(p) for p in zip(potencia_ativa_faseA[:min_len_p_ativa], potencia_ativa_faseB[:min_len_p_ativa], potencia_ativa_faseC[:min_len_p_ativa])]
        total_series = pd.Series(total_potencia_ativa_historico)
        demanda_maxima_dia_atual = total_series.rolling(window=demand_window).mean().max()
    
    # Compara a demanda do dia atual com a histórica
    if demanda_maxima_dia_atual > st.session_state["max_demanda_historica"]:
        st.session_state["max_demanda_historica"] = demanda_maxima_dia_atual
        st.session_state["dia_max_demanda_historica"] = st.session_state["dia_atual"].strftime('%d/%m/%Y')
    
    demanda_maxima = demanda_maxima_dia_atual
    
    # Adiciona o consumo do dia atual (em tempo real) ao consumo acumulado
    consumo_dia_atual = (st.session_state["valores_A"]["consumo"][-1] - st.session_state["valores_A"]["consumo"][0]) + \
                       (st.session_state["valores_B"]["consumo"][-1] - st.session_state["valores_B"]["consumo"][0]) + \
                       (st.session_state["valores_C"]["consumo"][-1] - st.session_state["valores_C"]["consumo"][0]) if len(st.session_state["valores_A"]["consumo"]) > 1 else 0
    consumo_total_para_calculo = st.session_state["consumo_acumulado"] + consumo_dia_atual
else: # Dia Anterior
    df_A = dfs["A"][dfs["A"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]
    df_B = dfs["B"][dfs["B"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]
    df_C = dfs["C"][dfs["C"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]

    if not df_A.empty and not df_B.empty and not df_C.empty:
        min_len_df = min(len(df_A), len(df_B), len(df_C))
        
        df_A = df_A.iloc[:min_len_df]
        df_B = df_B.iloc[:min_len_df]
        df_C = df_C.iloc[:min_len_df]
        
        if len(df_A) >= demand_window:
            total_potencia_ativa_historico = df_A[colunas["A"]["potencia_ativa"]].add(df_B[colunas["B"]["potencia_ativa"]], fill_value=0).add(df_C[colunas["C"]["potencia_ativa"]], fill_value=0)
            demanda_maxima = total_potencia_ativa_historico.rolling(window=demand_window).mean().max()
        else:
            demanda_maxima = 0.0
    else:
        demanda_maxima = 0.0
    
    # Consumo total do dia anterior (já está no acumulado, então não precisa adicionar de novo)
    consumo_total_para_calculo = st.session_state["consumo_acumulado"]

# --- CÁLCULO DA CONTA ESTIMADA (AGORA ACUMULADA) ---
custo_bandeira_verde = TARIFAS["BANDEIRAS"]["Verde"]
custo_base_realtime = consumo_total_para_calculo * (TARIFAS["TE"] + TARIFAS["TUSD"] + custo_bandeira_verde)
impostos_realtime = custo_base_realtime * (TARIFAS["ICMS"] + TARIFAS["PIS"] + TARIFAS["COFINS"])
conta_estimada_acumulada = custo_base_realtime + impostos_realtime


st.markdown("<h3>Grandezas Totais e Demanda</h3>", unsafe_allow_html=True)
col7, col8, col9 = st.columns(3)

with col7:
    visor_total("Potência Aparente Total", S_total_inst, "VA", timestamp_ultimo_dado, limite_superior=POTENCIA_APARENTE_TOTAL_MAX)
with col8:
    visor_total("Fator de Potência Total", FP_total_inst, "", timestamp_ultimo_dado, limite_inferior=FATOR_POTENCIA_MIN)
with col9:
    visor_total("Demanda Máxima", demanda_maxima, "W", timestamp_ultimo_dado, limite_superior=DEMANDA_MAXIMA)

st.markdown("---")
st.markdown("<h3>Análise de Custo em Tempo Real</h3>", unsafe_allow_html=True)

col_conta = st.columns(1)[0]
with col_conta:
    st.markdown(f"""
    <div style='
        background-color: #2c3e50;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 15px;
    '>
        <h3 style='color:white; text-align:center;'>Análise de Custos e Demanda</h3>
        <div style='
            background-color: #34495e;
            color: #2ecc71;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            width: 100%;
        '>
            Consumo Acumulado: {consumo_total_para_calculo:.2f} kWh
            <br>
            Valor Estimado (acumulado): R$ {conta_estimada_acumulada:.2f}
        </div>
        <div style='
            background-color: #34495e;
            color: #2ecc71;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            width: 100%;
            margin-top: 10px;
        '>
            Maior Demanda Histórica: {st.session_state["max_demanda_historica"]:.2f} W
            <br>
            Dia da Ocorrência: {st.session_state["dia_max_demanda_historica"]}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- GRÁFICOS DINÂMICOS ---
st.markdown("<h3>Selecione o Gráfico</h3>", unsafe_allow_html=True)
col_left, col_right = st.columns([2, 3])

with col_left:
    st.button("Tensão", on_click=lambda: st.session_state.update(grafico_selecionado="Tensão"), use_container_width=True)
    st.button("Corrente", on_click=lambda: st.session_state.update(grafico_selecionado="Corrente"), use_container_width=True)

with col_right:
    st.button("Potência Aparente", on_click=lambda: st.session_state.update(grafico_selecionado="Potência Aparente"), use_container_width=True)
    st.button("Potência Aparente Total", on_click=lambda: st.session_state.update(grafico_selecionado="Potência Aparente Total"), use_container_width=True)
    st.button("Fator de Potência Total", on_click=lambda: st.session_state.update(grafico_selecionado="Fator de Potência Total"), use_container_width=True)

grafico_selecionado = st.session_state.get("grafico_selecionado", "Tensão")

fig = go.Figure()
cores = {"A": "#2980b9", "B": "#e67e22", "C": "#27ae60"}

grafico_key_map = {
    "Tensão": "tensao",
    "Corrente": "corrente",
    "Potência Aparente": "potencia"
}

plotted = False

if grafico_selecionado in ["Tensão", "Corrente", "Potência Aparente"]:
    for fase in ["A", "B", "C"]:
        if dia_escolhido == "Dia Atual":
            dados = st.session_state[f"valores_{fase}"]
            x_values = dados.get("timestamp", [])
            y_key = grafico_key_map.get(grafico_selecionado)
            if y_key and dados.get(y_key):
                y_data = dados[y_key]
                modo = "lines"
                plotted = True
            else:
                continue
        else:
            df_dia_anterior = dfs[fase][dfs[fase]["Timestamp"].dt.date == st.session_state["dia_anterior"]]
            if not df_dia_anterior.empty:
                y_key = grafico_key_map.get(grafico_selecionado)
                if y_key:
                    x_values = df_dia_anterior["Timestamp"].tolist()
                    y_data = df_dia_anterior[colunas[fase][y_key]].tolist()
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

elif grafico_selecionado in ["Potência Aparente Total", "Fator de Potência Total"]:
    if dia_escolhido == "Dia Atual":
        dados_A = st.session_state["valores_A"]
        dados_B = st.session_state["valores_B"]
        dados_C = st.session_state["valores_C"]
        
        min_len = min(len(dados_A["potencia_ativa"]), len(dados_B["potencia_ativa"]), len(dados_C["potencia_ativa"]))
        
        if min_len > 0:
            x_values = dados_A["timestamp"][:min_len]
            p_ativa_total = np.array(dados_A["potencia_ativa"][:min_len]) + np.array(dados_B["potencia_ativa"][:min_len]) + np.array(dados_C["potencia_ativa"][:min_len])
            p_reativa_total = np.array(dados_A["potencia_reativa"][:min_len]) + np.array(dados_B["potencia_reativa"][:min_len]) + np.array(dados_C["potencia_reativa"][:min_len])
            
            if grafico_selecionado == "Potência Aparente Total":
                y_data = np.sqrt(p_ativa_total**2 + p_reativa_total**2)
            elif grafico_selecionado == "Fator de Potência Total":
                y_data = p_ativa_total / np.sqrt(p_ativa_total**2 + p_reativa_total**2)
                y_data[np.isnan(y_data)] = 0
            
            fig.add_trace(go.Scatter(x=x_values, y=y_data, mode='lines', name="Total", line=dict(color="#3498db")))
            plotted = True
    else:
        df_A = dfs["A"][dfs["A"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]
        df_B = dfs["B"][dfs["B"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]
        df_C = dfs["C"][dfs["C"]["Timestamp"].dt.date == st.session_state["dia_anterior"]]
        
        if not df_A.empty and not df_B.empty and not df_C.empty:
            min_len_df = min(len(df_A), len(df_B), len(df_C))
            
            df_A = df_A.iloc[:min_len_df]
            df_B = df_B.iloc[:min_len_df]
            df_C = df_C.iloc[:min_len_df]
            
            x_values = df_A["Timestamp"]
            p_ativa_total = df_A[colunas["A"]["potencia_ativa"]].add(df_B[colunas["B"]["potencia_ativa"]], fill_value=0).add(df_C[colunas["C"]["potencia_ativa"]], fill_value=0)
            p_reativa_total = df_A[colunas["A"]["potencia_reativa"]].add(df_B[colunas["B"]["potencia_reativa"]], fill_value=0).add(df_C[colunas["C"]["potencia_reativa"]], fill_value=0)
            
            if grafico_selecionado == "Potência Aparente Total":
                y_data = np.sqrt(p_ativa_total**2 + p_reativa_total**2)
            elif grafico_selecionado == "Fator de Potência Total":
                y_data = p_ativa_total / np.sqrt(p_ativa_total**2 + p_reativa_total**2)
                y_data = y_data.fillna(0)
            
            fig.add_trace(go.Scatter(x=x_values, y=y_data, mode='lines', name="Total", line=dict(color="#3498db")))
            plotted = True

if plotted:
    if dia_escolhido == "Dia Atual":
        date_start = datetime.combine(st.session_state["dia_atual"], datetime.min.time())
        dia_referencia = st.session_state["dia_atual"]
    else:
        date_start = datetime.combine(st.session_state["dia_anterior"], datetime.min.time())
        dia_referencia = st.session_state["dia_anterior"]

    date_end = date_start + timedelta(days=1)
    
    if grafico_selecionado == "Tensão":
        fig.update_layout(title="Tensão nas Fases", yaxis_title="Tensão (V)", yaxis=dict(range=[190, 250]))
    elif grafico_selecionado == "Corrente":
        fig.update_layout(title="Corrente nas Fases", yaxis_title="Corrente (A)", yaxis=dict(range=[0, 300]))
    elif grafico_selecionado == "Potência Aparente":
        fig.update_layout(title="Potência Aparente nas Fases", yaxis_title="Potência Aparente (VA)")
    elif grafico_selecionado == "Potência Aparente Total":
        fig.update_layout(title="Potência Aparente Total", yaxis_title="Potência Aparente (VA)", yaxis=dict(range=[0, 400000]))
    elif grafico_selecionado == "Fator de Potência Total":
        fig.update_layout(title="Fator de Potência Total", yaxis_title="Fator de Potência", yaxis=dict(range=[0.6, 1.0]))

    fig.update_layout(
        xaxis_title="Data e Horário",
        # Formato para mostrar dia/mês e hora:minuto
        xaxis_tickformat='%d/%m %H:%M',
        xaxis=dict(
            tickmode='array',
            tickvals=[date_start + timedelta(hours=h) for h in range(25)],
            ticktext=[f'{dia_referencia.strftime("%d/%m")} {h:02d}:00' for h in range(25)],
            range=[date_start, date_end],
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        height=450,
        template="simple_white"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"Não há dados para exibir no gráfico de {grafico_selecionado} para o dia selecionado.")

# --- LOG DE ERROS (agora em um expander) ---
with st.expander("Log de alarmes"):
    if st.session_state["log_erros"]:
        for erro in reversed(st.session_state["log_erros"]):
            st.error(erro)
    else:
        st.info("Nenhum alarme registrado.")
