import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="GeoStat Analytics", page_icon="🌍", layout="wide")
st.title("🌍 Dashboard Analítico - GeoStat Europa")
st.markdown("Visor interactivo de métricas macroeconómicas y demográficas extraídas mediante el pipeline ETL.")

# 2. Conexión a la base de datos (con caché para que sea rápido)
@st.cache_data
def cargar_datos():
    conexion = psycopg2.connect(
        host="localhost", port="5434", 
        user="etl_user", password="etl_password", database="geostat_db"
    )
    query = "SELECT pais, poblacion, area_km2, pib_euros, densidad, pib_per_capita FROM tb_indicadores_europa"
    df = pd.read_sql_query(query, conexion)
    conexion.close()
    
    # Ponemos la primera letra del país en mayúscula para que quede más bonito en los gráficos
    df['pais'] = df['pais'].str.title()
    return df

# Cargamos los datos
try:
    df_datos = cargar_datos()
    
    # 3. Tarjetas de KPIs (Métricas principales)
    col1, col2, col3 = st.columns(3)
    col1.metric("Países Consolidados", f"{len(df_datos)}")
    col2.metric("Población Total (Europa)", f"{df_datos['poblacion'].sum():,.0f}".replace(',', '.'))
    col3.metric("PIB per Cápita Medio", f"{df_datos['pib_per_capita'].mean():,.2f} €".replace(',', '.'))

    st.divider()

    # 4. Gráficos Interactivos
    col_mapa, col_ranking = st.columns([2, 1])

    with col_mapa:
        st.subheader("🗺️ Mapa de Riqueza (PIB per Cápita)")
        # Creamos un mapa interactivo. Plotly reconoce los nombres de países en inglés.
        fig_mapa = px.choropleth(
            df_datos, 
            locations="pais", 
            locationmode="country names",
            color="pib_per_capita",
            hover_name="pais",
            color_continuous_scale=px.colors.sequential.Viridis,
            scope="europe",
            labels={'pib_per_capita': 'PIB p.c. (€)'}
        )
        fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_mapa, use_container_width=True)

    with col_ranking:
        st.subheader("🏆 Top 10 Países más ricos")
        top_10 = df_datos.nlargest(10, 'pib_per_capita')[['pais', 'pib_per_capita']]
        
        fig_barras = px.bar(
            top_10, x='pib_per_capita', y='pais', orientation='h',
            color='pib_per_capita', color_continuous_scale='Viridis'
        )
        fig_barras.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_barras, use_container_width=True)

    # 5. Tabla de datos crudos
    st.divider()
    st.subheader("📊 Datos Consolidados (Extraídos de PostgreSQL)")
    st.dataframe(df_datos.style.format({"pib_euros": "{:,.2f} €", "pib_per_capita": "{:,.2f} €", "densidad": "{:,.2f}"}), use_container_width=True)

except Exception as e:
    st.error(f"Error al conectar con la base de datos. ¿Está Docker encendido? Detalle: {e}")