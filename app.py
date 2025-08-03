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
# A nova estrutura de colunas deve ser por grandeza
col_tensao, col_corrente, col_potencia, col_frequencia = st.columns(4)

def cor_tensao(valor):
    return "#2ecc71" if valor >= 210 else "#c0392b"
    
def criar_visor_agrupado(titulo, unidade, cor_fundo, cor_texto, dados_por_fase, cor_fase_A="#2ecc71", cor_fase_B="#2ecc71", cor_fase_C="#2ecc71"):
    """Função para criar um único visor grande com os dados das 3 fases"""
    conteudo_visor = ""
    conteudo_visor += f"<h4 style='text-align: center;'>{titulo}</h4>"
    for fase in ["A", "B", "C"]:
        valor = dados_por_fase[fase][-1] if dados_por_fase[fase] else None
        if valor is not None:
            # Aplica a cor condicional para a tensão
            cor_atual = cor_tensao(valor) if titulo == "Tensão" else cor_texto
            conteudo_visor += f"""
                <div style='
                    color: {cor_atual};
                    padding: 5px;
                    text-align: left;
                    font-size: 20px;
                    font-weight: bold;
                '>
                    Fase {fase}: {valor:.2f} {unidade}
                </div>
            """

    # Retorna o visor completo dentro de um container
    return f"""
    <div style='
        background-color: {cor_fundo};
        color: {cor_texto};
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    '>
        {conteudo_visor}
    </div>
    """

with col_tensao:
    # Coleta os últimos valores de tensão de cada fase
    dados_tensao = {fase: st.session_state[f"valores_{fase}"]["tensao"] for fase in ["A", "B", "C"]}
    # Cria o visor agrupado de tensão
    st.markdown(criar_visor_agrupado("Tensão", "V", "#2c3e50", "#ffffff", dados_tensao), unsafe_allow_html=True)
with col_corrente:
    # Coleta os últimos valores de corrente de cada fase
    dados_corrente = {fase: st.session_state[f"valores_{fase}"]["corrente"] for fase in ["A", "B", "C"]}
    # Cria o visor agrupado de corrente
    st.markdown(criar_visor_agrupado("Corrente", "A", "#2c3e50", "#ffffff", dados_corrente), unsafe_allow_html=True)
with col_potencia:
    # Coleta os últimos valores de potência de cada fase
    dados_potencia = {fase: st.session_state[f"valores_{fase}"]["potencia"] for fase in ["A", "B", "C"]}
    # Cria o visor agrupado de potência
    st.markdown(criar_visor_agrupado("Potência Ativa", "W", "#2c3e50", "#ffffff", dados_potencia), unsafe_allow_html=True)
with col_frequencia:
    # Coleta os últimos valores de frequência
    # Lembre-se que seu código original só extrai frequência para a Fase A
    valor_frequencia_A = dfs["A"].iloc[st.session_state["index_A"]-1].get(colunas["A"]["frequencia"], None)
    valor_frequencia_A = float(valor_frequencia_A) if valor_frequencia_A is not None else None
    
    # Cria o visor agrupado de frequência
    st.markdown(f"""
    <div style='
        background-color: #2c3e50;
        color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    '>
        <h4 style='text-align: center;'>Frequência</h4>
        <div style='
            color: #2ecc71;
            padding: 5px;
            text-align: left;
            font-size: 20px;
            font-weight: bold;
        '>
            Fase A: {valor_frequencia_A:.2f} Hz
        </div>
        <div style='
            color: #2ecc71;
            padding: 5px;
            text-align: left;
            font-size: 20px;
            font-weight: bold;
        '>
            Fase B: {valor_frequencia_A:.2f} Hz
        </div>
        <div style='
            color: #2ecc71;
            padding: 5px;
            text-align: left;
            font-size: 20px;
            font-weight: bold;
        '>
            Fase C: {valor_frequencia_A:.2f} Hz
        </div>
    </div>
    """, unsafe_allow_html=True)

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
