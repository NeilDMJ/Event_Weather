import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.nasapower import get_complete_climate_projection

class ClimatePredictor:
    def __init__(self):
        self.models = {}  # Modelos para cada parámetro
        self.feature_columns = [
            'Month', 'Month_sin', 'Month_cos', 'Season'
        ]
        self.target_parameters = [
            'Precipitation_mm_per_day',
            'Temperature_C', 
            'Temperature_Max_C', 
            'Temperature_Min_C',
            'Humidity_Percent',
            'Wind_Speed_ms',
            'Pressure_kPa',
            'Cloud_Cover_Percent'
        ]
        
    async def collect_training_data(self, lat, lon, target_date):
        """Recolectar 5 años de datos históricos para un solo punto"""
        print(f"Recolectando 5 años de datos históricos para ({lat}, {lon})...")
        
        # Calcular año de inicio (5 años antes del año actual)
        current_year = datetime.now().year
        start_year = current_year - 5
        end_year = current_year - 1  # Año anterior al actual
        
        print(f"Obteniendo datos desde {start_year} hasta {end_year}")
        
        try:
            # Obtener datos históricos directamente de NASA POWER
            data = await get_complete_climate_projection(lat, lon, start_year, end_year)
            
            if "parameters" not in data or not data["parameters"]:
                raise Exception("No se pudieron obtener datos históricos")
            
            # Procesar los datos en formato DataFrame
            records_list = []
            parameters = data["parameters"]
            
            # Usar PRECTOTCORR como referencia para las fechas
            if "PRECTOTCORR" in parameters and parameters["PRECTOTCORR"]["data"]:
                dates = list(parameters["PRECTOTCORR"]["data"].keys())
                
                for date_str in dates:
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                    
                    record = {
                        "Date": date_str,
                        "Year": year,
                        "Month": month,
                        "Latitude": lat,
                        "Longitude": lon
                    }
                    
                    # Mapear parámetros NASA a nombres descriptivos
                    param_mapping = {
                        "PRECTOTCORR": "Precipitation_mm_per_day",
                        "T2M": "Temperature_C",
                        "T2M_MAX": "Temperature_Max_C",
                        "T2M_MIN": "Temperature_Min_C",
                        "RH2M": "Humidity_Percent",
                        "WS2M": "Wind_Speed_ms",
                        "PS": "Pressure_kPa",
                        "CLOUD_AMT": "Cloud_Cover_Percent"
                    }
                    
                    # Agregar cada parámetro climático
                    for nasa_param, column_name in param_mapping.items():
                        if nasa_param in parameters and date_str in parameters[nasa_param]["data"]:
                            record[column_name] = parameters[nasa_param]["data"][date_str]
                    
                    records_list.append(record)
                
                combined_df = pd.DataFrame(records_list)
                print(f"Datos históricos recolectados: {len(combined_df)} registros para {end_year - start_year + 1} años")
                return combined_df
            else:
                raise Exception("No se encontraron datos de precipitación")
                
        except Exception as e:
            print(f"Error recolectando datos: {e}")
            raise
    
    def prepare_features(self, df):
        """Preparar características para entrenamiento - simplificado para un solo punto"""
        df = df.copy()
        
        # Crear características temporales (solo basadas en mes)
        df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
        df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
        
        # Crear características de temporada
        df['Season'] = df['Month'].map({
            12: 0, 1: 0, 2: 0,  # Invierno
            3: 1, 4: 1, 5: 1,   # Primavera
            6: 2, 7: 2, 8: 2,   # Verano
            9: 3, 10: 3, 11: 3  # Otoño
        })
        
        # Limpiar datos: eliminar filas con demasiados NaN en target_parameters
        df_clean = df.dropna(subset=self.target_parameters, thresh=len(self.target_parameters)//2)
        
        # Rellenar valores NaN en características de entrada
        for feature in self.feature_columns:
            if feature in df_clean.columns:
                if df_clean[feature].isna().any():
                    # Para características numéricas, usar mediana
                    if feature in ['Month']:
                        df_clean[feature] = df_clean[feature].fillna(df_clean[feature].median())
                    else:
                        # Para características calculadas, recalcular si es necesario
                        df_clean[feature] = df_clean[feature].fillna(0.0)
        
        # Rellenar valores NaN en parámetros objetivo
        for param in self.target_parameters:
            if param in df_clean.columns:
                median_value = df_clean[param].median()
                if pd.isna(median_value):
                    # Valores por defecto si no hay datos
                    default_values = {
                        'Precipitation_mm_per_day': 1.0,
                        'Temperature_C': 23.0,
                        'Temperature_Max_C': 29.0,
                        'Temperature_Min_C': 17.0,
                        'Humidity_Percent': 65.0,
                        'Wind_Speed_ms': 2.0,
                        'Pressure_kPa': 80.0,
                        'Cloud_Cover_Percent': 50.0
                    }
                    median_value = default_values.get(param, 0.0)
                
                df_clean[param] = df_clean[param].fillna(median_value)
        
        # Verificar que no quedan NaN en las características de entrada
        X_features = df_clean[self.feature_columns]
        if X_features.isna().any().any():
            print("⚠️  Advertencia: Aún hay valores NaN en características de entrada")
            # Rellenar cualquier NaN restante con 0
            df_clean[self.feature_columns] = df_clean[self.feature_columns].fillna(0.0)
        
        print(f"Datos preparados: {len(df_clean)} registros limpios de {len(df)} originales")
        print(f"Características de entrada: {self.feature_columns}")
        return df_clean
    
    def train_models(self, df):
        """Entrenar modelos simplificados para cada parámetro climático"""
        print(f"Entrenando modelos para {len(self.target_parameters)} parámetros...")
        
        # Preparar características de entrada (solo temporales, sin coordenadas)
        X = df[self.feature_columns]
        
        model_metrics = {}
        
        for param in self.target_parameters:
            if param not in df.columns:
                print(f"  Parámetro {param} no encontrado en datos")
                continue
                
            try:
                # Preparar datos para este parámetro
                y = df[param]
                
                # Verificar que hay suficientes datos
                if len(y) < 20:
                    print(f"  {param}: Insuficientes datos ({len(y)} muestras)")
                    continue
                
                # Dividir datos (80% entrenamiento, 20% prueba)
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, shuffle=True
                )
                
                # Entrenar modelo más simple para datos limitados
                model = GradientBoostingRegressor(
                    n_estimators=30,      # Menos estimadores
                    learning_rate=0.1,
                    max_depth=3,          # Menor profundidad
                    min_samples_split=5,  # Mínimo para dividir
                    random_state=42
                )
                
                model.fit(X_train, y_train)
                
                # Evaluar
                y_pred = model.predict(X_test)
                r2 = r2_score(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                
                # Guardar modelo
                self.models[param] = model
                model_metrics[param] = {
                    'r2_score': r2,
                    'mae': mae,
                    'samples': len(X_train)
                }
                
                print(f"  {param}: R²={r2:.3f}, MAE={mae:.3f}, Muestras={len(X_train)}")
                
            except Exception as e:
                print(f"  Error entrenando {param}: {e}")
                continue
        
        print(f"✓ Modelos entrenados exitosamente: {len(self.models)}/{len(self.target_parameters)}")
        return model_metrics
    
    async def predict_for_date(self, lat, lon, target_date):
        """
        Predicción completa para una fecha específica
        
        Args:
            lat (float): Latitud
            lon (float): Longitud  
            target_date (str): Fecha en formato 'YYYY-MM-DD'
            
        Returns:
            dict: Predicción en formato JSON con todos los parámetros
        """
        try:
            # Validar fecha
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            
            print(f" Iniciando predicción para {target_date} en ({lat}, {lon})")
            
            # Paso 1: Recolectar datos de entrenamiento
            training_data = await self.collect_training_data(lat, lon, target_date)
            
            # Paso 2: Preparar características
            prepared_data = self.prepare_features(training_data)
            
            # Paso 3: Entrenar modelos
            model_metrics = self.train_models(prepared_data)
            
            if not self.models:
                raise Exception("No se pudieron entrenar modelos válidos")
            
            # Paso 4: Hacer predicción
            year = target_dt.year
            month = target_dt.month
            
            # Crear características para predicción
            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            
            # Determinar estación
            if month in [12, 1, 2]:
                season = 0  # Invierno
            elif month in [3, 4, 5]:
                season = 1  # Primavera
            elif month in [6, 7, 8]:
                season = 2  # Verano
            else:
                season = 3  # Otoño
            
            # Datos de entrada para predicción (solo características temporales)
            prediction_features = pd.DataFrame([{
                'Month': month,
                'Month_sin': month_sin,
                'Month_cos': month_cos,
                'Season': season
            }])
            
            # Hacer predicciones para cada parámetro
            predictions = {}
            
            # Valores por defecto si no hay modelo disponible
            default_values = {
                'Precipitation_mm_per_day': 2.0,
                'Temperature_C': 23.0,
                'Temperature_Max_C': 29.0,
                'Temperature_Min_C': 17.0,
                'Humidity_Percent': 65.0,
                'Wind_Speed_ms': 2.0,
                'Pressure_kPa': 80.0,
                'Cloud_Cover_Percent': 50.0
            }
            
            for param in self.target_parameters:
                if param in self.models:
                    try:
                        pred_value = self.models[param].predict(prediction_features)[0]
                        predictions[param] = float(pred_value)
                    except Exception as e:
                        print(f"  Error prediciendo {param}: {e}")
                        # Usar valores por defecto como fallback
                        predictions[param] = default_values.get(param, 0.0)
                else:
                    print(f"  Modelo no disponible para {param}")
                    # Usar valores por defecto como fallback
                    predictions[param] = default_values.get(param, 0.0)
            
            # Formato de salida JSON
            result = {
                "date": target_date,
                "latitude": lat,
                "longitude": lon,
                "training_years": 5,
                "models_trained": len(self.models),
                "model_metrics": model_metrics,
                "predictions": {
                    "precipitation_mm_per_day": round(predictions.get('Precipitation_mm_per_day', 0.0), 3),
                    "temperature_c": round(predictions.get('Temperature_C', 0.0), 2),
                    "temperature_max_c": round(predictions.get('Temperature_Max_C', 0.0), 2),
                    "temperature_min_c": round(predictions.get('Temperature_Min_C', 0.0), 2),
                    "humidity_percent": round(predictions.get('Humidity_Percent', 0.0), 1),
                    "wind_speed_ms": round(predictions.get('Wind_Speed_ms', 0.0), 2),
                    "pressure_kpa": round(predictions.get('Pressure_kPa', 0.0), 2),
                    "cloud_cover_percent": round(predictions.get('Cloud_Cover_Percent', 0.0), 1)
                },
                "generated_at": datetime.now().isoformat()
            }
            
            print(f"✓ Predicción completada exitosamente")
            return result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "date": target_date,
                "latitude": lat,
                "longitude": lon,
                "generated_at": datetime.now().isoformat()
            }
            print(f"✗ Error en predicción: {e}")
            return error_result

