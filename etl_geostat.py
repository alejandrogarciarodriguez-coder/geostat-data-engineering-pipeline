import pandas as pd
import os
import requests
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import datetime
import unicodedata

def extraer_datos_api():
    print("1. Conectando a la API demográfica...")
    url = "https://restcountries.com/v3.1/region/europe"
    try:
        respuesta = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if respuesta.status_code != 200:
            raise ValueError("Error de red")
        datos = respuesta.json()
        if isinstance(datos, str) or 'message' in datos:
            raise TypeError("Proxy bloqueando la API")
            
        lista_paises = []
        for pais in datos:
            nombre = pais.get("name", {}).get("common", "").lower().strip()
            nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('utf-8')
            poblacion = pais.get("population", 0)
            lista_paises.append({"pais": nombre, "poblacion": poblacion})
        return pd.DataFrame(lista_paises)
    except Exception as error:
        print(f"   -> Fallo en API. Activando RESPALDO INTERNO COMPLETO...")
        datos_respaldo = [
            {"pais": "albania", "poblacion": 2837743}, {"pais": "andorra", "poblacion": 77265}, 
            {"pais": "austria", "poblacion": 8917205}, {"pais": "belarus", "poblacion": 9398861}, 
            {"pais": "belgium", "poblacion": 11555997}, {"pais": "bosnia and herzegovina", "poblacion": 3280815}, 
            {"pais": "bulgaria", "poblacion": 6927328}, {"pais": "croatia", "poblacion": 4047200}, 
            {"pais": "cyprus", "poblacion": 1207361}, {"pais": "czechia", "poblacion": 10693939}, 
            {"pais": "denmark", "poblacion": 5831404}, {"pais": "estonia", "poblacion": 1331057}, 
            {"pais": "finland", "poblacion": 5530719}, {"pais": "france", "poblacion": 67391582}, 
            {"pais": "germany", "poblacion": 83240525}, {"pais": "greece", "poblacion": 10715549}, 
            {"pais": "hungary", "poblacion": 9749763}, {"pais": "iceland", "poblacion": 366130}, 
            {"pais": "ireland", "poblacion": 4994724}, {"pais": "italy", "poblacion": 59554023}, 
            {"pais": "kosovo", "poblacion": 1775378}, {"pais": "latvia", "poblacion": 1901548}, 
            {"pais": "liechtenstein", "poblacion": 38137}, {"pais": "lithuania", "poblacion": 2794700}, 
            {"pais": "luxembourg", "poblacion": 632275}, {"pais": "malta", "poblacion": 514564}, 
            {"pais": "moldova", "poblacion": 2597100}, {"pais": "monaco", "poblacion": 39244}, 
            {"pais": "montenegro", "poblacion": 621718}, {"pais": "netherlands", "poblacion": 17441139}, 
            {"pais": "north macedonia", "poblacion": 2077132}, {"pais": "norway", "poblacion": 5379475}, 
            {"pais": "poland", "poblacion": 37950802}, {"pais": "portugal", "poblacion": 10305564}, 
            {"pais": "romania", "poblacion": 19286123}, {"pais": "russia", "poblacion": 144104080}, 
            {"pais": "san marino", "poblacion": 33938}, {"pais": "serbia", "poblacion": 6908224}, 
            {"pais": "slovakia", "poblacion": 5459642}, {"pais": "slovenia", "poblacion": 2100126}, 
            {"pais": "spain", "poblacion": 47351567}, {"pais": "sweden", "poblacion": 10353442}, 
            {"pais": "switzerland", "poblacion": 8636896}, {"pais": "ukraine", "poblacion": 44134693},
            {"pais": "united kingdom", "poblacion": 67215293}, {"pais": "vatican city", "poblacion": 800}
        ]
        return pd.DataFrame(datos_respaldo)

def extraer_datos_sqlite(ruta_archivo):
    print("2. Leyendo SQLite en lotes...")
    conexion = sqlite3.connect(ruta_archivo)
    df = pd.concat([lote for lote in pd.read_sql_query("SELECT * FROM economia_paises", conexion, chunksize=1000)], ignore_index=True)
    conexion.close()
    return df

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
def cargar_postgresql(df_final, df_cuarentena, total_leidos):
    print("5. Cargando en PostgreSQL con Upsert y purgado de cuarentena...")
    inicio = datetime.datetime.now()
    
    # Variables de entorno para hacer el código universal 
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5434")
    
    conexion = psycopg2.connect(
        host=db_host, 
        port=db_port, 
        user="etl_user", 
        password="etl_password", 
        database="geostat_db"
    )
    cursor = conexion.cursor()
    
    # Vaciamos la tabla de cuarentena
    cursor.execute("TRUNCATE TABLE tb_cuarentena_geodatos RESTART IDENTITY;")
    
    if not df_cuarentena.empty:
        # Limpiamos los espacios y ponemos la primera en mayúscula solo para agrupar
        df_cuarentena['dato_original'] = df_cuarentena['pais_nombre_local'].str.strip().str.title()
        
        # Eliminamos las filas que tengan el mismo país y el mismo motivo de rechazo
        df_cuarentena = df_cuarentena.drop_duplicates(subset=['dato_original', 'motivo_rechazo'])
        
        # Insertamos los datos ya deduplicados
        cuarentena_tuplas = [tuple(x) for x in df_cuarentena[['dato_original', 'motivo_rechazo']].to_numpy()]
        execute_values(cursor, "INSERT INTO tb_cuarentena_geodatos (dato_original, motivo_rechazo) VALUES %s", cuarentena_tuplas)
        
    if not df_final.empty:
        final_tuplas = [tuple(x) for x in df_final.to_numpy()]
        query_upsert = """
            INSERT INTO tb_indicadores_europa (pais, poblacion, area_km2, pib_euros, densidad, pib_per_capita)
            VALUES %s
            ON CONFLICT (pais) DO UPDATE SET
                poblacion = EXCLUDED.poblacion, area_km2 = EXCLUDED.area_km2, pib_euros = EXCLUDED.pib_euros,
                densidad = EXCLUDED.densidad, pib_per_capita = EXCLUDED.pib_per_capita;
        """
        execute_values(cursor, query_upsert, final_tuplas)
        
    fin = datetime.datetime.now()
    cursor.execute(
        "INSERT INTO tb_ejecuciones_etl (inicio, fin, registros_leidos, registros_insertados, errores) VALUES (%s, %s, %s, %s, %s)",
        (inicio, fin, total_leidos, len(df_final), len(df_cuarentena))
    )
    
    conexion.commit()
    cursor.close()
    conexion.close()
    print(f"   -> ¡Carga finalizada con éxito! {len(df_final)} países insertados y cuarentena limpia.")


if __name__ == "__main__":
    df_demo = extraer_datos_api()
    
    # Variable de entorno para la ruta SQLite
    # Mi ruta larga original de Windows
    ruta_windows = r"C:\Users\em2026008781\Documents\PROYECTOS NTER\Entregables_Proyecto_Geostat_Alejandro_Garcia_Rodriguez\Datos_ejercicio\datos_economicos_locales.db"
    
    # Busca la variable de Docker. Si no existe, usa la ruta de Windows.
    ruta_db = os.getenv("SQLITE_PATH", ruta_windows)
    
    # Le pasamos ruta_db, que es la que decide si usar Windows o Docker
    df_eco = extraer_datos_sqlite(ruta_db)
    
    df_cons, df_cuar = limpiar_y_detectar_anomalias(df_eco, df_demo)
    df_final = calcular_indicadores(df_cons, df_demo)
    cargar_postgresql(df_final, df_cuar, len(df_eco))
    print("PROCESO ETL COMPLETADO ")
   