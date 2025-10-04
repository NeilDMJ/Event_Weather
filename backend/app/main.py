from fastapi import FastAPI,Query
from fastapi.middleware.cors import CORSMiddleware
from app.services.nasapower import get_climate_projection

# backend/app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.nasapower import get_climate_projection
from typing import List, Optional
import os

app = FastAPI(
    title="Climate Projection API",
    description="API for retrieving climate projection data from NASA POWER",
    version="1.0.0",
)


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
    end: int = Query(2025, description="Año de fin del rango"),
):
    """
    Devuelve la proyección climática (precipitación total mensual)
    para la ubicación y rango de años especificados.
    """
    
@app.get("/climate/complete")
async def get_complete_climate_data(
    lat: float = Query(..., description="Latitud en grados decimales"),
    lon: float = Query(..., description="Longitud en grados decimales"),
    start: int = Query(2020, description="Año de inicio del rango"),
    end: int = Query(2030, description="Año de fin del rango"),
):
    """
    Devuelve la proyección climática completa (precipitación total mensual)
    para la ubicación y rango de años especificados.

    Incluye:
    - Precipitación (PRECTOTCORR)
    - Temperatura (T2M, T2M_MAX, T2M_MIN)
    - Humedad relativa (RH2M)
    - Velocidad del viento (WS2M)
    - Presión superficial (PS)
    - Nubosidad (CLOUD_AMT)
    """

@app.get("/climate/temperature")
async def get_temperatura_data(
    lat: float = Query(...,description="Latitud en grados decimales"),
    lon: float = Query(..., description="Longitud en grados decimales"),
    start: int = Query(2020, description="Año de inicio del rango"),
    end: int = Query(2030, description="Año de fin del rango"),
):
    """
    Temperatura a 2 metros : T2M, T2M_MAX, T2M_MIN
    """

@app.get("/climate/atmosferic")
async def get_atmosferic_data(
    lat: float = Query(...,description="Latitud en grados decimales"),
    lon: float = Query(...,description="Longitud en grados decimales"),
    start: int = Query(2020, description="Año de inicio del rango"),
    end: int = Query(2030, description="Año de fin del rango"),
):
    """
    Datos atmosféricos:
    - Humedad relativa (RH2M)
    - Velocidad del viento (WS2M, WS10M, WS50M)
    - Dirección del viento (WD2M, WD10M, WD50M)
    - Presión superficial (PS)
    """
@app.get("/climate/solar")
async def get_solar_data(
    lat: float = Query(..., description ="Latitud en grados decimales"),
    lon : float = Query(..., description="Longitud en grados decimales"),
    start: int = Query(2020, description="Año de inicio del rango"),
    end: int = Query(2030, description="Año de fin del rango"),
):
    """Datos solares:
    Datos de radiación solar:
    - Irradiancia de onda corta (ALLSKY_SFC_SW_DWN)
    - Irradiancia de onda larga (ALLSKY_SFC_LW_DWN)
    - Nubosidad (CLOUD_AMT)
    """ 

    data = await get_climate_projection(lat, lon, start, end)
    return {"location": {"lat": lat, "lon": lon}, "projection": data}
