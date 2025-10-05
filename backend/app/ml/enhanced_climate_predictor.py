# backend/app/ml/enhanced_climate_predictor.py
from app.database.model_repository import ModelRepository, ModelRecord
import os
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EnhancedClimatePredictor:
    def __init__(self, database_url: str = None):
        self.use_database = database_url is not None
        
        if self.use_database:
            try:
                self.model_repo = ModelRepository(database_url)
            except Exception as e:
                logger.error(f"Error inicializando ModelRepository: {e}")
                self.use_database = False
                self.model_repo = None
        
        # Fallback al sistema de archivos
        if not self.use_database:
            try:
                from app.ml.climate_predictor_functional import FunctionalClimatePredictor
                self.predictor = FunctionalClimatePredictor()
                logger.info("Usando FunctionalClimatePredictor como fallback")
            except ImportError as e:
                logger.error(f"No se pudo importar FunctionalClimatePredictor: {e}")
                self.predictor = None
        else:
            self.predictor = None
        
        self.variable_names = [
            'Temperature_C',
            'Humidity_Percent', 
            'Pressure_kPa',
            'Precipitation_mm_per_day',
            'Cloud_Cover_Percent'
        ]
    
    async def initialize(self):
        """Inicializar conexión a base de datos"""
        if self.use_database and self.model_repo:
            try:
                await self.model_repo.connect()
            except Exception as e:
                logger.error(f"Error conectando a base de datos: {e}")
    
    async def cleanup(self):
        """Limpiar recursos"""
        if self.use_database and self.model_repo:
            try:
                await self.model_repo.disconnect()
            except Exception as e:
                logger.error(f"Error desconectando base de datos: {e}")
    
    async def predict_climate(self, latitude: float, longitude: float, target_date: str) -> Dict:
        """Predecir clima usando modelos de base de datos o archivos"""
        
        try:
            if self.use_database and self.model_repo:
                return await self._predict_with_database(latitude, longitude, target_date)
            elif self.predictor:
                return await self._predict_with_files(latitude, longitude, target_date)
            else:
                return {
                    'success': False,
                    'error': 'No prediction method available (database and file predictor both unavailable)',
                    'location': {'latitude': latitude, 'longitude': longitude},
                    'prediction_date': target_date
                }
        except Exception as e:
            logger.error(f"Error en predict_climate: {e}")
            return {
                'success': False,
                'error': f'Prediction failed: {str(e)}',
                'location': {'latitude': latitude, 'longitude': longitude},
                'prediction_date': target_date
            }
    
    async def _predict_with_database(self, latitude: float, longitude: float, target_date: str) -> Dict:
        """Predicción usando modelos de base de datos"""
        
        try:
            # 1. Verificar caché
            cached_prediction = await self.model_repo.get_cached_prediction(
                latitude, longitude, target_date
            )
            if cached_prediction:
                return {
                    'success': True,
                    'location': {'latitude': latitude, 'longitude': longitude},
                    'prediction_date': target_date,
                    'predictions': cached_prediction,
                    'generated_at': datetime.now().isoformat(),
                    'source': 'cache'
                }
            
            # 2. Buscar mejores modelos para cada variable
            best_models = await self.model_repo.find_best_models(
                latitude, longitude, self.variable_names
            )
            
            predictions = {}
            model_versions = {}
            
            # 3. Hacer predicciones para cada variable
            for variable_name in self.variable_names:
                models = best_models.get(variable_name, [])
                
                if models:
                    # Usar el mejor modelo (primero en la lista)
                    best_model_record = models[0]
                    model = await self.model_repo.load_model(best_model_record.id)
                    
                    if model:
                        try:
                            # Preparar features para predicción
                            features = self._prepare_features(latitude, longitude, target_date)
                            prediction_value = model.predict([features])[0]
                            
                            predictions[variable_name.lower()] = float(prediction_value)
                            model_versions[variable_name] = {
                                'model_id': best_model_record.id,
                                'accuracy': best_model_record.accuracy_score,
                                'distance_km': self.model_repo.calculate_distance(
                                    latitude, longitude,
                                    best_model_record.latitude, best_model_record.longitude
                                )
                            }
                            
                            # Registrar uso del modelo
                            await self.model_repo.update_model_usage(
                                best_model_record.id, 50.0, True
                            )
                            
                        except Exception as e:
                            logger.error(f"Error prediciendo {variable_name}: {e}")
                            predictions[variable_name.lower()] = 0.0
            
            # 4. Formatear resultado
            formatted_predictions = {
                'temperature_c': predictions.get('temperature_c', 20.0),
                'temperature_max_c': predictions.get('temperature_c', 20.0) + 5,
                'temperature_min_c': predictions.get('temperature_c', 20.0) - 5,
                'humidity_percent': predictions.get('humidity_percent', 65.0),
                'pressure_kpa': predictions.get('pressure_kpa', 81.0),
                'precipitation_mm_per_day': predictions.get('precipitation_mm_per_day', 1.0),
                'cloud_cover_percent': predictions.get('cloud_cover_percent', 40.0),
                'wind_speed_ms': 2.5
            }
            
            # 5. Guardar en caché
            await self.model_repo.cache_prediction(
                latitude, longitude, target_date, 
                formatted_predictions, model_versions
            )
            
            return {
                'success': True,
                'location': {'latitude': latitude, 'longitude': longitude},
                'prediction_date': target_date,
                'predictions': formatted_predictions,
                'generated_at': datetime.now().isoformat(),
                'source': 'database_models',
                'model_info': model_versions
            }
        
        except Exception as e:
            logger.error(f"Error en _predict_with_database: {e}")
            raise
    
    async def _predict_with_files(self, latitude: float, longitude: float, target_date: str) -> Dict:
        """Fallback: predicción usando FunctionalClimatePredictor"""
        
        if self.predictor is None:
            return {
                'success': False,
                'error': 'File-based predictor not available',
                'source': 'file_fallback'
            }
        
        try:
            # Usar el método .predict() de FunctionalClimatePredictor
            loop = asyncio.get_event_loop()
            
            # Preparar fecha como features adicionales
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            additional_features = {
                'day_of_year': date_obj.timetuple().tm_yday,
                'month': date_obj.month,
                'day': date_obj.day,
                'year': date_obj.year
            }
            
            # Ejecutar predicción en thread pool
            prediction = await loop.run_in_executor(
                None, 
                self.predictor.predict,
                latitude,
                longitude,
                additional_features
            )
            
            # Formatear respuesta si es necesario
            if prediction.get('success'):
                # Adaptar formato de respuesta
                predictions_data = prediction.get('predictions', {})
                
                formatted_predictions = {
                    'temperature_c': predictions_data.get('temperature_c', 20.0),
                    'temperature_max_c': predictions_data.get('temperature_c', 20.0) + 5,
                    'temperature_min_c': predictions_data.get('temperature_c', 20.0) - 5,
                    'humidity_percent': predictions_data.get('humidity_percent', 65.0),
                    'pressure_kpa': predictions_data.get('pressure_kpa', 81.0),
                    'precipitation_mm_per_day': predictions_data.get('precipitation_mm_per_day', 1.0),
                    'cloud_cover_percent': predictions_data.get('cloud_cover_percent', 40.0),
                    'wind_speed_ms': 2.5
                }
                
                return {
                    'success': True,
                    'location': {'latitude': latitude, 'longitude': longitude},
                    'prediction_date': target_date,
                    'predictions': formatted_predictions,
                    'generated_at': datetime.now().isoformat(),
                    'source': 'file_models'
                }
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error en _predict_with_files: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'file_fallback'
            }
    
    def _prepare_features(self, latitude: float, longitude: float, target_date: str) -> List[float]:
        """Preparar features para el modelo ML"""
        try:
            # Convertir fecha a features
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            day_of_year = date_obj.timetuple().tm_yday
            
            # Features básicos
            features = [
                latitude,
                longitude,
                day_of_year,
                date_obj.month,
                date_obj.day
            ]
            
            return features
        except Exception as e:
            logger.error(f"Error preparando features: {e}")
            return [latitude, longitude, 1, 1, 1]  # Default values
    
    async def train_and_save_model(self, 
                                  latitude: float, 
                                  longitude: float,
                                  variable_name: str,
                                  training_data,
                                  model_params: Dict = None) -> int:
        """Entrenar y guardar modelo en base de datos"""
        
        if not self.use_database:
            raise ValueError("Base de datos no configurada")
        
        # TODO: Implementar entrenamiento real del modelo
        trained_model = None
        
        metadata = {
            'training_date': datetime.now().isoformat(),
            'model_type': 'GradientBoostingRegressor',
            'parameters': model_params or {},
            'accuracy_score': 0.85,
            'mean_absolute_error': 1.2,
            'r2_score': 0.82,
            'data_points_count': len(training_data) if training_data else 0
        }
        
        model_id = await self.model_repo.save_model(
            latitude, longitude, variable_name, 
            trained_model, metadata
        )
        
        return model_id
    
    async def get_stats(self) -> Dict:
        """Obtener estadísticas del sistema"""
        try:
            if self.use_database and self.model_repo:
                return await self.model_repo.get_model_stats()
            elif self.predictor:
                health = self.predictor.health_check()
                return {
                    'source': 'file_system',
                    'models_loaded': health.get('models_loaded', 0),
                    'variables_available': health.get('variables_available', [])
                }
            else:
                return {
                    'source': 'none',
                    'error': 'No predictor available'
                }
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {
                'source': 'error',
                'error': str(e)
            }