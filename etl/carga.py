import psycopg2
from psycopg2.extras import execute_values
import datetime

def cargar_postgresql(df_final, df_cuarentena, total_leidos):
    print("5. Cargando en PostgreSQL con Upsert y purgado de cuarentena...")
    inicio = datetime.datetime.now()
    
    # Conexión local fija
    conexion = psycopg2.connect(host="localhost", port="5434", user="etl_user", password="etl_password", database="geostat_db")
    cursor = conexion.cursor()
    
    # Vaciamos la tabla de cuarentena
    cursor.execute("TRUNCATE TABLE tb_cuarentena_geodatos RESTART IDENTITY;")
    
    if not df_cuarentena.empty:
        # Limpiamos los espacios y ponemos la primera en mayúscula solo para agrupar
        df_cuarentena['dato_original'] = df_cuarentena['pais_nombre_local'].str.strip().str.title()
        
        # Eliminamos las filas duplicadas
        df_cuarentena = df_cuarentena.drop_duplicates(subset=['dato_original', 'motivo_rechazo'])
        
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