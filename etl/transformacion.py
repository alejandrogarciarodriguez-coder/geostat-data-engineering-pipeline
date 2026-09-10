import pandas as pd
import requests
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import datetime
import unicodedata

def limpiar_y_detectar_anomalias(df, df_demo):
    print("3. Limpiando y detectando anomalías locales por país...")
    df['pais_limpio'] = df['pais_nombre_local'].str.lower().str.strip()
    df['pais_limpio'] = df['pais_limpio'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    
    # Traducimos los países problemáticos
    traducciones = {'francia': 'france', 'espana': 'spain'}
    df['pais_limpio'] = df['pais_limpio'].replace(traducciones)
    
    df.loc[df['superficie_unidad'] == 'sq_mi', 'superficie_valor'] *= 2.58999
    
    # DICCIONARIO DE DIVISAS AMPLIADO 
    tasas = {
        'GBP': 1.17, 'CHF': 1.05, 'PLN': 0.23, 'SEK': 0.089, 'NOK': 0.087, 
        'DKK': 0.13, 'USD': 0.92, 'EUR': 1.0, 
        'HUF': 0.0025,  # Florín húngaro
        'CZK': 0.039,   # Corona checa
        'RON': 0.20,    # Leu rumano
        'BGN': 0.51,    # Lev búlgaro
        'RSD': 0.0085,  # Dinar serbio
        'BAM': 0.51,    # Marco bosnio
        'ALL': 0.0096,  # Lek albanés
        'MKD': 0.016,   # Denar macedonio
        'ISK': 0.0067,  # Corona islandesa
        'RUB': 0.010,   # Rublo ruso
        'UAH': 0.024,   # Grivna ucraniana
        'MDL': 0.052,   # Leu moldavo
        'BYN': 0.28     # Rublo bielorruso
    }
    # Si falta alguna moneda rara, le damos un peso ínfimo (0.001) para no inflar el PIB
    df['tasa'] = df['pib_divisa'].map(tasas).fillna(0.001)
    df['pib_euros'] = df['pib_valor'] * df['tasa']
    
    # Cuarentena 1: PIB <= 0
    c1 = df[df['pib_euros'] <= 0].copy()
    c1['motivo_rechazo'] = 'PIB <= 0'
    df_val = df[df['pib_euros'] > 0].copy()
    
    # Cuarentena 2: Anomalías IQR
    df_val['Q1'] = df_val.groupby('pais_limpio')['superficie_valor'].transform(lambda x: x.quantile(0.25))
    df_val['Q3'] = df_val.groupby('pais_limpio')['superficie_valor'].transform(lambda x: x.quantile(0.75))
    df_val['IQR'] = df_val['Q3'] - df_val['Q1']
    df_val['lim_inf'] = df_val['Q1'] - 1.5 * df_val['IQR']
    df_val['lim_sup'] = df_val['Q3'] + 1.5 * df_val['IQR']
    
    c2 = df_val[(df_val['superficie_valor'] < df_val['lim_inf']) | (df_val['superficie_valor'] > df_val['lim_sup'])].copy()
    c2['motivo_rechazo'] = 'Anomalía IQR (Outlier)'
    
    df_val = df_val[(df_val['superficie_valor'] >= df_val['lim_inf']) & (df_val['superficie_valor'] <= df_val['lim_sup'])]
    
    # Cuarentena 3: Entidades no europeas
    paises_europeos = df_demo['pais'].tolist()
    c3 = df_val[~df_val['pais_limpio'].isin(paises_europeos)].copy()
    c3['motivo_rechazo'] = 'Entidad no perteneciente a Europa'
    df_val = df_val[df_val['pais_limpio'].isin(paises_europeos)]
    
    df_cons = df_val.groupby('pais_limpio').agg({'superficie_valor': 'median', 'pib_euros': 'median'}).reset_index()
    
    c1 = c1[['pais_nombre_local', 'motivo_rechazo']]
    c2 = c2[['pais_nombre_local', 'motivo_rechazo']]
    c3 = c3[['pais_nombre_local', 'motivo_rechazo']]
    df_cuarentena = pd.concat([c1, c2, c3])
    
    return df_cons, df_cuarentena

def calcular_indicadores(df_eco, df_demo):
    print("4. Consolidando indicadores y cruzando tablas...")
    df_final = pd.merge(df_eco, df_demo, left_on='pais_limpio', right_on='pais', how='inner')
    
    # Hacemos los cálculos iniciales
    df_final['densidad'] = df_final['poblacion'] / df_final['superficie_valor']
    df_final['pib_per_capita'] = df_final['pib_euros'] / df_final['poblacion']
    
    # Filtramos las columnas que van a la base de datos
    df_final = df_final[['pais_limpio', 'poblacion', 'superficie_valor', 'pib_euros', 'densidad', 'pib_per_capita']]
    
    # Forzamos el redondeo matemático estricto a 2 decimales 
    # en cada una de las columnas numéricas para que PostgreSQL no invente decimales extra.
    columnas_numericas = ['superficie_valor', 'pib_euros', 'densidad', 'pib_per_capita']
    for col in columnas_numericas:
        df_final[col] = df_final[col].astype(float).apply(lambda x: round(x, 2))
        
    return df_final