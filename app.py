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
st.title("🔌 Supervisório LAT – Fases A, B e C")

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

# --- VISOR PERSONALIZADO ---
def visor(valor, label, cor_fundo, cor_texto):
    return f"""
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
    """

# --- ATUALIZAÇÃO DOS DADOS POR FASE ---
for fase in ["A", "B", "C"]:
    df = dfs[fase]
    idx = st.session_state[f"index_{fase}"]
    if idx >= len(df):
        st.session_state[f"index_{fase}"] = 0
        idx = 0
        st.success(f"Reiniciando dados da fase {fase}")
    row = df.iloc[idx]
    st.session_state[f"index_{fase}"] += 1

    # Extrai dados
    tensao = row.get(colunas[fase]["tensao"], None)
    corrente = row.get(colunas[fase]["corrente"], None)
    potencia = row.get(colunas[fase]["potencia"], None)
    frequencia = row.get(colunas[fase]["frequencia"], None)

    # Corrente zero → mantém anterior
    if corrente == 0:
        corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
    else:
        st.session_state[f"corrente_anterior_{fase}"] = corrente

    # Atualiza buffers para gráfico
    if tensao is not None:
        st.session_state[f"valores_{fase}"]["tensao"].append(float(tensao))
        st.session_state[f"valores_{fase}"]["tensao"] = st.session_state[f"valores_{fase}"]["tensao"][-50:]
    if corrente is not None:
        st.session_state[f"valores_{fase}"]["corrente"].append(float(corrente))
        st.session_state[f"valores_{fase}"]["corrente"] = st.session_state[f"valores_{fase}"]["corrente"][-50:]
    if potencia is not None:
        st.session_state[f"valores_{fase}"]["potencia"].append(float(potencia))
        st.session_state[f"valores_{fase}"]["potencia"] = st.session_state[f"valores_{fase}"]["potencia"][-50:]

# --- VISUALIZAÇÃO AGRUPADA DOS VISORS ---
def cor_tensao(valor):
    return "#2ecc71" if valor >= 210 else "#c0392b"
    
def criar_visor_agrupado_interno(titulo, unidade, cor_fundo):
    """
    Função para criar um único visor grande com os dados das 3 fases dentro,
    como mostrado na imagem.
    """
    conteudo_visor = f"<h4 style='text-align: center;'>{titulo}</h4>"
    conteudo_corpo = ""
    for fase in ["A", "B", "C"]:
        valor = None
        cor_texto_fase = "#ffffff"

        # Tensão
        if titulo == "Tensão":
            valor = st.session_state[f"valores_{fase}"]["tensao"][-1] if st.session_state[f"valores_{fase}"]["tensao"] else None
            if valor is not None:
                cor_texto_fase = cor_tensao(valor)
                valor = f"{valor:.1f}"

        # Corrente
        elif titulo == "Corrente":
            valor = st.session_state[f"valores_{fase}"]["corrente"][-1] if st.session_state[f"valores_{fase}"]["corrente"] else None
            if valor is not None:
                valor = f"{valor:.2f}"

        # Potência Ativa
        elif titulo == "Potência Ativa":
            valor = st.session_state[f"valores_{fase}"]["potencia"][-1] if st.session_state[f"valores_{fase}"]["potencia"] else None
            if valor is not None:
                valor = f"{valor:.2f}"
                
        # Frequência (pega o valor da Fase A e aplica para B e C)
        elif titulo == "Frequência":
            try:
                if fase == "A":
                    valor = dfs["A"].iloc[st.session_state["index_A"]-1].get(colunas["A"]["frequencia"], None)
                    st.session_state['frequencia_ultima'] = valor
                else:
                    valor = st.session_state.get('frequencia_ultima', None)
            except:
                valor = None
            if valor is not None:
                valor = f"{float(valor):.2f}"

        if valor is not None:
            conteudo_corpo += f"""
                <div style='
                    color: {cor_texto_fase};
                    padding: 5px;
                    text-align: left;
                    font-size: 20px;
                    font-weight: bold;
                '>
                    Fase {fase}: {valor} {unidade}
                </div>
            """
    
    # Monta o visor completo dentro de um container principal
    return f"""
    <div style='
        background-color: {cor_fundo};
        color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    '>
        {conteudo_visor}
        {conteudo_corpo}
    </div>
    """

col_tensao, col_corrente, col_potencia, col_frequencia = st.columns(4)

with col_tensao:
    st.markdown(criar_visor_agrupado_interno("Tensão", "V", "#2c3e50"), unsafe_allow_html=True)

with col_corrente:
    st.markdown(criar_visor_agrupado_interno("Corrente", "A", "#2c3e50"), unsafe_allow_html=True)
    
with col_potencia:
    st.markdown(criar_visor_agrupado_interno("Potência Ativa", "W", "#2c3e50"), unsafe_allow_html=True)
    
with col_frequencia:
    st.markdown(criar_visor_agrupado_interno("Frequência", "Hz", "#2c3e50"), unsafe_allow_html=True)


# --- GRÁFICOS DINÂMICOS ---
grafico_selecionado = st.radio("📈 Selecione o gráfico a ser exibido:", ("Tensão", "Corrente", "Potência Ativa"))

fig = go.Figure()
cores = {"A": "#2980b9", "B": "#e67e22", "C": "#27ae60"}

for fase in ["A", "B", "C"]:
    dados = st.session_state[f"valores_{fase}"]
    if grafico_selecionado == "Tensão":
        fig.add_trace(go.Scatter(
            y=dados["tensao"],
            mode='lines+markers',
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))
        fig.update_layout(title="Tensão nas Fases", yaxis_title="Tensão (V)")
    elif grafico_selecionado == "Corrente":
        fig.add_trace(go.Scatter(
            y=dados["corrente"],
            mode='lines+markers',
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))
        fig.update_layout(title="Corrente nas Fases", yaxis_title="Corrente (A)")
    elif grafico_selecionado == "Potência Ativa":
        fig.add_trace(go.Scatter(
            y=dados["potencia"],
            mode='lines+markers',
            name=f"Fase {fase}",
            line=dict(color=cores[fase])
        ))
        fig.update_layout(title="Potência Ativa nas Fases", yaxis_title="Potência Ativa (W)")

fig.update_layout(
    xaxis_title="Amostras",
    height=450,
    template="simple_white"
)
st.plotly_chart(fig, use_container_width=True)
