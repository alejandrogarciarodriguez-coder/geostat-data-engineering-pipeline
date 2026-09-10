import psycopg2
from psycopg2.extras import execute_values
import datetime

def cargar_postgresql(df_final, df_cuarentena, total_leidos):
    print("5. Cargando en PostgreSQL con Upsert e histórico de cuarentena...")
    
    inicio = datetime.datetime.now()
    
    conexion = psycopg2.connect(host="localhost", port="5434", user="etl_user", password="etl_password", database="geostat_db")
    cursor = conexion.cursor()
    
    # --- LA MAGIA ESTÁ AQUÍ ---
    # Buscamos el último ID de la tabla y le sumamos 1. Si la tabla está vacía, devuelve 1.
    cursor.execute("SELECT COALESCE(MAX(id_ejecucion), 0) + 1 FROM tb_ejecuciones_etl")
    id_lote = cursor.fetchone()[0]
    
    if not df_cuarentena.empty:
        df_cuarentena['dato_original'] = df_cuarentena['pais_nombre_local'].str.strip().str.title()
        df_cuarentena = df_cuarentena.drop_duplicates(subset=['dato_original', 'motivo_rechazo'])
        
        # Usamos el id_lote (que ahora es 1, 2, 3...)
        cuarentena_tuplas = [
            (row['dato_original'], row['motivo_rechazo'], id_lote) 
            for _, row in df_cuarentena.iterrows()
        ]
        
        query_cuarentena = """
            INSERT INTO tb_cuarentena_geodatos (dato_original, motivo_rechazo, id_ejecucion) 
            VALUES %s
        """
        execute_values(cursor, query_cuarentena, cuarentena_tuplas)
        
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
    
    # Guardamos el resumen con el mismo id_lote numérico
    cursor.execute(
        "INSERT INTO tb_ejecuciones_etl (id_ejecucion, inicio, fin, registros_leidos, registros_insertados, errores) VALUES (%s, %s, %s, %s, %s, %s)",
        (id_lote, inicio, fin, total_leidos, len(df_final), len(df_cuarentena))
    )
    
    conexion.commit()
    cursor.close()
    conexion.close()