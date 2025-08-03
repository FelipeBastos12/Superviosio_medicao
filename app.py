# --- VISUALIZAÇÃO AGRUPADA DOS VISORS ---
def visor_linha(fase, valor, unidade, cor_texto):
    return f"""
    <div style='
        color: {cor_texto};
        font-size: 24px;
        font-weight: bold;
        margin: 8px 0;
    '>
        Fase {fase}: {valor:.1f} {unidade}
    </div>
    """

def visor_linha_potencia(fase, valor, unidade, cor_texto):
    return f"""
    <div style='
        color: {cor_texto};
        font-size: 24px;
        font-weight: bold;
        margin: 8px 0;
    '>
        Fase {fase}: {valor:.2f} {unidade}
    </div>
    """

def visor_linha_frequencia(fase, valor, unidade, cor_texto):
    return f"""
    <div style='
        color: {cor_texto};
        font-size: 24px;
        font-weight: bold;
        margin: 8px 0;
    '>
        Fase {fase}: {valor:.2f} {unidade}
    </div>
    """

def cor_tensao(valor):
    return "#2ecc71" if valor >= 210 else "#c0392b"

col_tensao, col_corrente, col_potencia, col_frequencia = st.columns(4)

with col_tensao:
    st.subheader("Tensão")
    conteudo = f"""
    <div style='
        background-color: #2c3e50;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    '>
    """
    for fase in ["A", "B", "C"]:
        valor = st.session_state[f"valores_{fase}"]["tensao"][-1] if st.session_state[f"valores_{fase}"]["tensao"] else None
        if valor is not None:
            cor = cor_tensao(valor)
            conteudo += visor_linha(fase, valor, "V", cor)
    conteudo += "</div>"
    st.markdown(conteudo, unsafe_allow_html=True)

with col_corrente:
    st.subheader("Corrente")
    conteudo = f"""
    <div style='
        background-color: #2c3e50;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    '>
    """
    for fase in ["A", "B", "C"]:
        valor = st.session_state[f"valores_{fase}"]["corrente"][-1] if st.session_state[f"valores_{fase}"]["corrente"] else None
        if valor is not None:
            conteudo += visor_linha(fase, valor, "A", "#2ecc71")
    conteudo += "</div>"
    st.markdown(conteudo, unsafe_allow_html=True)

with col_potencia:
    st.subheader("Potência Ativa")
    conteudo = f"""
    <div style='
        background-color: #2c3e50;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    '>
    """
    for fase in ["A", "B", "C"]:
        valor = st.session_state[f"valores_{fase}"]["potencia"][-1] if st.session_state[f"valores_{fase}"]["potencia"] else None
        if valor is not None:
            conteudo += visor_linha_potencia(fase, valor, "W", "#2ecc71")
    conteudo += "</div>"
    st.markdown(conteudo, unsafe_allow_html=True)

with col_frequencia:
    st.subheader("Frequência")
    conteudo = f"""
    <div style='
        background-color: #2c3e50;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    '>
    """
    for fase in ["A", "B", "C"]:
        valor = None
        # Pega a frequência da fase atual (última linha)
        try:
            valor_raw = dfs[fase].iloc[st.session_state[f"index_{fase}"]-1].get(colunas[fase]["frequencia"], None)
            if valor_raw is not None:
                valor = float(valor_raw)
        except:
            pass
        if valor is not None:
            conteudo += visor_linha_frequencia(fase, valor, "Hz", "#2ecc71")
    conteudo += "</div>"
    st.markdown(conteudo, unsafe_allow_html=True)
