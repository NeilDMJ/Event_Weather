from fastapi import FastAPI,Query
from fastapi.middleware.cors import CORSMiddleware
from app.services.nasapower import get_climate_projection

app = FastAPI(
    title="Climate Projection API",
    description="API for retrieving climate projection data from NASA POWER",
    version="1.0.0",
)
# backend/app/main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app.services.nasapower import get_climate_projection

app = FastAPI(
    title="Will It Rain On My Parade - NASA Space Apps",
    description="API que obtiene proyecciones de precipitación desde NASA POWER",
    version="1.0"
)

# Permitir peticiones desde el frontend (por ejemplo, React, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # puedes restringirlo luego a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """
    Endpoint de bienvenida que muestra información básica de la API.
    """
    return {
        "message": "Will It Rain On My Parade - NASA Space Apps API",
        "description": "API que obtiene proyecciones de precipitación desde NASA POWER",
        "version": "1.0",
        "endpoints": {
            "climate": "/climate?lat={latitude}&lon={longitude}&start={year}&end={year}",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "example": "/climate?lat=17.866667&lon=-97.783333&start=2020&end=2025"
    }

@app.get("/climate")
async def get_climate_data(
    lat: float = Query(..., description="Latitud en grados decimales"),
    lon: float = Query(..., description="Longitud en grados decimales"),
    start: int = Query(2020, description="Año de inicio del rango"),
    end: int = Query(2030, description="Año de fin del rango"),
):
    """
    Devuelve la proyección climática (precipitación total mensual)
    para la ubicación y rango de años especificados.
    """
    data = await get_climate_projection(lat, lon, start, end)
    return {"location": {"lat": lat, "lon": lon}, "projection": data}
