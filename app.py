import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_monthly_fake_data(fase_letter, num_days=30):
    """
    Gera um DataFrame com dados fictícios para um mês inteiro, seguindo uma
    lógica de consumo total diário e com redução para fins de semana.

    Args:
        fase_letter (str): A letra da fase (e.g., 'A', 'B', 'C').
        num_days (int): O número de dias para gerar os dados.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados fictícios.
    """
    # AQUI ESTÁ A MUDANÇA
    start_date = datetime(2025, 8, 1)
    
    time_series = pd.date_range(start_date, start_date + timedelta(days=num_days) - timedelta(minutes=3), freq='3min')
    
    line_voltage_col_name = {
        'A': 'Tensao_De_Linha_AB',
        'B': 'Tensao_De_Linha_BC',
        'C': 'Tensao_De_Linha_CA'
    }[fase_letter]

    data = {
        'Data': [ts.strftime('%d/%m/%Y') for ts in time_series],
        'Horário': [ts.strftime('%H:%M:%S') for ts in time_series],
        f'Tensao_Fase_{fase_letter}': [],
        line_voltage_col_name: [],
        f'Corrente_Fase_{fase_letter}': [],
        f'Potencia_Ativa_Fase_{fase_letter}': [],
        f'fator_De_Potencia_Fase_{fase_letter}': [],
        f'Potencia_Reativa_Fase_{fase_letter}': [],
        f'Potencia_Aparente_Fase_{fase_letter}': [],
        f'Frequencia_Fase_{fase_letter}': [],
        'Intervalos em Hora': [],
        'C (Wh)': [],
        'C (kWh)': []
    }
    
    cumulative_wh = 0.0
    
    for i, ts in enumerate(time_series):
        hour = ts.hour
        day_of_week = ts.dayofweek # 0=Segunda, 5=Sábado, 6=Domingo
        
        # Lógica para os dias úteis (Segunda a Sexta)
        if day_of_week < 5: 
            if 0 <= hour < 8:
                power_total_kW_base = np.random.uniform(45, 55)
                power_factor_base = np.random.uniform(0.83, 0.87)
            elif 8 <= hour < 13:
                power_total_kW_base = np.random.uniform(90, 110)
                power_factor_base = np.random.uniform(0.88, 0.92)
            elif 13 <= hour < 18:
                power_total_kW_base = np.random.uniform(135, 165)
                power_factor_base = np.random.uniform(0.90, 0.94)
            elif 18 <= hour < 21:
                power_total_kW_base = np.random.uniform(90, 110)
                power_factor_base = np.random.uniform(0.88, 0.92)
            else: # 21h a 00h
                power_total_kW_base = np.random.uniform(45, 55)
                power_factor_base = np.random.uniform(0.83, 0.87)
        
        # Lógica para os fins de semana (Sábado e Domingo)
        else:
            weekend_reduction_factor = np.random.uniform(0.4, 0.6) # Fator de redução aleatório
            if 0 <= hour < 8:
                power_total_kW_base = np.random.uniform(45, 55) * weekend_reduction_factor
                power_factor_base = np.random.uniform(0.83, 0.87)
            elif 8 <= hour < 18:
                power_total_kW_base = np.random.uniform(90, 110) * weekend_reduction_factor
                power_factor_base = np.random.uniform(0.88, 0.92)
            else: # 18h a 00h
                power_total_kW_base = np.random.uniform(45, 55) * weekend_reduction_factor
                power_factor_base = np.random.uniform(0.83, 0.87)

        # AQUI ESTÁ A MUDANÇA: A potência por fase é calculada com base na potência total
        # A potência ativa total é dividida por 3 (para um sistema balanceado)
        active_power_per_phase = (power_total_kW_base * 1000) / 3
        
        voltage_phase = np.random.normal(222.5, 1.0)
        power_factor = min(1.0, max(0.8, power_factor_base * np.random.uniform(0.98, 1.02)))
        frequency = np.random.normal(60.0, 0.1)

        active_power = active_power_per_phase * np.random.uniform(0.95, 1.05)
        apparent_power = active_power / power_factor
        reactive_power = apparent_power * np.sin(np.arccos(power_factor))
        current = apparent_power / voltage_phase
        
        data[f'Tensao_Fase_{fase_letter}'].append(voltage_phase)
        data[line_voltage_col_name].append(voltage_phase * np.sqrt(3))
        data[f'Corrente_Fase_{fase_letter}'].append(current)
        data[f'Potencia_Ativa_Fase_{fase_letter}'].append(active_power)
        data[f'fator_De_Potencia_Fase_{fase_letter}'].append(power_factor)
        data[f'Potencia_Reativa_Fase_{fase_letter}'].append(reactive_power)
        data[f'Potencia_Aparente_Fase_{fase_letter}'].append(apparent_power)
        data[f'Frequencia_Fase_{fase_letter}'].append(frequency)

        interval_in_hours = 3 / 60.0
        data['Intervalos em Hora'].append(interval_in_hours)

        energy_wh = active_power * interval_in_hours
        cumulative_wh += energy_wh
        data['C (Wh)'].append(cumulative_wh)
        data['C (kWh)'].append(cumulative_wh / 1000.0)

    return pd.DataFrame(data)

# Gerar e salvar dados para cada fase para um mês (30 dias)
num_days_to_generate = 30
for fase in ['A', 'B', 'C']:
    df = generate_monthly_fake_data(fase, num_days_to_generate)
    
    for col in df.columns:
        if df[col].dtype == np.float64:
            df[col] = df[col].apply(lambda x: f"{x:.2f}".replace('.', ','))
            
    file_name = f'Planilha_242_LAT - FASE{fase}.csv'
    df.to_csv(file_name, index=False, encoding='utf-8')
    print(f'Arquivo {file_name} para {num_days_to_generate} dias gerado com sucesso.')
