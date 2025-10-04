import pandas as pd
import numpy as np
import joblib
import os
import glob
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.nasapower import get_complete_climate_projection

class ClimatePredictor:
    def __init__(self, model_path=None):
        """
        Inicializa el predictor de clima
        
        Args:
            model_path (str, optional): Ruta específica al modelo. 
                                      Si no se proporciona, carga el más reciente.
        """
        self.model = None
        self.model_info = None
        self.feature_columns = None
        self.model_path = model_path
        
        # Cargar modelo automáticamente
        if model_path:
            self.load_model(model_path)
        else:
            self.load_latest_model()
    
    def load_latest_model(self):
        """Cargar el modelo más reciente del directorio models/trained/"""
        models_dir = "models/trained"
        
        if not os.path.exists(models_dir):
            raise FileNotFoundError(f"Directorio {models_dir} no encontrado. Entrena un modelo primero.")
        
        # Buscar archivos .joblib
        model_files = glob.glob(f"{models_dir}/*.joblib")
        
        if not model_files:
            raise FileNotFoundError(f"No se encontraron modelos en {models_dir}. Entrena un modelo primero.")
        
        # Obtener el más reciente por fecha de modificación
        latest_model = max(model_files, key=os.path.getctime)
        
        print(f"Cargando modelo más reciente: {os.path.basename(latest_model)}")
        self.load_model(latest_model)
        
        return latest_model
    
    def load_model(self, model_path):
        """
        Cargar un modelo específico
        
        Args:
            model_path (str): Ruta al archivo .joblib del modelo
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
        
        try:
            # Cargar modelo
            self.model = joblib.load(model_path)
            self.model_path = model_path
            
            # Intentar cargar información del modelo
            info_path = model_path.replace('.joblib', '.txt').replace('climate_model_', 'model_info_')
            
            if os.path.exists(info_path):
                with open(info_path, 'r') as f:
                    content = f.read()
                    # Extraer características de la información
                    if "Características:" in content:
                        features_line = [line for line in content.split('\n') if 'Características:' in line][0]
                        # Parsear la lista de características
                        features_str = features_line.split('Características: ')[1]
                        self.feature_columns = eval(features_str)  # Convierte string a lista
                
                print(f"Modelo cargado exitosamente")
                print(f"Características: {len(self.feature_columns) if self.feature_columns else 'No disponibles'}")
            else:
                print(f"Información del modelo no encontrada: {info_path}")
                
        except Exception as e:
            raise Exception(f"Error cargando modelo: {str(e)}")
    
    async def predict_precipitation(self, lat, lon, start_year=None, end_year=None):
        """
        Predecir precipitación para una ubicación específica
        
        Args:
            lat (float): Latitud
            lon (float): Longitud  
            start_year (int, optional): Año de inicio. Default: año actual
            end_year (int, optional): Año de fin. Default: año actual + 1
            
        Returns:
            dict: Predicciones con fechas y valores
        """
        if self.model is None:
            raise ValueError("No hay modelo cargado. Usa load_model() primero.")
        
        # Configurar años por defecto
        current_year = datetime.now().year
        if start_year is None:
            start_year = current_year
        if end_year is None:
            end_year = current_year + 1
        
        try:
            # 1. Obtener datos climáticos actuales de NASA POWER
            print(f"Obteniendo datos climáticos para ({lat}, {lon})...")
            climate_data = await get_complete_climate_projection(lat, lon, start_year, end_year)
            
            if "error" in climate_data:
                return {"error": f"Error obteniendo datos NASA: {climate_data['error']}"}
            
            # 2. Convertir datos a DataFrame
            df = self._parse_nasa_data(climate_data, lat, lon)
            
            if df.empty:
                return {"error": "No se pudieron obtener datos válidos de NASA POWER"}
            
            # 3. Preparar características igual que en entrenamiento
            df_features = self._prepare_prediction_features(df)
            
            # 4. Hacer predicciones
            predictions = self.model.predict(df_features[self.feature_columns])
            
            # 5. Formatear resultados
            results = []
            for i, (idx, row) in enumerate(df_features.iterrows()):
                results.append({
                    "date": row['Date'].strftime('%Y-%m') if pd.notnull(row['Date']) else f"{row['Year']}-{row['Month']:02d}",
                    "year": int(row['Year']),
                    "month": int(row['Month']),
                    "predicted_precipitation_mm_per_day": float(predictions[i]),
                    "latitude": lat,
                    "longitude": lon,
                    "input_features": {
                        "temperature_c": float(row['Temperature_C']) if pd.notnull(row['Temperature_C']) else None,
                        "humidity_percent": float(row['Humidity_Percent']) if pd.notnull(row['Humidity_Percent']) else None,
                        "wind_speed_ms": float(row['Wind_Speed_ms']) if pd.notnull(row['Wind_Speed_ms']) else None,
                        "cloud_cover_percent": float(row['Cloud_Cover_Percent']) if pd.notnull(row['Cloud_Cover_Percent']) else None
                    }
                })
            
            return {
                "predictions": results,
                "model_info": {
                    "model_path": os.path.basename(self.model_path),
                    "total_predictions": len(results),
                    "date_range": f"{start_year}-{end_year}"
                }
            }
            
        except Exception as e:
            return {"error": f"Error en predicción: {str(e)}"}
    
    def _parse_nasa_data(self, climate_data, lat, lon):
        """Convertir datos de NASA POWER a DataFrame"""
        parameters = climate_data.get("parameters", {})
        
        if not parameters or "PRECTOTCORR" not in parameters:
            return pd.DataFrame()
        
        # Obtener fechas de referencia
        dates = list(parameters["PRECTOTCORR"]["data"].keys())
        
        records = []
        for date_str in dates:
            try:
                # Validar formato de fecha (debe ser YYYYMM)
                if len(date_str) != 6 or not date_str.isdigit():
                    continue
                    
                year = int(date_str[:4])
                month = int(date_str[4:6])
                
                # Validar año y mes
                if year < 1900 or year > 2100 or month < 1 or month > 12:
                    continue
                
                record = {
                    "Date": f"{year}-{month:02d}",  # Mantener como string primero
                    "Year": year,
                    "Month": month,
                    "Latitude": lat,
                    "Longitude": lon
                }
                
                # Agregar parámetros climáticos
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
                        # Filtrar valores inválidos de NASA (-999.0)
                        record[col_name] = value if value != -999.0 else np.nan
                    else:
                        record[col_name] = np.nan
                
                records.append(record)
                
            except (ValueError, IndexError) as e:
                print(f"⚠️  Saltando fecha inválida: {date_str} - {str(e)}")
                continue
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Convertir Date a datetime después de crear el DataFrame
        try:
            df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m')
        except Exception as e:
            print(f"⚠️  Error convirtiendo fechas: {str(e)}")
            # Fallback: crear fechas manualmente
            df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))
        
        return df
    
    def _prepare_prediction_features(self, df):
        """Preparar características igual que en entrenamiento"""
        df = df.copy()
        
        # Ordenar por fecha
        df = df.sort_values(['Latitude', 'Longitude', 'Date']).reset_index(drop=True)
        
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
        
        # Crear características de lag (si hay suficientes datos)
        if len(df) > 1:
            df['Temp_lag1'] = df.groupby(['Latitude', 'Longitude'])['Temperature_C'].shift(1)
            df['Humidity_lag1'] = df.groupby(['Latitude', 'Longitude'])['Humidity_Percent'].shift(1)
            df['Precipitation_lag1'] = df.groupby(['Latitude', 'Longitude'])['Precipitation_mm_per_day'].shift(1)
            
            # Medias móviles
            df['Temp_ma3'] = df.groupby(['Latitude', 'Longitude'])['Temperature_C'].rolling(window=3, min_periods=1).mean().reset_index(level=[0,1], drop=True)
            df['Humidity_ma3'] = df.groupby(['Latitude', 'Longitude'])['Humidity_Percent'].rolling(window=3, min_periods=1).mean().reset_index(level=[0,1], drop=True)
        else:
            # Para predicción de un solo punto, usar valores actuales como lag
            df['Temp_lag1'] = df['Temperature_C']
            df['Humidity_lag1'] = df['Humidity_Percent'] 
            df['Precipitation_lag1'] = 0.0  # Valor por defecto
            df['Temp_ma3'] = df['Temperature_C']
            df['Humidity_ma3'] = df['Humidity_Percent']
        
        # Rango de temperatura
        df['Temp_Range'] = df['Temperature_Max_C'] - df['Temperature_Min_C']
        
        # Llenar valores NaN con valores por defecto razonables
        df = df.fillna({
            'Temp_lag1': df['Temperature_C'].mean() if not df['Temperature_C'].isna().all() else 20.0,
            'Humidity_lag1': df['Humidity_Percent'].mean() if not df['Humidity_Percent'].isna().all() else 60.0,
            'Precipitation_lag1': 0.0,
            'Temp_ma3': df['Temperature_C'].mean() if not df['Temperature_C'].isna().all() else 20.0,
            'Humidity_ma3': df['Humidity_Percent'].mean() if not df['Humidity_Percent'].isna().all() else 60.0,
            'Temp_Range': 10.0,
            'Temperature_C': 20.0,
            'Temperature_Max_C': 30.0,
            'Temperature_Min_C': 10.0,
            'Humidity_Percent': 60.0,
            'Wind_Speed_ms': 2.0,
            'Pressure_kPa': 80.0,
            'Cloud_Cover_Percent': 50.0
        })
        
        return df
    
    def predict_from_manual_data(self, data_dict):
        """
        Hacer predicción desde datos manuales
        
        Args:
            data_dict (dict): Diccionario con los datos requeridos
                Ejemplo: {
                    'Year': 2024, 'Month': 10, 'Latitude': 17.86, 'Longitude': -97.78,
                    'Temperature_C': 25.0, 'Humidity_Percent': 70.0, 'Wind_Speed_ms': 3.0,
                    'Cloud_Cover_Percent': 45.0, ...
                }
        
        Returns:
            float: Predicción de precipitación en mm/día
        """
        if self.model is None:
            raise ValueError("No hay modelo cargado.")
        
        # Crear DataFrame desde datos manuales
        df = pd.DataFrame([data_dict])
        
        # Agregar columna Date si no existe
        if 'Date' not in df.columns:
            df['Date'] = pd.to_datetime(f"{data_dict.get('Year', 2024)}-{data_dict.get('Month', 1):02d}", format='%Y-%m')
        
        # Preparar características
        df_features = self._prepare_prediction_features(df)
        
        # Asegurar que tiene todas las columnas necesarias
        for col in self.feature_columns:
            if col not in df_features.columns:
                df_features[col] = 0.0  # Valor por defecto
        
        # Hacer predicción
        prediction = self.model.predict(df_features[self.feature_columns])
        
        return float(prediction[0])
    
    def get_model_info(self):
        """Obtener información del modelo cargado"""
        if self.model is None:
            return {"error": "No hay modelo cargado"}
        
        return {
            "model_path": os.path.basename(self.model_path) if self.model_path else "Unknown",
            "model_type": type(self.model).__name__,
            "feature_count": len(self.feature_columns) if self.feature_columns else 0,
            "features": self.feature_columns
        }


# Script de ejemplo para probar el predictor
if __name__ == "__main__":
    import asyncio
    
    async def test_predictor():
        print("Probando Climate Predictor")
        print("=" * 40)
        
        try:
            # Inicializar predictor (carga modelo automáticamente)
            predictor = ClimatePredictor()
            
            # Mostrar información del modelo
            print("\nInformación del modelo:")
            model_info = predictor.get_model_info()
            print(f"   Tipo: {model_info.get('model_type', 'Unknown')}")
            print(f"   Características: {model_info.get('feature_count', 0)}")
            
            # Ejemplo 1: Predicción con datos de NASA POWER
            print("\nPredicción para Oaxaca (datos NASA POWER):")
            lat, lon = 17.866667, -97.783333
            
            result = await predictor.predict_precipitation(lat, lon, 2024, 2024)
            
            if "error" in result:
                print(f"   Error: {result['error']}")
            else:
                predictions = result["predictions"][:3]  # Primeras 3 predicciones
                for pred in predictions:
                    print(f"   {pred['date']}: {pred['predicted_precipitation_mm_per_day']:.3f} mm/día")
            
            # Ejemplo 2: Predicción con datos manuales
            print("\nPredicción con datos manuales:")
            manual_data = {
                'Year': 2024,
                'Month': 10,
                'Latitude': 17.866667,
                'Longitude': -97.783333,
                'Temperature_C': 25.0,
                'Temperature_Max_C': 32.0,
                'Temperature_Min_C': 18.0,
                'Humidity_Percent': 75.0,
                'Wind_Speed_ms': 2.5,
                'Pressure_kPa': 80.5,
                'Cloud_Cover_Percent': 60.0
            }
            
            manual_prediction = predictor.predict_from_manual_data(manual_data)
            print(f"   Predicción: {manual_prediction:.3f} mm/día")
            
            print("\nPruebas completadas!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Asegúrate de haber entrenado un modelo primero con: python app/ml/model_trainer.py")
    
    # Ejecutar prueba
    asyncio.run(test_predictor())