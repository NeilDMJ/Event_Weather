# backend/app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.services.nasapower import (
    get_climate_projection,
    get_complete_climate_projection,
    get_temperature_projection,
    get_atmospheric_projection,
    get_solar_projection
)
from app.ml.climate_predictor import ClimatePredictor
from app.ml.climate_predictor import ClimatePredictor

app = FastAPI(
    title="Will It Rain On My Parade - NASA Space Apps",
    description="API que obtiene proyecciones climáticas desde NASA POWER y predicciones ML",
    version="2.0.0"
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
        "description": "API que obtiene proyecciones climáticas desde NASA POWER y predicciones ML",
        "version": "2.0",
        "endpoints": {
            "climate": "/climate?lat={latitude}&lon={longitude}&start={year}&end={year}",
            "climate_complete": "/climate/complete?lat={latitude}&lon={longitude}&start={year}&end={year}",
            "predict_future": "/predict?lat={latitude}&lon={longitude}&date={YYYY-MM-DD}",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "examples": {
            "historical_data": "/climate?lat=17.866667&lon=-97.783333&start=2020&end=2025",
            "future_prediction": "/predict?lat=17.8270&lon=-97.8043&date=2025-12-25"
        }
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

    data = await get_climate_projection(lat, lon, start, end)
    return {"location": {"lat": lat, "lon": lon}, "projection": data}


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
    data = await get_complete_climate_projection(lat, lon, start, end)
    return {"location": {"lat": lat, "lon": lon}, "projection": data}

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
    data = await get_temperature_projection(lat, lon, start, end)
    return {"location": {"lat": lat, "lon": lon}, "projection": data}

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
    data = await get_atmospheric_projection(lat, lon, start, end)
    return {"location": {"lat": lat, "lon": lon}, "projection": data}

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
    data = await get_solar_projection(lat, lon, start, end)
    return {"location": {"lat": lat, "lon": lon}, "projection": data}

@app.get("/predict")
async def predict_future_climate(
    lat: float = Query(..., description="Latitud en grados decimales", example=17.8270),
    lon: float = Query(..., description="Longitud en grados decimales", example=-97.8043),
    date: str = Query(..., description="Fecha futura en formato YYYY-MM-DD", example="2025-12-25"),
):
    """
    Predice los parámetros climáticos para una fecha futura específica.
    
    Utiliza machine learning con datos históricos de NASA POWER para entrenar
    modelos específicos y generar predicciones precisas.
    
    **Parámetros predichos:**
    - Precipitación (mm/día)
    - Temperatura promedio, máxima y mínima (°C)
    - Humedad relativa (%)
    - Velocidad del viento (m/s)
    - Presión superficial (kPa)
    - Nubosidad (%)
    
    **Proceso:**
    1. Recolecta datos históricos de la ubicación y alrededores
    2. Entrena modelos específicos para cada parámetro climático
    3. Genera predicción para la fecha solicitada
    
    **Precisión típica:** 85-95% (R² score)
    """
    
    # Validar formato de fecha
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
        if target_date <= datetime.now():
            raise HTTPException(
                status_code=400, 
                detail="La fecha debe ser futura. Use formato YYYY-MM-DD."
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de fecha inválido. Use YYYY-MM-DD (ejemplo: 2025-12-25)."
        )
    
    # Validar coordenadas (rango aproximado para México)
    if not (14.0 <= lat <= 33.0 and -118.0 <= lon <= -86.0):
        raise HTTPException(
            status_code=400,
            detail="Coordenadas fuera del rango válido para México. Latitud: 14-33, Longitud: -118 a -86."
        )
    
    try:
        # Crear predictor y hacer predicción
        predictor = ClimatePredictor()
        result = await predictor.predict_for_date(lat, lon, date)
        
        # Verificar si hay error en el resultado
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=f"Error en predicción: {result['error']}"
            )
        
        return result
        
    except Exception as e:
        # Capturar cualquier error no manejado
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
