import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import numpy as np

# --- CONFIGURAÇÕES ---
PATHS = {
    "A": "Medicoes_FASEA.csv",
    "B": "Medicoes_FASEB.csv",
    "C": "Medicoes_FASEC.csv"
}
REFRESH_INTERVAL_MS = 500

# --- LIMITES DE OPERAÇÃO ---
TENSÃO_MIN = 200.0  # Volts
TENSÃO_MAX = 240.0  # Volts
CORRENTE_MAX = 20.0  # Amperes
POTENCIA_APARENTE_MAX = 4500.0  # VA (por fase)
POTENCIA_APARENTE_TOTAL_MAX = 12000.0 # VA (total)
FREQUENCIA_MIN = 59.5 # Hz (para sistema 60Hz)
FREQUENCIA_MAX = 60.5 # Hz (para sistema 60Hz)
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
            "tensao": [], "corrente": [], "potencia": [], "timestamp": [],
            "potencia_ativa": [], "potencia_reativa": []
        }
    if f"corrente_anterior_{fase}" not in st.session_state:
        st.session_state[f"corrente_anterior_{fase}"] = 0.0
        
if "grafico_selecionado" not in st.session_state:
    st.session_state["grafico_selecionado"] = "Tensão"

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
        st.session_state[f"index_{fase}"] = 0
        st.session_state[f"valores_{fase}"]["tensao"] = []
        st.session_state[f"valores_{fase}"]["corrente"] = []
        st.session_state[f"valores_{fase}"]["potencia"] = []
        st.session_state[f"valores_{fase}"]["timestamp"] = []
        st.session_state[f"valores_{fase}"]["potencia_ativa"] = []
        st.session_state[f"valores_{fase}"]["potencia_reativa"] = []
        
    idx = st.session_state[f"index_{fase}"]
    row = df.iloc[idx]
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
            dados_sessao = st.session_state[f"valores_{fase}"]
            if dados_sessao["timestamp"]:
                last_idx = len(dados_sessao["timestamp"]) - 1
                tensao = dados_sessao["tensao"][last_idx]
                corrente = dados_sessao["corrente"][last_idx]
                potencia = dados_sessao["potencia"][last_idx]
                potencia_ativa = dados_sessao["potencia_ativa"][last_idx]
                potencia_reativa = dados_sessao["potencia_reativa"][last_idx]
                row = df.iloc[st.session_state[f"index_{fase}"] - 1]
                frequencia = row.get(colunas[fase]["frequencia"], 0)
                fator_potencia = row.get(colunas[fase]["fator_de_potencia"], 0)
                consumo = row.get(colunas[fase]["consumo"], 0)
            else:
                tensao, corrente, potencia, frequencia, fator_potencia, consumo = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                potencia_ativa, potencia_reativa = 0.0, 0.0
        else:  # Dia Anterior
            row = df.iloc[-1]
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

# --- VISOR PERSONALIZADO ---
def visor_fases(label, valores_por_fase, unidade):
    cor_fundo_default = "#2c3e50"
    cor_fundo_alerta = "#c0392b"
    cor_fundo_atual = cor_fundo_default
    
    # Define as cores do texto e verifica alarmes
    cores_texto = {}
    for fase in ["A", "B", "C"]:
        if label == "Tensão":
            if TENSÃO_MIN <= valores_por_fase[fase] <= TENSÃO_MAX:
                cores_texto[fase] = "#2ecc71" # Verde
            else:
                cores_texto[fase] = "#c0392b" # Vermelho
                cor_fundo_atual = cor_fundo_alerta # Aciona o alarme de fundo
        elif label == "Corrente":
            cores_texto[fase] =  "#2ecc71" # Verde
            if valores_por_fase[fase] > CORRENTE_MAX:
                cor_fundo_atual = cor_fundo_alerta
        elif label == "Potência Aparente":
            cores_texto[fase] =  "#2ecc71" # Verde
            if valores_por_fase[fase] > POTENCIA_APARENTE_MAX:
                cor_fundo_atual = cor_fundo_alerta
        elif label == "Frequência":
            cores_texto[fase] =  "#2ecc71" # Verde
            if not (FREQUENCIA_MIN <= valores_por_fase[fase] <= FREQUENCIA_MAX):
                cor_fundo_atual = cor_fundo_alerta
        elif label == "Fator de Potência":
            cores_texto[fase] =  "#2ecc71" # Verde
            if valores_por_fase[fase] < FATOR_POTENCIA_MIN:
                cor_fundo_atual = cor_fundo_alerta
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
def visor_total(label, valor_total, unidade, limite_superior=None, limite_inferior=None):
    cor_fundo_default = "#2c3e50"
    cor_fundo_alerta = "#c0392b"
    cor_fundo_atual = cor_fundo_default
    
    alarme_acionado = False
    if limite_superior is not None and valor_total > limite_superior:
        alarme_acionado = True
    if limite_inferior is not None and valor_total < limite_inferior:
        alarme_acionado = True
    
    if alarme_acionado:
        cor_fundo_atual = cor_fundo_alerta

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
            color: #ffffff;
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
    visor_fases("Tensão", valores_tensao, "V")
with col2:
    visor_fases("Corrente", valores_corrente, "A")
with col3:
    visor_fases("Frequência", valores_frequencia, "Hz")

col4, col5, col6 = st.columns(3)

with col4:
    visor_fases("Potência Aparente", valores_potencia, "VA")
with col5:
    visor_fases("Fator de Potência", valores_fator_potencia, "")
with col6:
    visor_fases("Consumo", valores_consumo, "kWh")


# --- CÁLCULOS DOS VALORES TOTAIS E DEMANDA ---
P_total_inst = sum(valores_potencia_ativa.values())
Q_total_inst = sum(valores_potencia_reativa.values())
S_total_inst = np.sqrt(P_total_inst**2 + Q_total_inst**2)
FP_total_inst = P_total_inst / S_total_inst if S_total_inst != 0 else 0

# Para demanda, vamos calcular a média móvel da potência ativa total
demand_window = 5 # 5 pontos de 3min = 15 minutos
if dia_escolhido == "Dia Atual":
    potencia_ativa_faseA = st.session_state["valores_A"]["potencia_ativa"]
    potencia_ativa_faseB = st.session_state["valores_B"]["potencia_ativa"]
    potencia_ativa_faseC = st.session_state["valores_C"]["potencia_ativa"]
    
    if len(potencia_ativa_faseA) >= demand_window:
        total_potencia_ativa_historico = [sum(p) for p in zip(potencia_ativa_faseA, potencia_ativa_faseB, potencia_ativa_faseC)]
        total_series = pd.Series(total_potencia_ativa_historico)
        demanda_maxima = total_series.rolling(window=demand_window).mean().max()
    else:
        demanda_maxima = 0.0
else: # Dia Anterior
    potencia_ativa_faseA = dfs["A"][colunas["A"]["potencia_ativa"]]
    potencia_ativa_faseB = dfs["B"][colunas["B"]["potencia_ativa"]]
    potencia_ativa_faseC = dfs["C"][colunas["C"]["potencia_ativa"]]

    if not potencia_ativa_faseA.empty and len(potencia_ativa_faseA) >= demand_window:
        total_potencia_ativa_historico = potencia_ativa_faseA.add(potencia_ativa_faseB, fill_value=0).add(potencia_ativa_faseC, fill_value=0)
        demanda_maxima = total_potencia_ativa_historico.rolling(window=demand_window).mean().max()
    else:
        demanda_maxima = 0.0

st.markdown("<h3>Grandezas Totais e Demanda</h3>", unsafe_allow_html=True)
col7, col8, col9 = st.columns(3)

with col7:
    visor_total("Potência Aparente Total", S_total_inst, "VA", limite_superior=POTENCIA_APARENTE_TOTAL_MAX)
with col8:
    visor_total("Fator de Potência Total", FP_total_inst, "", limite_inferior=FATOR_POTENCIA_MIN)
with col9:
    visor_total("Demanda Máxima", demanda_maxima, "W", limite_superior=DEMANDA_MAXIMA)


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

# Plotagem dos gráficos por fase
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
# Plotagem dos gráficos totais
elif grafico_selecionado in ["Potência Aparente Total", "Fator de Potência Total"]:
    if dia_escolhido == "Dia Atual":
        dados_A = st.session_state["valores_A"]
        dados_B = st.session_state["valores_B"]
        dados_C = st.session_state["valores_C"]
        
        if dados_A["timestamp"] and dados_B["timestamp"] and dados_C["timestamp"]:
            x_values = dados_A["timestamp"]
            p_ativa_total = np.array(dados_A["potencia_ativa"]) + np.array(dados_B["potencia_ativa"]) + np.array(dados_C["potencia_ativa"])
            p_reativa_total = np.array(dados_A["potencia_reativa"]) + np.array(dados_B["potencia_reativa"]) + np.array(dados_C["potencia_reativa"])
            
            if grafico_selecionado == "Potência Aparente Total":
                y_data = np.sqrt(p_ativa_total**2 + p_reativa_total**2)
            else: # Fator de Potência Total
                y_data = p_ativa_total / np.sqrt(p_ativa_total**2 + p_reativa_total**2)
                y_data[np.isnan(y_data)] = 0 # Substitui NaNs por 0 se houver divisao por zero
            
            fig.add_trace(go.Scatter(x=x_values, y=y_data, mode='lines', name="Total", line=dict(color="#3498db")))
            plotted = True
    else: # Dia Anterior
        df_A = dfs["A"]
        df_B = dfs["B"]
        df_C = dfs["C"]
        
        if not df_A.empty and not df_B.empty and not df_C.empty:
            x_values = df_A["Timestamp"]
            p_ativa_total = df_A[colunas["A"]["potencia_ativa"]].add(df_B[colunas["B"]["potencia_ativa"]], fill_value=0).add(df_C[colunas["C"]["potencia_ativa"]], fill_value=0)
            p_reativa_total = df_A[colunas["A"]["potencia_reativa"]].add(df_B[colunas["B"]["potencia_reativa"]], fill_value=0).add(df_C[colunas["C"]["potencia_reativa"]], fill_value=0)
            
            if grafico_selecionado == "Potência Aparente Total":
                y_data = np.sqrt(p_ativa_total**2 + p_reativa_total**2)
            else: # Fator de Potência Total
                y_data = p_ativa_total / np.sqrt(p_ativa_total**2 + p_reativa_total**2)
                y_data = y_data.fillna(0) # Substitui NaNs por 0
            
            fig.add_trace(go.Scatter(x=x_values, y=y_data, mode='lines', name="Total", line=dict(color="#3498db")))
            plotted = True


if plotted:
    date_23_05 = datetime(2025, 5, 23)
    
    if grafico_selecionado == "Tensão":
        fig.update_layout(title="Tensão nas Fases", yaxis_title="Tensão (V)", yaxis=dict(range=[190, 250]))
    elif grafico_selecionado == "Corrente":
        fig.update_layout(title="Corrente nas Fases", yaxis_title="Corrente (A)")
    elif grafico_selecionado == "Potência Aparente":
        fig.update_layout(title="Potência Aparente nas Fases", yaxis_title="Potência Aparente (VA)")
    elif grafico_selecionado == "Potência Aparente Total":
        fig.update_layout(title="Potência Aparente Total", yaxis_title="Potência Aparente (VA)")
    elif grafico_selecionado == "Fator de Potência Total":
        fig.update_layout(title="Fator de Potência Total", yaxis_title="Fator de Potência", yaxis=dict(range=[-0.1, 1.1]))

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


