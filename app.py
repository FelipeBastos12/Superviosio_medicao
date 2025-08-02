import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Monitoramento Elétrico - Leitura Atual por Grandeza")

# Carrega os arquivos CSV (você pode trocar para seu caminho real)
fase_a = pd.read_csv("Planilha_242_LAT - FASEA.csv")
fase_b = pd.read_csv("Planilha_242_LAT - FASEB.csv")
fase_c = pd.read_csv("Planilha_242_LAT - FASEC.csv")

# Pega a última linha de cada planilha
ultima_a = fase_a.iloc[-1]
ultima_b = fase_b.iloc[-1]
ultima_c = fase_c.iloc[-1]

# Função auxiliar para criar bloco HTML
def bloco_grandeza(nome, valores):
    bloco = f"""
    <div style="border: 2px solid #333; border-radius: 12px; padding: 20px; background-color: #f5f5f5; margin-bottom: 20px">
        <h3 style="color: #222;">🔷 {nome}</h3>
        <ul style="list-style: none; padding-left: 0; font-size: 18px">
            <li>Fase A: <strong>{valores['A']}</strong></li>
            <li>Fase B: <strong>{valores['B']}</strong></li>
            <li>Fase C: <strong>{valores['C']}</strong></li>
        </ul>
    </div>
    """
    return bloco

# Prepara os valores formatados
tensoes = {
    "A": f"{ultima_a[' Tensão (V)']:.1f} V",
    "B": f"{ultima_b[' Tensão (V)']:.1f} V",
    "C": f"{ultima_c[' Tensão (V)']:.1f} V"
}

correntes = {
    "A": f"{ultima_a[' Corrente (A)']:.1f} A",
    "B": f"{ultima_b[' Corrente (A)']:.1f} A",
    "C": f"{ultima_c[' Corrente (A)']:.1f} A"
}

potencias = {
    "A": f"{ultima_a[' Potência Ativa (W)']:.2f} W",
    "B": f"{ultima_b[' Potência Ativa (W)']:.2f} W",
    "C": f"{ultima_c[' Potência Ativa (W)']:.2f} W"
}

frequencias = {
    "A": f"{ultima_a[' Frequência (Hz)']:.2f} Hz",
    "B": f"{ultima_b[' Frequência (Hz)']:.2f} Hz",
    "C": f"{ultima_c[' Frequência (Hz)']:.2f} Hz"
}

# Exibe os blocos agrupados
st.markdown(bloco_grandeza("Tensão", tensoes), unsafe_allow_html=True)
st.markdown(bloco_grandeza("Corrente", correntes), unsafe_allow_html=True)
st.markdown(bloco_grandeza("Potência Ativa", potencias), unsafe_allow_html=True)
st.markdown(bloco_grandeza("Frequência", frequencias), unsafe_allow_html=True)
