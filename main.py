import os
import logging
from etl.extraccion import extraer_datos_api, extraer_datos_sqlite
from etl.transformacion import limpiar_y_detectar_anomalias, calcular_indicadores
from etl.carga import cargar_postgresql

# CONFIGURACIÓN DEL LOG 
# Comprobamos si la carpeta 'log' existe. Si no, la creamos automáticamente.
if not os.path.exists('log'):
    os.makedirs('log')

# Configuramos cómo y dónde se guarda el registro
logging.basicConfig(
    filename='log/pipeline_ejecucion.log',  # Archivo donde se guardará
    level=logging.INFO,                     # Nivel de los mensajes a capturar
    format='%(asctime)s - %(levelname)s - %(message)s', # Formato: Fecha - Nivel - Mensaje
    encoding='utf-8'
)
# -------------------------------------------------------

def ejecutar_pipeline():
    logging.info("--- INICIANDO PIPELINE DE DATOS GEOSTAT ---")
    print("Iniciando proceso... (revisa la carpeta 'log' para ver el detalle)")
    
    try:
        # 1. Extracción
        logging.info("Fase 1: Iniciando extracción de datos (API y SQLite)...")
        df_demo = extraer_datos_api()
        ruta_db = r"C:\Users\em2026008781\Documents\PROYECTOS NTER\Entregables_Proyecto_Geostat_Alejandro_Garcia_Rodriguez\Datos_ejercicio\datos_economicos_locales.db"
        df_eco = extraer_datos_sqlite(ruta_db)
        logging.info(f"Extracción completada. Países leídos: {len(df_eco)}")
        
        # 2. Transformación
        logging.info("Fase 2: Iniciando transformación, limpieza y cuarentena...")
        df_cons, df_cuar = limpiar_y_detectar_anomalias(df_eco, df_demo)
        df_final = calcular_indicadores(df_cons, df_demo)
        logging.info(f"Transformación completada. Países a cargar: {len(df_final)} | Países en cuarentena: {len(df_cuar)}")
        
        # 3. Carga
        logging.info("Fase 3: Iniciando carga en base de datos PostgreSQL...")
        cargar_postgresql(df_final, df_cuar, len(df_eco))
        
        logging.info("--- PROCESO ETL COMPLETADO CON ÉXITO ---")
        print("¡Pipeline ejecutado con éxito! Revisa el archivo pipeline_ejecucion.log")
        
    except Exception as e:
        # Si algo falla en cualquier punto, el log atrapará el error exacto
        logging.error(f"ERROR CRÍTICO DETENIDO EL PIPELINE: {e}")
        print("El proceso ha fallado. Revisa el log para más detalles.")

if __name__ == "__main__":
    ejecutar_pipeline()