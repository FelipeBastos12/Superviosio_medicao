import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from collections import deque
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAÇÕES ---
CSV_PATH = "Planilha_242_LAT.csv"  # Altere conforme necessário
REFRESH_INTERVAL_MS = 1000

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Supervisório LAT", layout="wide")

# --- ESTILO DOS VISORES ---
def visor(valor, titulo, subtexto="", cor="#111", cor_texto="#00ffcc"):
    st.markdown(f"""
    <div style="
        background-color: {cor};
        color: {cor_texto};
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        font-family: 'Arial';
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
    ">
        <div style="font-size: 20px;">{titulo}</div>
        <div style="font-size: 36px; font-weight: bold;">{valor}</div>
        <div style="font-size: 14px; color: #aaa;">{subtexto}</div>
    </div>
    """, unsafe_allow_html=True)

def barra_potencia(valor, cor):
    percentual = int(valor * 100)
    st.markdown(f"""
    <div style="background: #333; border-radius: 8px; height: 25px; margin-bottom: 5px;">
      <div style="width: {percentual}%; background: {cor}; height: 100%; border-radius: 8px;"></div>
    </div>
    <div style="text-align: center; color: white;">{valor:.2f}</div>
    """, unsafe_allow_html=True)

# --- LEITURA DO CSV ---
@st.cache_data
def load_and_clean_csv(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
        try:
            df[col] = df[col].astype(float)
        except:
            pass
    return df

df = load_and_clean_csv(CSV_PATH)

# --- CONTROLE DE REFRESH ---
if "index" not in st.session_state:
    st.session_state.index = 0
count = st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")

# --- AVANÇA LINHA NO CSV ---
if st.session_state.index >= len(df):
    st.session_state.index = 0
row = df.iloc[st.session_state.index]
st.session_state.index += 1

# --- EXTRAI VALORES DAS FASES ---
def extrai(nome):
    return row.get(nome, 0.0)

# Tensão
t1 = extrai("Tensao_Fase_A")
t2 = extrai("Tensao_Fase_B")
t3 = extrai("Tensao_Fase_C")

# Frequência
f1 = extrai("Frequencia_Fase_A")
f2 = extrai("Frequencia_Fase_B")
f3 = extrai("Frequencia_Fase_C")

# Corrente
i1 = extrai("Corrente_Fase_A")
i2 = extrai("Corrente_Fase_B")
i3 = extrai("Corrente_Fase_C")

# Potência
fp1 = extrai("FP_Fase_A")
fp2 = extrai("FP_Fase_B")
fp3 = extrai("FP_Fase_C")

ea1 = extrai("Energia_Aparente_A")
ea2 = extrai("Energia_Aparente_B")
ea3 = extrai("Energia_Aparente_C")

er1 = extrai("Energia_Reativa_A")
er2 = extrai("Energia_Reativa_B")
er3 = extrai("Energia_Reativa_C")

ep1 = extrai("Energia_Ativa_A")
ep2 = extrai("Energia_Ativa_B")
ep3 = extrai("Energia_Ativa_C")

# --- HISTÓRICO PARA GRÁFICO ---
if "tensao_a" not in st.session_state:
    st.session_state.tensao_a = deque(maxlen=50)
    st.session_state.tensao_b = deque(maxlen=50)
    st.session_state.tensao_c = deque(maxlen=50)

st.session_state.tensao_a.append(t1)
st.session_state.tensao_b.append(t2)
st.session_state.tensao_c.append(t3)

# --- LINHA 1: TENSÕES ---
col1, col2, col3 = st.columns(3)
with col1:
    visor(f"{t1:.0f} V", "Fase 1", f"{f1:.0f} Hz", "#111", "#00ff00")
with col2:
    visor(f"{t2:.0f} V", "Fase 2", f"{f2:.0f} Hz", "#111", "#ff0000")
with col3:
    visor(f"{t3:.0f} V", "Fase 3", f"{f3:.0f} Hz", "#111", "#0099ff")

# --- GRÁFICO DE TENSÃO ---
st.markdown("### Gráfico de Tensão (V)")
fig = go.Figure()
fig.add_trace(go.Scatter(y=list(st.session_state.tensao_a), name="Fase A", line=dict(color="blue")))
fig.add_trace(go.Scatter(y=list(st.session_state.tensao_b), name="Fase B", line=dict(color="red")))
fig.add_trace(go.Scatter(y=list(st.session_state.tensao_c), name="Fase C", line=dict(color="orange")))
fig.update_layout(
    xaxis_title="Amostras",
    yaxis_title="Tensão (V)",
    template="plotly_dark",
    height=400
)
st.plotly_chart(fig, use_container_width=True)

# --- LINHA 2: ENERGIAS APARENTES ---
col4, col5, col6 = st.columns(3)
with col4:
    visor(f"{ea1:.2f} VA", "Fase 1", "", "#111", "#00ffcc")
with col5:
    visor(f"{ea2:.2f} VA", "Fase 2", "", "#111", "#ff4444")
with col6:
    visor(f"{ea3:.2f} VA", "Fase 3", "", "#111", "#3399ff")

# --- LINHA 3: ENERGIA ATIVA / CORRENTE / REATIVA ---
col7, col8, col9 = st.columns(3)
with col7:
    visor(f"{ep1:.2f} W", "Fase 1", "", "#111", "#00ffcc")
    visor(f"{ep2:.2f} W", "Fase 2", "", "#111", "#ff4444")
    visor(f"{ep3:.2f} W", "Fase 3", "", "#111", "#3399ff")
with col8:
    visor(f"{i1:.2f} A", "Corrente Fase 1", "", "#111", "#00ffcc")
    visor(f"{i2:.2f} A", "Corrente Fase 2", "", "#111", "#ff4444")
    visor(f"{i3:.2f} A", "Corrente Fase 3", "", "#111", "#3399ff")
with col9:
    visor(f"{er1:.2f} VAr", "Fase 1", "", "#111", "#00ffcc")
    visor(f"{er2:.2f} VAr", "Fase 2", "", "#111", "#ff4444")
    visor(f"{er3:.2f} VAr", "Fase 3", "", "#111", "#3399ff")

# --- FATOR DE POTÊNCIA ---
st.markdown("### Fator de Potência")
col10, col11, col12 = st.columns(3)
with col10:
    barra_potencia(fp1, "#ffff00")
with col11:
    barra_potencia(fp2, "#ff3333")
with col12:
    barra_potencia(fp3, "#00ccff")

media_fp = (fp1 + fp2 + fp3) / 3
st.markdown(f"**Média do fator de potência:** :green[{media_fp:.2f}]")
