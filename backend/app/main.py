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
from app.ml.climate_predictor_functional import ClimatePredictor, obtener_o_entrenar_modelo
import pandas as pd
import numpy as np

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
    
    try:
        # Coordenadas del punto objetivo
        coordenadas = (lat, lon)
        
        # Obtener o entrenar modelo para las coordenadas
        print(f"🔍 Buscando/entrenando modelo para ({lat}, {lon})")
        modelos = await obtener_o_entrenar_modelo(coordenadas, distancia_maxima=100)
        
        if not modelos:
            raise HTTPException(
                status_code=500,
                detail="No se pudo obtener o entrenar un modelo para esta ubicación"
            )
        
        # Preparar características para predicción
        year = target_date.year
        month = target_date.month
        
        # Características temporales cíclicas
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        
        # Crear DataFrame con características para predicción (sin Season)
        features = pd.DataFrame([{
            'Year': year,
            'Month': month,
            'Latitude': lat,
            'Longitude': lon,
            'Month_sin': month_sin,
            'Month_cos': month_cos
        }])
        
        # Hacer predicciones con cada modelo
        predicciones = {}
        modelos_usados = []
        
        # Mapeo de nombres de parámetros para la respuesta
        param_names = {
            'Precipitation_mm_per_day': 'precipitation_mm_per_day',
            'Temperature_C': 'temperature_c',
            'Temperature_Max_C': 'temperature_max_c',
            'Temperature_Min_C': 'temperature_min_c',
            'Humidity_Percent': 'humidity_percent',
            'Wind_Speed_ms': 'wind_speed_ms',
            'Pressure_kPa': 'pressure_kpa',
            'Cloud_Cover_Percent': 'cloud_cover_percent'
        }
        
        # Valores por defecto en caso de error
        default_values = {
            'precipitation_mm_per_day': 2.0,
            'temperature_c': 23.0,
            'temperature_max_c': 29.0,
            'temperature_min_c': 17.0,
            'humidity_percent': 65.0,
            'wind_speed_ms': 2.0,
            'pressure_kpa': 80.0,
            'cloud_cover_percent': 50.0
        }
        
        for param_model_name, modelo in modelos.items():
            try:
                pred_value = modelo.predict(features)[0]
                
                # Limpiar nombre del parámetro (quitar timestamp si existe)
                clean_param_name = param_model_name
                if '_20251004' in clean_param_name:
                    clean_param_name = clean_param_name.split('_20251004')[0]
                
                # Convertir nombre del parámetro
                response_name = param_names.get(clean_param_name, clean_param_name.lower())
                predicciones[response_name] = round(float(pred_value), 3)
                modelos_usados.append(param_model_name)
                
            except Exception as e:
                print(f"Error prediciendo {param_model_name}: {e}")
                # Usar valor por defecto solo si no hay predicción
                clean_param_name = param_model_name
                if '_20251004' in clean_param_name:
                    clean_param_name = clean_param_name.split('_20251004')[0]
                
                response_name = param_names.get(clean_param_name, clean_param_name.lower())
                if response_name in default_values and response_name not in predicciones:
                    predicciones[response_name] = default_values[response_name]
        
        # Solo agregar valores por defecto para parámetros que no tuvieron predicción
        for response_name, default_val in default_values.items():
            if response_name not in predicciones:
                predicciones[response_name] = default_val
        
        # Preparar respuesta
        response = {
            "success": True,
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "prediction_date": date,
            "predictions": predicciones,
            "model_info": {
                "models_used": modelos_usados,
                "total_models": len(modelos),
                "prediction_method": "gradient_boosting_regressor"
            },
            "generated_at": datetime.now().isoformat()
        }
        
        print(f"✅ Predicción completada para ({lat}, {lon}) - {date}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Error en predicción: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor durante la predicción: {str(e)}"
        )
