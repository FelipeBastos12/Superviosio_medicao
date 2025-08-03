# --- VISUALIZAÇÃO DOS VISORS AGRUPADOS POR GRANDEZA ---
def visor(valor, label, cor_fundo, cor_texto):
    return f"""
    <div style='
        background-color: {cor_fundo};
        color: {cor_texto};
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin: 5px 10px;
        flex: 1;
    '>
        {label}: {valor}
    </div>
    """

def visor_grupo(titulo, valores_fases, cores_fundo, cores_texto):
    itens_html = ""
    for fase, valor, cor_f, cor_t in valores_fases:
        itens_html += visor(valor, f"Fase {fase}", cor_f, cor_t)
    html = f"""
    <div style='
        border: 2px solid #34495e;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: #2c3e50;
        color: white;
    '>
        <h3 style='text-align:center;'>{titulo}</h3>
        <div style='display: flex; justify-content: space-around;'>
            {itens_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# --- AGRUPANDO OS VISORS ---
# Para cada grandeza, junta as fases e exibe dentro de um quadrado só

# Tensões
valores_tensao = []
for fase in ["A", "B", "C"]:
    idx = st.session_state[f"index_{fase}"] - 1
    if idx < 0:
        idx = 0
    row = dfs[fase].iloc[idx]
    tensao = row.get(colunas[fase]["tensao"], None)
    if tensao is not None:
        tensao = float(tensao)
        cor_texto = "#2ecc71" if tensao >= 210 else "#c0392b"
        valores_tensao.append((fase, f"{tensao:.1f} V", "#34495e", cor_texto))
visor_grupo("Tensão", valores_tensao, None, None)

# Correntes
valores_corrente = []
for fase in ["A", "B", "C"]:
    idx = st.session_state[f"index_{fase}"] - 1
    if idx < 0:
        idx = 0
    row = dfs[fase].iloc[idx]
    corrente = row.get(colunas[fase]["corrente"], None)
    if corrente == 0:
        corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
    else:
        st.session_state[f"corrente_anterior_{fase}"] = corrente
    if corrente is not None:
        valores_corrente.append((fase, f"{float(corrente):.1f} A", "#34495e", "#2ecc71"))
visor_grupo("Corrente", valores_corrente, None, None)

# Potência Ativa
valores_potencia = []
for fase in ["A", "B", "C"]:
    idx = st.session_state[f"index_{fase}"] - 1
    if idx < 0:
        idx = 0
    row = dfs[fase].iloc[idx]
    potencia = row.get(colunas[fase]["potencia"], None)
    if potencia is not None:
        valores_potencia.append((fase, f"{float(potencia):.2f} W", "#34495e", "#2ecc71"))
visor_grupo("Potência Ativa", valores_potencia, None, None)

# Frequência
valores_frequencia = []
for fase in ["A", "B", "C"]:
    idx = st.session_state[f"index_{fase}"] - 1
    if idx < 0:
        idx = 0
    row = dfs[fase].iloc[idx]
    frequencia = row.get(colunas[fase]["frequencia"], None)
    if frequencia is not None:
        valores_frequencia.append((fase, f"{float(frequencia):.2f} Hz", "#34495e", "#2ecc71"))
visor_grupo("Frequência", valores_frequencia, None, None)
