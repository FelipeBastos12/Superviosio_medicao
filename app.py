import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta, date
import numpy as np
import collections

# --- CONFIGURAÇÕES ---
# O ideal é que os arquivos Planilha_242_LAT contenham dados de 01/08, 02/08, etc.
# Assumindo que você tem arquivos com essas datas.
PATHS = {
    "A": "Planilha_242_LAT - FASEA (3).csv",
    "B": "Planilha_242_LAT - FASEB (3).csv",
    "C": "Planilha_242_LAT - FASEC (3).csv"
}
REFRESH_INTERVAL_MS = 100 # Reduzido para 100ms para ver a mudança

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

# Carregar os dados de todas as fases de uma vez
dfs_raw = {fase: load_and_clean_csv(path) for fase, path in PATHS.items()}

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Supervisório LAT Trifásico", layout="wide")

# --- AUTOREFRESH (agora sempre ativo) ---
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- LÓGICA DE PROGRESSÃO DE DATAS ---
# Encontrar todas as datas únicas nos dados
combined_timestamps = pd.concat([df['Timestamp'] for df in dfs_raw.values() if not df.empty])
unique_dates = sorted(combined_timestamps.dt.date.unique())

if not unique_dates:
    st.error("Não há dados para exibir. Por favor, verifique os arquivos CSV.")
    st.stop()

# Inicialização do estado de data
if "current_live_date" not in st.session_state:
    # A sua solicitação foi para iniciar com 01/08 e 02/08.
    # No entanto, os arquivos fornecidos possuem apenas dados de 23/05/2025 e 03/08/2025.
    # Para o código funcionar, ele usará as duas primeiras datas disponíveis,
    # mas a lógica está pronta para começar com 01/08 e 02/08 se os arquivos corretos forem fornecidos.
    
    # Se houver mais de uma data, inicia com as duas primeiras
    if len(unique_dates) > 1:
        st.session_state.previous_live_date = unique_dates[0]
        st.session_state.current_live_date = unique_dates[1]
    else: # Caso haja apenas uma data
        st.session_state.previous_live_date = unique_dates[0]
        st.session_state.current_live_date = unique_dates[0]

    st.session_state.all_available_dates = unique_dates

# --- INICIALIZAÇÃO E RESET DE SESSION STATE PARA DADOS ---
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

if "log_erros" not in st.session_state:
    st.session_state["log_erros"] = collections.deque(maxlen=10)


# --- Layout com logo e título lado a lado ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("FDJ_engenharia.jpg", width=500)
with col_titulo:
    st.markdown("<h1 style='padding-top: 90px;'>Supervisório de Medição Elétrica</h1>", unsafe_allow_html=True)

# --- FUNÇÃO PARA ATUALIZAR DADOS DO DIA ATUAL E AVANÇAR O DIA ---
def atualizar_dados_dia_atual(fase, df):
    df_dia_atual = df[df['Timestamp'].dt.date == st.session_state.current_live_date]
    if df_dia_atual.empty:
        return
    
    # Verifica se a leitura do dia atual terminou
    if st.session_state[f"index_{fase}"] >= len(df_dia_atual):
        current_idx = st.session_state.all_available_dates.index(st.session_state.current_live_date)
        
        # Avança para o próximo dia se houver
        if current_idx + 1 < len(st.session_state.all_available_dates):
            st.session_state.previous_live_date = st.session_state.current_live_date
            st.session_state.current_live_date = st.session_state.all_available_dates[current_idx + 1]
            
            # Reseta todos os estados para o novo dia
            st.session_state[f"index_{fase}"] = 0
            st.session_state[f"valores_{fase}"] = {
                "tensao": [], "corrente": [], "potencia": [], "timestamp": [],
                "potencia_ativa": [], "potencia_reativa": []
            }
            # Limpa o log de erros
            st.session_state["log_erros"] = collections.deque(maxlen=10)
        else:
            # Chegou no último dia disponível, para de avançar
            st.warning(f"Fim da leitura dos dados. Aguardando novos dados...")
            return

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
    atualizar_dados_dia_atual(fase, dfs_raw[fase])

# --- SELETOR DE DIA ---
dia_atual_str = st.session_state.current_live_date.strftime('%d/%m/%Y') + " (Dia Atual)"
dia_anterior_str = st.session_state.previous_live_date.strftime('%d/%m/%Y') + " (Dia Anterior)"
dia_escolhido_str = st.radio("Selecionar dia para visualização:", (dia_atual_str, dia_anterior_str))
if dia_escolhido_str.endswith(" (Dia Atual)"):
    dia_escolhido = st.session_state.current_live_date
else:
    dia_escolhido = st.session_state.previous_live_date

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
    df = dfs_raw[fase]
    df_filtrado = df[df['Timestamp'].dt.date == dia_escolhido]
    
    if df_filtrado.empty:
        tensao, corrente, potencia, frequencia, fator_potencia, consumo = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        potencia_ativa, potencia_reativa = 0.0, 0.0
    else:
        if dia_escolhido == st.session_state.current_live_date:
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

timestamp_ultimo_dado = st.session_state["valores_A"]["timestamp"][-1] if st.session_state["valores_A"]["timestamp"] and dia_escolhido == st.session_state.current_live_date else datetime.now()


# --- VISOR PERSONALIZADO ---
def visor_fases(label, valores_por_fase, unidade, timestamp_erro):
    cor_fundo_default = "#2c3e50"
    cor_fundo_alerta = "#c0392b"
    cor_fundo_atual = cor_fundo_default
    
    cores_texto = {}
    for fase in ["A", "B", "C"]:
        valor = valores_por_fase[fase]
        if label == "Tensão":
            if TENSÃO_MIN <= valor <= TENSÃO_MAX: cores_texto[fase] = "#2ecc71"
            else: cores_texto[fase] = "#c0392b"; cor_fundo_atual = cor_fundo_alerta; st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Tensão na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Corrente":
            cores_texto[fase] =  "#2ecc71"
            if valor > CORRENTE_MAX: cores_texto[fase] = "#c0392b"; cor_fundo_atual = cor_fundo_alerta; st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Corrente na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Potência Aparente":
            cores_texto[fase] =  "#2ecc71"
            if valor > POTENCIA_APARENTE_MAX: cores_texto[fase] = "#c0392b"; cor_fundo_atual = cor_fundo_alerta; st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Potência na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Frequência":
            cores_texto[fase] =  "#2ecc71"
            if not (FREQUENCIA_MIN <= valor <= FREQUENCIA_MAX): cores_texto[fase] = "#c0392b"; cor_fundo_atual = cor_fundo_alerta; st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Frequência na Fase {fase}: {valor:.2f} {unidade}")
        elif label == "Fator de Potência":
            cores_texto[fase] =  "#2ecc71"
            if valor < FATOR_POTENCIA_MIN: cores_texto[fase] = "#c0392b"; cor_fundo_atual = cor_fundo_alerta; st.session_state["log_erros"].append(f"[{timestamp_erro.strftime('%H:%M:%S')}] ALARME de Fator de Potência na Fase {fase}: {valor:.2f}")
        else:
            cores_texto[fase] =  "#2ecc71"
    
    st.markdown(f"""
    <div style='background-color: {cor_fundo_atual}; padding: 15px; border-radius: 15px; margin-bottom: 15px;'>
        <h3 style='color:white; text-align:center;'>{label}</h3>
        <div style='display: flex; flex-direction: column; gap: 10px;'>
            <div style='background-color: #34495e; color: {cores_texto["A"]}; padding: 15px; border-radius: 10px; text-align: center; font-size: 20px; font-weight: bold; width: 100%;'>
                Fase A: {valores_por_fase["A"]:.2f} {unidade}
            </div>
            <div style='background-color: #34495e; color: {cores_texto["B"]}; padding: 15px; border-radius: 10px; text-align: center; font-size: 20px; font-weight: bold; width: 100%;'>
                Fase B: {valores_por_fase["B"]:.2f} {unidade}
            </div>
            <div style='background-color: #34495e; color: {cores_texto["C"]}; padding: 15px; border-radius: 10px; text-align: center; font-size: 20px; font-weight: bold; width: 100%;'>
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
    <div style='background-color: {cor_fundo_atual}; padding: 15px; border-radius: 15px; margin-bottom: 15px;'>
        <h3 style='color:white; text-align:center;'>{label}</h3>
        <div style='background-color: #34495e; color: {cor_texto_atual}; padding: 15px; border-radius: 10px; text-align: center; font-size: 20px; font-weight: bold; width: 100%;'>
            Total: {valor_total:.2f} {unidade}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<h3>Grandezas por Fase</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1: visor_fases("Tensão", valores_tensao, "V", timestamp_ultimo_dado)
with col2: visor_fases("Corrente", valores_corrente, "A", timestamp_ultimo_dado)
with col3: visor_fases("Frequência", valores_frequencia, "Hz", timestamp_ultimo_dado)
col4, col5, col6 = st.columns(3)
with col4: visor_fases("Potência Aparente", valores_potencia, "VA", timestamp_ultimo_dado)
with col5: visor_fases("Fator de Potência", valores_fator_potencia, "", timestamp_ultimo_dado)
with col6: visor_fases("Consumo", valores_consumo, "kWh", timestamp_ultimo_dado)

# --- CÁLCULOS DOS VALORES TOTAIS E DEMANDA ---
P_total_inst = sum(valores_potencia_ativa.values())
Q_total_inst = sum(valores_potencia_reativa.values())
S_total_inst = np.sqrt(P_total_inst**2 + Q_total_inst**2)
FP_total_inst = P_total_inst / S_total_inst if S_total_inst != 0 else 0

demand_window = 5 # 5 pontos de 3min = 15 minutos
if dia_escolhido == st.session_state.current_live_date:
    potencia_ativa_faseA = st.session_state["valores_A"]["potencia_ativa"]
    potencia_ativa_faseB = st.session_state["valores_B"]["potencia_ativa"]
    potencia_ativa_faseC = st.session_state["valores_C"]["potencia_ativa"]
    if len(potencia_ativa_faseA) >= demand_window:
        total_potencia_ativa_historico = [sum(p) for p in zip(potencia_ativa_faseA, potencia_ativa_faseB, potencia_ativa_faseC)]
        total_series = pd.Series(total_potencia_ativa_historico)
        demanda_maxima = total_series.rolling(window=demand_window).mean().max()
    else: demanda_maxima = 0.0
else:
    df_A_prev = dfs_raw["A"][dfs_raw["A"]['Timestamp'].dt.date == dia_escolhido]
    df_B_prev = dfs_raw["B"][dfs_raw["B"]['Timestamp'].dt.date == dia_escolhido]
    df_C_prev = dfs_raw["C"][dfs_raw["C"]['Timestamp'].dt.date == dia_escolhido]
    if not df_A_prev.empty and len(df_A_prev) >= demand_window:
        total_potencia_ativa_historico = df_A_prev[colunas["A"]["potencia_ativa"]].add(df_B_prev[colunas["B"]["potencia_ativa"]], fill_value=0).add(df_C_prev[colunas["C"]["potencia_ativa"]], fill_value=0)
        demanda_maxima = total_potencia_ativa_historico.rolling(window=demand_window).mean().max()
    else: demanda_maxima = 0.0

st.markdown("<h3>Grandezas Totais e Demanda</h3>", unsafe_allow_html=True)
col7, col8, col9 = st.columns(3)
with col7: visor_total("Potência Aparente Total", S_total_inst, "VA", timestamp_ultimo_dado, limite_superior=POTENCIA_APARENTE_TOTAL_MAX)
with col8: visor_total("Fator de Potência Total", FP_total_inst, "", timestamp_ultimo_dado, limite_inferior=FATOR_POTENCIA_MIN)
with col9: visor_total("Demanda Máxima", demanda_maxima, "W", timestamp_ultimo_dado, limite_superior=DEMANDA_MAXIMA)


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
dia_do_grafico_timestamp = datetime.combine(dia_escolhido, datetime.min.time())
grafico_key_map = {"Tensão": "tensao", "Corrente": "corrente", "Potência Aparente": "potencia"}
plotted = False

if grafico_selecionado in ["Tensão", "Corrente", "Potência Aparente"]:
    for fase in ["A", "B", "C"]:
        if dia_escolhido == st.session_state.current_live_date:
            dados = st.session_state[f"valores_{fase}"]
            x_values = dados.get("timestamp", [])
            y_key = grafico_key_map.get(grafico_selecionado)
            if y_key and dados.get(y_key):
                y_data = dados[y_key]
                modo = "lines"; plotted = True
            else: continue
        else:
            df_filtrado = dfs_raw[fase][dfs_raw[fase]['Timestamp'].dt.date == dia_escolhido]
            if not df_filtrado.empty:
                y_key = grafico_key_map.get(grafico_selecionado)
                if y_key:
                    x_values = df_filtrado["Timestamp"].tolist()
                    y_data = df_filtrado[colunas[fase][y_key]].tolist()
                    modo = "lines"; plotted = True
                else: continue
            else: continue
        if plotted: fig.add_trace(go.Scatter(x=x_values, y=y_data, mode=modo, name=f"Fase {fase}", line=dict(color=cores[fase])))

elif grafico_selecionado in ["Potência Aparente Total", "Fator de Potência Total"]:
    if dia_escolhido == st.session_state.current_live_date:
        dados_A, dados_B, dados_C = st.session_state["valores_A"], st.session_state["valores_B"], st.session_state["valores_C"]
        if dados_A["timestamp"] and dados_B["timestamp"] and dados_C["timestamp"]:
            x_values = dados_A["timestamp"]
            p_ativa_total = np.array(dados_A["potencia_ativa"]) + np.array(dados_B["potencia_ativa"]) + np.array(dados_C["potencia_ativa"])
            p_reativa_total = np.array(dados_A["potencia_reativa"]) + np.array(dados_B["potencia_reativa"]) + np.array(dados_C["potencia_reativa"])
            if grafico_selecionado == "Potência Aparente Total": y_data = np.sqrt(p_ativa_total**2 + p_reativa_total**2)
            elif grafico_selecionado == "Fator de Potência Total": y_data = p_ativa_total / np.sqrt(p_ativa_total**2 + p_reativa_total**2); y_data[np.isnan(y_data)] = 0
            fig.add_trace(go.Scatter(x=x_values, y=y_data, mode='lines', name="Total", line=dict(color="#3498db"))); plotted = True
    else:
        df_A_prev = dfs_raw["A"][dfs_raw["A"]['Timestamp'].dt.date == dia_escolhido]
        df_B_prev = dfs_raw["B"][dfs_raw["B"]['Timestamp'].dt.date == dia_escolhido]
        df_C_prev = dfs_raw["C"][dfs_raw["C"]['Timestamp'].dt.date == dia_escolhido]
        if not df_A_prev.empty and not df_B_prev.empty and not df_C_prev.empty:
            x_values = df_A_prev["Timestamp"]
            p_ativa_total = df_A_prev[colunas["A"]["potencia_ativa"]].add(df_B_prev[colunas["B"]["potencia_ativa"]], fill_value=0).add(df_C_prev[colunas["C"]["potencia_ativa"]], fill_value=0)
            p_reativa_total = df_A_prev[colunas["A"]["potencia_reativa"]].add(df_B_prev[colunas["B"]["potencia_reativa"]], fill_value=0).add(df_C_prev[colunas["C"]["potencia_reativa"]], fill_value=0)
            if grafico_selecionado == "Potência Aparente Total": y_data = np.sqrt(p_ativa_total**2 + p_reativa_total**2)
            elif grafico_selecionado == "Fator de Potência Total": y_data = p_ativa_total / np.sqrt(p_ativa_total**2 + p_reativa_total**2); y_data = y_data.fillna(0)
            fig.add_trace(go.Scatter(x=x_values, y=y_data, mode='lines', name="Total", line=dict(color="#3498db"))); plotted = True

if plotted:
    title_text = f"{grafico_selecionado} - {dia_escolhido.strftime('%d/%m/%Y')}"
    if grafico_selecionado == "Tensão": fig.update_layout(title=title_text, yaxis_title="Tensão (V)", yaxis=dict(range=[190, 250]))
    elif grafico_selecionado == "Corrente": fig.update_layout(title=title_text, yaxis_title="Corrente (A)", yaxis=dict(range=[0, 300]))
    elif grafico_selecionado == "Potência Aparente": fig.update_layout(title=title_text, yaxis_title="Potência Aparente (VA)")
    elif grafico_selecionado == "Potência Aparente Total": fig.update_layout(title=title_text, yaxis_title="Potência Aparente (VA)", yaxis=dict(range=[0, 400000]))
    elif grafico_selecionado == "Fator de Potência Total": fig.update_layout(title=title_text, yaxis_title="Fator de Potência", yaxis=dict(range=[0.6, 1.0]))
    fig.update_layout(xaxis_title="Horário", xaxis_tickformat='%H:%M', xaxis=dict(tickmode='array', tickvals=[dia_do_grafico_timestamp + timedelta(hours=h) for h in range(25)], ticktext=[f'{h:02d}:00' for h in range(25)], range=[dia_do_grafico_timestamp, dia_do_grafico_timestamp + timedelta(days=1)], showgrid=True, gridcolor='rgba(128,128,128,0.2)'), height=450, template="simple_white")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"Não há dados para exibir no gráfico de {grafico_selecionado} no dia {dia_escolhido.strftime('%d/%m/%Y')}.")

with st.expander("Log de alarmes"):
    if st.session_state["log_erros"]:
        for erro in reversed(st.session_state["log_erros"]):
            st.error(erro)
    else:
        st.info("Nenhum alarme registrado.")

