import pandas as pd
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