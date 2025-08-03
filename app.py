# --- SELETOR DE DIA ---
dia_escolhido = st.radio("Selecionar dia para visualização:", ("Dia Atual", "Dia Anterior"))

# --- CONTROLANDO AUTORELOAD ---
if dia_escolhido == "Dia Atual":
    st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh")
else:
    # No "Dia Anterior" não atualiza automaticamente
    pass

# --- FUNÇÃO PARA PEGAR OS DADOS SEGUNDO O DIA SELECIONADO ---
def get_dados(fase, dia):
    df = dfs[fase]
    if dia == "Dia Atual":
        idx = st.session_state[f"index_{fase}"]
        if idx >= len(df):
            st.session_state[f"index_{fase}"] = 0
            idx = 0
            st.success(f"Reiniciando dados da fase {fase}")
        row = df.iloc[idx]
        st.session_state[f"index_{fase}"] += 1

        # Extrai dados linha a linha
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

        return {
            "tensao": st.session_state[f"valores_{fase}"]["tensao"],
            "corrente": st.session_state[f"valores_{fase}"]["corrente"],
            "potencia": st.session_state[f"valores_{fase}"]["potencia"]
        }
    else:  # Dia Anterior - retorna todos os dados da planilha
        tensao = df[colunas[fase]["tensao"]].astype(float).tolist()
        corrente = df[colunas[fase]["corrente"]].astype(float).tolist()
        potencia = df[colunas[fase]["potencia"]].astype(float).tolist()

        # Atualiza session_state para evitar erros futuros no código que usa esses dados
        st.session_state[f"valores_{fase}"]["tensao"] = tensao
        st.session_state[f"valores_{fase}"]["corrente"] = corrente
        st.session_state[f"valores_{fase}"]["potencia"] = potencia

        return {
            "tensao": tensao,
            "corrente": corrente,
            "potencia": potencia
        }


# --- PEGANDO OS DADOS SEGUNDO DIA SELECIONADO ---
for fase in ["A", "B", "C"]:
    _ = get_dados(fase, dia_escolhido)


# --- PEGANDO ÚLTIMOS VALORES PARA VISOR AGRUPADO ---
valores_tensao = {}
valores_corrente = {}
valores_potencia = {}
valores_frequencia = {}

for fase in ["A", "B", "C"]:
    df = dfs[fase]

    if dia_escolhido == "Dia Atual":
        idx = st.session_state[f"index_{fase}"] - 1
        if idx < 0:
            idx = 0
        row = df.iloc[idx]

        tensao = row.get(colunas[fase]["tensao"], 0)
        corrente = row.get(colunas[fase]["corrente"], 0)
        potencia = row.get(colunas[fase]["potencia"], 0)
        frequencia = row.get(colunas[fase]["frequencia"], 0)

        if corrente == 0:
            corrente = st.session_state.get(f"corrente_anterior_{fase}", corrente)
        else:
            st.session_state[f"corrente_anterior_{fase}"] = corrente

        valores_tensao[fase] = float(tensao)
        valores_corrente[fase] = float(corrente)
        valores_potencia[fase] = float(potencia)
        valores_frequencia[fase] = float(frequencia)

    else:  # Dia Anterior pega o último valor de cada coluna da planilha para exibir no visor
        valores_tensao[fase] = float(df[colunas[fase]["tensao"]].iloc[-1])
        valores_corrente[fase] = float(df[colunas[fase]["corrente"]].iloc[-1])
        valores_potencia[fase] = float(df[colunas[fase]["potencia"]].iloc[-1])
        valores_frequencia[fase] = float(df[colunas[fase]["frequencia"]].iloc[-1])


# --- GRÁFICOS DINÂMICOS (usar dados atualizados conforme dia escolhido) ---
grafico_selecionado = st.radio("", ("Tensão", "Corrente", "Potência Ativa"))

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
