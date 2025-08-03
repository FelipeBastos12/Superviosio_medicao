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
    if f"corrente_anterior_{fase}" not in st.session_state:
        st.session_state[f"corrente_anterior_{fase}"] = 0.0
    if "frequencia_ultima" not in st.session_state:
        st.session_state["frequencia_ultima"] = 0.0

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
        st.session_state[f"valores_{fase}"]["tensao"] = st.session_state[f"valores_{fase}"]["tensao"][-50:]
    if corrente is not None:
        st.session_state[f"valores_{fase}"]["corrente"].append(float(corrente))
        st.session_state[f"valores_{fase}"]["corrente"] = st.session_state[f"valores_{fase}"]["corrente"][-50:]
    if potencia is not None:
        st.session_state[f"valores_{fase}"]["potencia"].append(float(potencia))
        st.session_state[f"valores_{fase}"]["potencia"] = st.session_state[f"valores_{fase}"]["potencia"][-50:]
    if frequencia is not None:
        st.session_state["frequencia_ultima"] = float(frequencia)

# --- FUNÇÃO PARA RENDERIZAR O PAINEL ---
def cor_tensao(valor):
    return "#2ecc71" if valor >= 210 else "#c0392b"
    
def renderizar_painel_principal(titulo, unidade, cor_fundo):
    conteudo_corpo = []
    
    # Adiciona a fase A, que tem uma estrutura ligeiramente diferente
    valor_a = None
    if titulo == "Tensão":
        valor_a = st.session_state["valores_A"]["tensao"][-1] if st.session_state["valores_A"]["tensao"] else None
    elif titulo == "Corrente":
        valor_a = st.session_state["valores_A"]["corrente"][-1] if st.session_state["valores_A"]["corrente"] else None
    elif titulo == "Potência Ativa":
        valor_a = st.session_state["valores_A"]["potencia"][-1] if st.session_state["valores_A"]["potencia"] else None
    elif titulo == "Frequência":
        valor_a = st.session_state.get('frequencia_ultima', None)
    
    if valor_a is not None:
        cor_texto_a = cor_tensao(valor_a) if titulo == "Tensão" else "#ffffff"
        
        conteudo_corpo.append(f"""
            <div style='
                background-color: {cor_fundo};
                color: {cor_texto_a};
                padding: 10px;
                border-radius: 10px;
                text-align: left;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            '>
                Fase A: {valor_a:.2f} {unidade}
            </div>
        """)

    # Adiciona a estrutura das fases B e C em um único bloco HTML
    html_interno_b_c = []
    for fase in ["B", "C"]:
        valor_num = None
        if titulo == "Tensão":
            valor_num = st.session_state[f"valores_{fase}"]["tensao"][-1] if st.session_state[f"valores_{fase}"]["tensao"] else None
        elif titulo == "Corrente":
            valor_num = st.session_state[f"valores_{fase}"]["corrente"][-1] if st.session_state[f"valores_{fase}"]["corrente"] else None
        elif titulo == "Potência Ativa":
            valor_num = st.session_state[f"valores_{fase}"]["potencia"][-1] if st.session_state[f"valores_{fase}"]["potencia"] else None
        elif titulo == "Frequência":
            valor_num = st.session_state.get('frequencia_ultima', None)
        
        if valor_num is not None:
            cor_texto_fase = cor_tensao(valor_num) if titulo == "Tensão" else "#ffffff"
            
            html_interno_b_c.append(f"""
                <div style='
                    color: {cor_texto_fase};
                    padding: 5px;
                    text-align: left;
                    font-size: 20px;
                    font-weight: bold;
                '>
                    Fase {fase}: {valor_num:.2f} {unidade}
                </div>
            """)
    
    html_completo_b_c = "".join(html_interno_b_c)
    
    # Renderiza o container principal com o título e os blocos de fases A, B e C
    st.markdown(f"### {titulo}")
    st.markdown("".join(conteudo_corpo), unsafe_allow_html=True)
    st.markdown(f"""
        <div style='
            background-color: {cor_fundo};
            color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 10px;
        '>
            {html_completo_b_c}
        </div>
    """, unsafe_allow_html=True)

col_tensao, col_corrente, col_potencia, col_frequencia = st.columns(4)

with col_tensao:
    renderizar_painel_principal("Tensão", "V", "#2c3e50")

with col_corrente:
    renderizar_painel_principal("Corrente", "A", "#2c3e50")
    
with col_potencia:
    renderizar_painel_principal("Potência Ativa", "W", "#2c3e50")
    
with col_frequencia:
    renderizar_painel_principal("Frequência", "Hz", "#2c3e50")

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
