import pandas as pd
import numpy as np
import joblib
import json
import os
import glob
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.nasapower import get_complete_climate_projection

class ClimatePredictor:
    def __init__(self):
        """
        Predictor de clima que usa data_collector y model_trainer
        para entrenar modelos específicos y predecir todos los parámetros climáticos
        """
        self.models = {}  # Modelos para cada parámetro
        self.feature_columns = [
            'Year', 'Month', 'Latitude', 'Longitude', 'Month_sin', 'Month_cos', 'Season'
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
        """Recolectar datos de entrenamiento para la ubicación y fecha especificadas"""
        print(f"Recolectando datos para entrenamiento...")
        
        # Parsear fecha objetivo
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        
        # Determinar rango de años para obtener datos históricos
        current_year = datetime.now().year
        start_year = max(2010, current_year - 10)  
        end_year = current_year
        
        print(f"Obteniendo datos históricos: {start_year}-{end_year}")
        
        # Ubicaciones para entrenamiento (ubicación objetivo + ubicaciones cercanas)
        training_locations = [
            (lat, lon),                    # Ubicación objetivo
        ]
        
        all_data = []
        
        for train_lat, train_lon in training_locations:
            try:
                # Obtener datos climáticos completos
                climate_data = await get_complete_climate_projection(train_lat, train_lon, start_year, end_year)
                
                if "parameters" not in climate_data or not climate_data["parameters"]:
                    continue
                
                # Convertir a DataFrame
                df_location = self._parse_nasa_data(climate_data, train_lat, train_lon)
                
                if not df_location.empty:
                    all_data.append(df_location)
                    print(f"Datos obtenidos para ({train_lat:.3f}, {train_lon:.3f}): {len(df_location)} registros")
                    
            except Exception as e:
                print(f"Error obteniendo datos para ({train_lat:.3f}, {train_lon:.3f}): {e}")
                continue
        
        if not all_data:
            raise Exception("No se pudieron obtener datos de entrenamiento")
        
        # Combinar todos los datos
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"Total de datos recolectados: {len(combined_df)} registros")
        
        return combined_df
    
    def _parse_nasa_data(self, climate_data, lat, lon):
        """Convertir datos de NASA POWER a DataFrame"""
        parameters = climate_data.get("parameters", {})
        
        if not parameters or "PRECTOTCORR" not in parameters:
            return pd.DataFrame()
        
        dates = list(parameters["PRECTOTCORR"]["data"].keys())
        records = []
        
        for date_str in dates:
            try:
                if len(date_str) != 6 or not date_str.isdigit():
                    continue
                    
                year = int(date_str[:4])
                month = int(date_str[4:6])
                
                if year < 1900 or year > 2100 or month < 1 or month > 12:
                    continue
                
                record = {
                    "Date": f"{year}-{month:02d}",
                    "Year": year,
                    "Month": month,
                    "Latitude": lat,
                    "Longitude": lon
                }
                
                # Mapeo de parámetros NASA POWER a nombres de columnas
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
                
                for nasa_param, col_name in param_mapping.items():
                    if nasa_param in parameters and date_str in parameters[nasa_param]["data"]:
                        value = parameters[nasa_param]["data"][date_str]
                        record[col_name] = value if value != -999.0 else np.nan
                    else:
                        record[col_name] = np.nan
                
                records.append(record)
                
            except (ValueError, IndexError):
                continue
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        return df
    
    def prepare_features(self, df):
        
        df = df.copy()
        
        # Crear características temporales
        df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
        df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
        
        # Crear características de temporada
        df['Season'] = df['Month'].map({
            12: 0, 1: 0, 2: 0,  # Invierno
            3: 1, 4: 1, 5: 1,   # Primavera
            6: 2, 7: 2, 8: 2,   # Verano
            9: 3, 10: 3, 11: 3  # Otoño
        })
        
        # Limpiar datos: eliminar filas con demasiados NaN
        df_clean = df.dropna(subset=self.target_parameters, thresh=len(self.target_parameters)//2)
        
        # Rellenar valores NaN restantes con medianas
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
        
        print(f"Datos preparados: {len(df_clean)} registros limpios")
        return df_clean
    
    def train_models(self, df):
        """Entrenar un modelo para cada parámetro climático"""
        print(f"Entrenando modelos para {len(self.target_parameters)} parámetros...")
        
        # Preparar características de entrada
        X = df[self.feature_columns]
        
        model_metrics = {}
        
        for param in self.target_parameters:
            if param not in df.columns:
                print(f"Parámetro {param} no encontrado en datos")
                continue
                
            try:
                # Preparar datos para este parámetro
                y = df[param]
                
                # Dividir datos
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, shuffle=True
                )
                
                # Entrenar modelo
                model = GradientBoostingRegressor(
                    n_estimators=50,  # Menos estimadores para velocidad
                    learning_rate=0.1,
                    max_depth=4,
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
                
                print(f"    {param}: R²={r2:.3f}, MAE={mae:.3f}")
                
            except Exception as e:
                print(f"    Error entrenando {param}: {e}")
                continue
        
        print(f" Modelos entrenados: {len(self.models)}/{len(self.target_parameters)}")
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
            
            # Datos de entrada para predicción
            prediction_features = pd.DataFrame([{
                'Year': year,
                'Month': month,
                'Latitude': lat,
                'Longitude': lon,
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
                "predictions": {
                    "precipitation_mm_per_day": round(predictions.get('Precipitation_mm_per_day', 0.0), 3),
                    "temperature_c": round(predictions.get('Temperature_C', 0.0), 2),
                    "temperature_max_c": round(predictions.get('Temperature_Max_C', 0.0), 2),
                    "temperature_min_c": round(predictions.get('Temperature_Min_C', 0.0), 2),
                    "humidity_percent": round(predictions.get('Humidity_Percent', 0.0), 1),
                    "wind_speed_ms": round(predictions.get('Wind_Speed_ms', 0.0), 2),
                    "pressure_kpa": round(predictions.get('Pressure_kPa', 0.0), 2),
                    "cloud_cover_percent": round(predictions.get('Cloud_Cover_Percent', 0.0), 1)
                }
            }
            
            print(f" Predicción completada exitosamente")
            return result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "date": target_date,
                "latitude": lat,
                "longitude": lon,
                "generated_at": datetime.now().isoformat()
            }
            return error_result
    
    def prepare_seasonal_features(self, df):
        """Crear múltiples características estacionales en lugar de una sola"""
        
        # Características cíclicas existentes
        df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
        df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
        
        # Características adicionales por ubicación
        for idx, row in df.iterrows():
            lat, lon, month = row['Latitude'], row['Longitude'], row['Month']
            
            # Característica de zona climática
            df.loc[idx, 'Climate_Zone'] = self._get_climate_zone(lat, lon)
            
            # Características solares
            solar_features = self.get_solar_season_features(month, lat)
            df.loc[idx, 'Daylight_Hours'] = solar_features['daylight_hours']
            df.loc[idx, 'Solar_Intensity'] = solar_features['solar_intensity']
            
            # Características de lluvia regional
            df.loc[idx, 'Rainy_Season'] = self._is_rainy_season(month, lat, lon)
            
            # Distancia al ecuador (afecta estacionalidad)
            df.loc[idx, 'Equatorial_Distance'] = abs(lat)
        
        return df

