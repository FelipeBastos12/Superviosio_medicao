import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(page_title="Analisador Elétrico", layout="wide")

# Título
st.markdown("<h1 style='text-align: center;'>Analisador Elétrico - Fase A</h1>", unsafe_allow_html=True)

# Carregar CSV com separador decimal vírgula
@st.cache_data
def load_data():
    # Carregar o CSV
    df = pd.read_csv("Planilha_242_LAT - FASEA.csv", sep=",", decimal=",")
    
    # Corrigir nomes de colunas removendo espaços extras
    df.columns = df.columns.str.strip()

    # Criar a coluna DataHora unindo 'Data' e 'Horário'
    df['DataHora'] = pd.to_datetime(df['Data'] + " " + df['Horário'], dayfirst=True)
    
    # Garantir que os dados estejam ordenados pela data e hora
    df.sort_values('DataHora', inplace=True)

    # Converter a coluna de Tensão de string para float (com substituição da vírgula por ponto)
    df['Tensao_Fase_A'] = df['Tensao_Fase_A'].astype(str).str.replace(",", ".").astype(float)

    return df

# Carregar os dados
df = load_data()

# Obter o último valor disponível para exibição
latest = df.iloc[-1]

# Colunas para exibir os dados
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Tensão (V)", f"{latest['Tensao_Fase_A']} V")
    st.metric("Tensão de Linha AB", f"{latest['Tensao_De_Linha_AB']} V")
    st.metric("Frequência", f"{latest['Frequencia_Fase_A']} Hz")

with col2:
    st.metric("Corrente (A)", f"{latest['Corrente_Fase_A']} A")
    st.metric("Fator de Potência", f"{latest['fator_De_Potencia_Fase_A']}")

with col3:
    st.metric("Potência Ativa", f"{latest['Potencia_Ativa_Fase_A']} W")
    st.metric("Potência Reativa", f"{latest['Potencia_Reativa_Fase_A']} VAr")

with col4:
    st.metric("Potência Aparente", f"{latest['Potencia_Aparente_Fase_A']} VA")
    st.metric("Energia Ativa (kWh)", f"{latest['C (kWh)']} kWh")

# Gráfico de Tensão ao longo do tempo
st.markdown("### Gráfico de Tensão (Fase A)")
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(df['DataHora'], df['Tensao_Fase_A'], label='Tensão Fase A (V)', color='orange')
ax.set_xlabel("Tempo")
ax.set_ylabel("Tensão (V)")
ax.grid(True)
ax.legend()
st.pyplot(fig)

# Exibir a tabela com as últimas 10 linhas dos dados
with st.expander("📊 Ver dados brutos"):
    st.dataframe(df.tail(10))
