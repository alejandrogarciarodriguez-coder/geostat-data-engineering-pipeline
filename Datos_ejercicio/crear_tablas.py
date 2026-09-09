import psycopg2

# Nos conectamos a la base de datos usando el puerto 5434 que configuramos
conexion = psycopg2.connect(
    host="localhost",
    port="5434",
    user="etl_user",
    password="etl_password",
    database="geostat_db"
)
cursor = conexion.cursor()

# 1. Tabla de indicadores (Destino). El país es clave única.
cursor.execute("""
CREATE TABLE IF NOT EXISTS tb_indicadores_europa (
    pais VARCHAR(150) UNIQUE,
    poblacion BIGINT,
    area_km2 NUMERIC,
    pib_euros NUMERIC,
    densidad NUMERIC,
    pib_per_capita NUMERIC
);
""")

# 2. Tabla de Cuarentena (Errores). Guarda el dato y el motivo.
cursor.execute("""
CREATE TABLE IF NOT EXISTS tb_cuarentena_geodatos (
    id SERIAL PRIMARY KEY,
    dato_original TEXT,
    motivo_rechazo TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# 3. Tabla de Auditoría (Ejecuciones). Guarda el conteo y los tiempos.
cursor.execute("""
CREATE TABLE IF NOT EXISTS tb_ejecuciones_etl (
    id SERIAL PRIMARY KEY,
    inicio TIMESTAMP,
    fin TIMESTAMP,
    registros_leidos INT,
    registros_insertados INT,
    errores INT
);
""")

# Guardamos los cambios y cerramos la conexión
conexion.commit()
cursor.close()
conexion.close()
print("¡Las tablas se han creado correctamente en PostgreSQL!")