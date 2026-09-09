# 🌍 Geostat Data Engineering Pipeline

Bienvenido al repositorio del proyecto **Geostat**. Este proyecto consiste en un pipeline de datos completo (ETL) que extrae información demográfica y económica, la procesa aplicando reglas de calidad de datos, y la consolida en una base de datos relacional para su posterior explotación analítica.

## 🛠️ Tecnologías Utilizadas
* **Lenguaje:** Python 3.11
* **Base de Datos:** PostgreSQL (Dockerizada) y SQLite (Legacy)
* **Visualización:** Streamlit (Dashboard Interactivo)
* **Microservicio:** FastAPI & Uvicorn (API REST)
* **Infraestructura:** Docker & Docker Compose

## 🚀 Cómo ejecutar este proyecto en local

Sigue estos pasos para levantar toda la infraestructura y servicios en tu propio equipo.

### 1. Requisitos Previos
* Tener instalado [Docker Desktop](https://www.docker.com/products/docker-desktop/).
* Tener instalado Python 3.9 o superior.
* Clonar este repositorio y crear un entorno virtual instalando las dependencias (`pip install -r requirements.txt`).

### 2. Levantar la Base de Datos
El proyecto utiliza un contenedor de Docker para alojar PostgreSQL en el puerto `5434`.
```bash
docker-compose up -d