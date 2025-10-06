# backend/app/main.py - Event Weather API con base de datos PostgreSQL
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from dotenv import load_dotenv
import os
from app.ml.enhanced_climate_predictor import EnhancedClimatePredictor
from app.services.nasapower import (
    get_climate_projection,
    get_complete_climate_projection,
    get_temperature_projection,
    get_atmospheric_projection,
    get_solar_projection
)
from app.services.gemini_service import get_gemini_service

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Event Weather - Enhanced ML API",
    description="API con predicciones ML usando base de datos PostgreSQL",
    version="2.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar predictor mejorado
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://eventweather_user:eventweather_pass@postgres:5432/eventweather_db")
enhanced_predictor = EnhancedClimatePredictor(DATABASE_URL)

# backend/app/main.py

# ... (tus imports y la inicialización de la app FastAPI) ...

# Inicializar predictor mejorado
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://eventweather_user:eventweather_pass@localhost:5432/eventweather_db")
enhanced_predictor = EnhancedClimatePredictor(DATABASE_URL)

# --- INICIO DEL CÓDIGO A AGREGAR ---

@app.on_event("startup")
async def startup_event():
    """
    Inicializar la conexión a la base de datos cuando la aplicación arranque.
    """
    if enhanced_predictor.use_database:
        await enhanced_predictor.initialize()
        print("INFO:     Conexión a la base de datos inicializada.")
    else:
        print("INFO:     La base de datos no está configurada, operando en modo fallback.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cerrar la conexión a la base de datos cuando la aplicación se detenga.
    """
    if enhanced_predictor.use_database:
        await enhanced_predictor.cleanup()
        print("INFO:     Conexión a la base de datos cerrada.")

# --- FIN DEL CÓDIGO A AGREGAR ---

@app.get("/")
async def root():
    """Información de la API"""
    stats = await enhanced_predictor.get_stats()
    return {
        "message": "Event Weather - Enhanced ML API",
        "version": "2.1.0",
        "database_enabled": enhanced_predictor.use_database,
        "status": "online",
        "database_stats": stats,
        "endpoints": {
            "predict": "/predict?lat=17.827&lon=-97.8043&date=2025-12-25",
            "stats": "/stats",
            "health": "/health"
        }
    }

@app.get("/predict")
async def predict_climate(
    lat: float = Query(..., description="Latitud", ge=-90, le=90),
    lon: float = Query(..., description="Longitud", ge=-180, le=180),
    date: str = Query(..., description="Fecha de predicción (YYYY-MM-DD)")
):
    """
    Predecir clima usando modelos ML de base de datos
    
    Busca automáticamente los mejores modelos disponibles para la ubicación
    y genera predicciones optimizadas por precisión y proximidad geográfica.
    """
    try:
        # Validar formato de fecha
        datetime.strptime(date, '%Y-%m-%d')
        
        # Hacer predicción mejorada
        prediction = await enhanced_predictor.predict_climate(lat, lon, date)
        
        if not prediction.get('success', False):
            raise HTTPException(status_code=404, detail="No se pudieron generar predicciones para esta ubicación")
        
        return prediction
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/stats")
async def get_database_stats():
    """Obtener estadísticas de la base de datos de modelos"""
    try:
        stats = await enhanced_predictor.get_stats()
        return {
            "success": True,
            "database_stats": stats,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check de la API y base de datos"""
    try:
        # Verificar conexión a base de datos
        stats = await enhanced_predictor.get_stats()
        
        return {
            "status": "healthy",
            "database_connected": enhanced_predictor.use_database,
            "total_models": stats.get('total_models', 0),
            "timestamp": datetime.now().isoformat(),
            "version": "2.1.0"
        }
    except Exception as e:
        return {
            "status": "degraded", 
            "error": str(e),
            "database_connected": False,
            "timestamp": datetime.now().isoformat()
        }

# Mantener endpoints originales para compatibilidad
@app.get("/climate")
async def get_climate_data(
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"), 
    start: int = Query(2020, description="Año inicial"),
    end: int = Query(2025, description="Año final")
):
    """Obtener datos climáticos (endpoint original mantenido)"""
    try:
        data = await get_climate_projection(lat, lon, start, end)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/climate/complete")
async def get_complete_climate_data(
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    start: int = Query(2020, description="Año inicial"), 
    end: int = Query(2030, description="Año final")
):
    """Datos climáticos completos"""
    try:
        data = await get_complete_climate_projection(lat, lon, start, end)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/climate/temperature")
async def get_temperature_data(
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    start: int = Query(2020, description="Año inicial"),
    end: int = Query(2030, description="Año final")
):
    """Datos de temperatura"""
    try:
        data = await get_temperature_projection(lat, lon, start, end)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/climate/atmosferic")
async def get_atmospheric_data(
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    start: int = Query(2020, description="Año inicial"),
    end: int = Query(2030, description="Año final")
):
    """Datos atmosféricos"""
    try:
        data = await get_atmospheric_projection(lat, lon, start, end)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/climate/solar")
async def get_solar_data(
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    start: int = Query(2020, description="Año inicial"),
    end: int = Query(2030, description="Año final")
):
    """Datos solares"""
    try:
        data = await get_solar_projection(lat, lon, start, end)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)