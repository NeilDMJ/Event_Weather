# backend/app/database/model_repository.py
import asyncpg
import joblib
import json
import io
import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ModelRecord:
    id: int
    latitude: float
    longitude: float
    variable_name: str
    model_data: bytes
    model_metadata: dict
    training_date: datetime
    accuracy_score: float
    mean_absolute_error: float
    r2_score: float
    data_points_count: int
    geographic_hash: str
    is_active: bool

class ModelRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def connect(self):
        """Inicializar pool de conexiones"""
        self.pool = await asyncpg.create_pool(self.database_url)
    
    async def disconnect(self):
        """Cerrar pool de conexiones"""
        if self.pool:
            await self.pool.close()
    
    def calculate_geo_hash(self, lat: float, lon: float) -> str:
        """Calcular hash geográfico para agrupar modelos por región"""
        return f"{round(lat, 1)},{round(lon, 1)}"
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcular distancia usando fórmula de Haversine"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c  # Radio de la Tierra en km
    
    async def save_model(self, 
                        latitude: float, 
                        longitude: float,
                        variable_name: str,
                        model,
                        metadata: dict) -> int:
        """Guardar modelo entrenado en la base de datos"""
        
        # Serializar modelo
        model_buffer = io.BytesIO()
        joblib.dump(model, model_buffer)
        model_data = model_buffer.getvalue()
        
        geo_hash = self.calculate_geo_hash(latitude, longitude)
        
        async with self.pool.acquire() as conn:
            model_id = await conn.fetchval(
                """
                INSERT INTO trained_models 
                (latitude, longitude, variable_name, model_data, model_metadata, 
                 accuracy_score, mean_absolute_error, r2_score, data_points_count, geographic_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """,
                latitude, longitude, variable_name, model_data, json.dumps(metadata),
                metadata.get('accuracy_score', 0), 
                metadata.get('mean_absolute_error', 0),
                metadata.get('r2_score', 0),
                metadata.get('data_points_count', 0),
                geo_hash
            )
        
        return model_id
    
    async def find_best_models(self, 
                              latitude: float, 
                              longitude: float,
                              variable_names: List[str],
                              max_distance_km: float = 100,
                              max_models: int = 3) -> Dict[str, List[ModelRecord]]:
        """Encontrar los mejores modelos para una ubicación específica"""
        
        results = {}
        
        async with self.pool.acquire() as conn:
            for variable in variable_names:
                # Buscar modelos cercanos con buena precisión
                rows = await conn.fetch(
                    """
                    SELECT * FROM trained_models 
                    WHERE variable_name = $1 
                      AND is_active = true
                      AND accuracy_score > 0.7
                    ORDER BY accuracy_score DESC
                    LIMIT 50
                    """, 
                    variable
                )
                
                # Filtrar por distancia y ordenar por precisión + distancia
                model_candidates = []
                for row in rows:
                    distance = self.calculate_distance(
                        latitude, longitude, 
                        float(row['latitude']), float(row['longitude'])
                    )
                    
                    if distance <= max_distance_km:
                        # Score combinado: precisión (70%) + proximidad (30%)
                        distance_score = max(0, 1 - (distance / max_distance_km))
                        combined_score = (0.7 * row['accuracy_score']) + (0.3 * distance_score)
                        
                        model_candidates.append({
                            'record': ModelRecord(**dict(row)),
                            'distance': distance,
                            'combined_score': combined_score
                        })
                
                # Ordenar por score combinado y tomar los mejores
                model_candidates.sort(key=lambda x: x['combined_score'], reverse=True)
                results[variable] = [
                    candidate['record'] 
                    for candidate in model_candidates[:max_models]
                ]
        
        return results
    
    async def load_model(self, model_id: int):
        """Cargar modelo desde la base de datos"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT model_data FROM trained_models WHERE id = $1",
                model_id
            )
            
            if row:
                model_buffer = io.BytesIO(row['model_data'])
                return joblib.load(model_buffer)
            return None
    
    async def cache_prediction(self, 
                              latitude: float, 
                              longitude: float,
                              prediction_date: str,
                              predictions: dict,
                              model_versions: dict):
        """Guardar predicción en caché"""
        async with self.pool.acquire() as conn:
            date_obj = datetime.strptime(prediction_date, '%Y-%m-%d').date()
            await conn.execute(
                """
                INSERT INTO prediction_cache 
                (latitude, longitude, prediction_date, predictions, model_versions, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (latitude, longitude, prediction_date) 
                DO UPDATE SET 
                    predictions = EXCLUDED.predictions,
                    model_versions = EXCLUDED.model_versions,
                    created_at = CURRENT_TIMESTAMP,
                    expires_at = EXCLUDED.expires_at
                """,
                latitude, longitude, date_obj,
                json.dumps(predictions), json.dumps(model_versions),
                datetime.now() + timedelta(hours=6)  # Cache por 6 horas
            )
    
    async def get_cached_prediction(self, 
                                   latitude: float, 
                                   longitude: float,
                                   prediction_date: str) -> Optional[dict]:
        """Obtener predicción del caché si existe y no ha expirado"""
        async with self.pool.acquire() as conn:
            date_obj = datetime.strptime(prediction_date, '%Y-%m-%d').date()
            row = await conn.fetchrow(
                """
                SELECT predictions FROM prediction_cache 
                WHERE latitude = $1 AND longitude = $2 AND prediction_date = $3
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                latitude, longitude, date_obj
            )
            
            if row:
                return json.loads(row['predictions'])
            return None
    
    async def update_model_usage(self, model_id: int, response_time_ms: float, success: bool):
        """Actualizar estadísticas de uso del modelo"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO model_usage_stats (model_id, usage_count, average_response_time, success_rate)
                VALUES ($1, 1, $2, $3)
                ON CONFLICT (model_id) DO UPDATE SET
                    usage_count = model_usage_stats.usage_count + 1,
                    average_response_time = (model_usage_stats.average_response_time + $2) / 2,
                    success_rate = (model_usage_stats.success_rate + $3) / 2,
                    last_used = CURRENT_TIMESTAMP
                """,
                model_id, response_time_ms, 1.0 if success else 0.0
            )
    
    async def get_model_stats(self, days: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas de uso de modelos"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_models,
                    COUNT(*) FILTER (WHERE is_active) as active_models,
                    AVG(accuracy_score) as avg_accuracy,
                    COUNT(DISTINCT geographic_hash) as regions_covered
                FROM trained_models
                """
            )
            
            usage_stats = await conn.fetchrow(
                f"""
                SELECT 
                    SUM(usage_count) as total_predictions,
                    AVG(average_response_time) as avg_response_time,
                    AVG(success_rate) as avg_success_rate
                FROM model_usage_stats 
                WHERE last_used > CURRENT_TIMESTAMP - INTERVAL '{days} days'
                """
            )
            
            return {
                'total_models': stats['total_models'],
                'active_models': stats['active_models'],
                'average_accuracy': float(stats['avg_accuracy'] or 0),
                'regions_covered': stats['regions_covered'],
                'total_predictions': usage_stats['total_predictions'] or 0,
                'average_response_time_ms': float(usage_stats['avg_response_time'] or 0),
                'average_success_rate': float(usage_stats['avg_success_rate'] or 0)
            }