from fastapi import FastAPI, HTTPException
import psycopg2
import psycopg2.extras

# Inicializamos la aplicación FastAPI
app = FastAPI(
    title="API REST GeoStat Europa",
    description="Servicio de exposición de métricas macroeconómicas consolidadas.",
    version="1.0.0"
)

# Función de ayuda para conectar a la BD
def obtener_conexion():
    try:
        conexion = psycopg2.connect(
            host="localhost", port="5434", 
            user="etl_user", password="etl_password", database="geostat_db"
        )
        return conexion
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a la BD: {e}")

@app.get("/", tags=["Inicio"])
def raiz():
    return {"mensaje": "Bienvenido a la API de GeoStat. Visita /docs para ver la documentación interactiva."}

@app.get("/api/v1/indicadores", tags=["Indicadores"])
def obtener_todos_los_indicadores():
    """Devuelve la lista completa de los 44 países con todas sus métricas."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM tb_indicadores_europa ORDER BY pib_per_capita DESC")
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return datos

@app.get("/api/v1/indicadores/{nombre_pais}", tags=["Indicadores"])
def obtener_indicador_por_pais(nombre_pais: str):
    """Devuelve las métricas de un país específico (ej: spain, france)."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # Buscamos ignorando mayúsculas/minúsculas
    cursor.execute("SELECT * FROM tb_indicadores_europa WHERE LOWER(pais) = LOWER(%s)", (nombre_pais,))
    dato = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    if not dato:
        raise HTTPException(status_code=404, detail="País no encontrado en la base de datos europea")
    return dato