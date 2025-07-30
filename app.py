@st.cache_data
def load_data():
    df = pd.read_csv("Planilha_242_LAT - FASEA.csv", sep=",", decimal=",")
    
    # Exibe os nomes das colunas para verificar
    st.write("Nomes das colunas:", df.columns)

    # Corrige os nomes das colunas removendo espaços extras e caracteres estranhos
    df.columns = df.columns.str.strip()

    # Exibe os nomes das colunas após a correção
    st.write("Nomes das colunas corrigidos:", df.columns)

    # Criar a coluna DataHora unindo 'Data' e 'Horário'
    df['DataHora'] = pd.to_datetime(df['Data'] + " " + df['Horário'], dayfirst=True)
    
    # Garantir que os dados estejam ordenados pela data e hora
    df.sort_values('DataHora', inplace=True)

    # Converter a coluna de Tensão de string para float (com substituição da vírgula por ponto)
    df['Tensao_Fase_A'] = df['Tensao_Fase_A'].astype(str).str.replace(",", ".").astype(float)

    return df
