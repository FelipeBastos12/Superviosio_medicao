else:
    st.title("Visualização de Dados - Dia Anterior")
    for fase in ["A", "B", "C"]:
        df = dfs[fase]

        if "Data" not in df.columns or "Horário" not in df.columns:
            st.warning(f"Planilha da Fase {fase} não contém colunas 'Data' e 'Horário'.")
            continue

        data_max = df["Data"].max()
        df_dia = df[df["Data"] == data_max]

        if df_dia.empty:
            st.warning(f"Sem dados do dia anterior para fase {fase}.")
            continue

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_dia["Horário"],
            y=df_dia[colunas[fase]["tensao"]],
            name="Tensão",
            line=dict(color="blue")
        ))
        fig.add_trace(go.Scatter(
            x=df_dia["Horário"],
            y=df_dia[colunas[fase]["corrente"]],
            name="Corrente",
            line=dict(color="green")
        ))
        fig.add_trace(go.Scatter(
            x=df_dia["Horário"],
            y=df_dia[colunas[fase]["potencia"]],
            name="Potência Ativa",
            line=dict(color="orange")
        ))

        fig.update_layout(
            title=f"Histórico do Dia Anterior - Fase {fase}",
            xaxis_title="Horário",
            yaxis_title="Valor",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
