# Predecir clima usando modelos entrenados - versión funcional simplificada
import pandas as pd
import numpy as np
import joblib
import os
import glob
import re
import math
import asyncio
import sys
from datetime import datetime
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Agregar path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def calcular_distancia_geografica(lat1, lon1, lat2, lon2):
    """Calcular distancia entre dos puntos usando fórmula de Haversine (km)"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radio de la Tierra en km
    return c * r

def extraer_coordenadas_archivo(filename):
    """Extraer coordenadas del archivo de información del modelo"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        for line in content.split('\n'):
            if "Ubicación entrenamiento:" in line:
                coords_part = line.split("Ubicación entrenamiento:")[1].strip()
                lat_str, lon_str = coords_part.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
                return lat, lon
    except Exception as e:
        print(f"Error extrayendo coordenadas de {filename}: {e}")
    return None, None

def obtener_modelos_entrenados(models_dir="../models/trained"):
    """Obtener lista de modelos entrenados con sus coordenadas"""
    if not os.path.exists(models_dir):
        print(f"⚠️  Directorio de modelos no encontrado: {models_dir}")
        return []
    
    info_pattern = os.path.join(models_dir, "model_info_*.txt")
    info_files = glob.glob(info_pattern)
    modelos_disponibles = []
    
    for info_file in info_files:
        lat, lon = extraer_coordenadas_archivo(info_file)
        if lat is not None and lon is not None:
            filename = os.path.basename(info_file)
            parts = filename.replace("model_info_", "").replace(".txt", "").split("_")
            if len(parts) >= 2:
                timestamp = parts[-1]
                param = "_".join(parts[:-1])
                model_file = os.path.join(models_dir, f"model_{param}_{timestamp}.joblib")
                if os.path.exists(model_file):
                    modelos_disponibles.append({
                        'parameter': param,
                        'timestamp': timestamp,
                        'latitude': lat,
                        'longitude': lon,
                        'model_file': model_file,
                        'info_file': info_file
                    })
    
    print(f"📋 Modelos entrenados encontrados: {len(modelos_disponibles)}")
    return modelos_disponibles

def buscar_modelo_ideal(coordenadas, distancia_maxima=100):
    """Buscar modelo entrenado más cercano o determinar si necesita entrenar uno nuevo"""
    lat_objetivo, lon_objetivo = coordenadas
    print(f"🔍 Buscando modelo ideal para ({lat_objetivo}, {lon_objetivo})")
    
    modelos_disponibles = obtener_modelos_entrenados()
    if not modelos_disponibles:
        print("❌ No se encontraron modelos entrenados")
        return {'encontrado': False, 'necesita_entrenar': True, 'coordenadas_objetivo': coordenadas}
    
    # Agrupar modelos por ubicación
    modelos_por_ubicacion = {}
    for modelo in modelos_disponibles:
        key = f"{modelo['latitude']}_{modelo['longitude']}_{modelo['timestamp']}"
        if key not in modelos_por_ubicacion:
            modelos_por_ubicacion[key] = {
                'latitude': modelo['latitude'],
                'longitude': modelo['longitude'],
                'timestamp': modelo['timestamp'],
                'models': []
            }
        modelos_por_ubicacion[key]['models'].append(modelo)
    
    # Encontrar ubicación más cercana
    mejor_distancia = float('inf')
    mejor_ubicacion = None
    
    for key, ubicacion in modelos_por_ubicacion.items():
        distancia = calcular_distancia_geografica(
            lat_objetivo, lon_objetivo,
            ubicacion['latitude'], ubicacion['longitude']
        )
        print(f"  📍 Ubicación ({ubicacion['latitude']:.3f}, {ubicacion['longitude']:.3f}): {distancia:.2f} km")
        if distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor_ubicacion = ubicacion
    
    # Verificar si la distancia es aceptable
    if mejor_distancia <= distancia_maxima:
        print(f"✅ Modelo encontrado a {mejor_distancia:.2f} km")
        modelos_cargados = {}
        for modelo in mejor_ubicacion['models']:
            try:
                model_obj = joblib.load(modelo['model_file'])
                modelos_cargados[modelo['parameter']] = model_obj
                print(f"  ✓ Modelo cargado: {modelo['parameter']}")
            except Exception as e:
                print(f"  ✗ Error cargando {modelo['parameter']}: {e}")
        
        return {
            'encontrado': True,
            'distancia': mejor_distancia,
            'ubicacion_modelo': (mejor_ubicacion['latitude'], mejor_ubicacion['longitude']),
            'timestamp': mejor_ubicacion['timestamp'],
            'modelos': modelos_cargados,
            'necesita_entrenar': False
        }
    else:
        print(f"❌ Modelo más cercano a {mejor_distancia:.2f} km (excede límite de {distancia_maxima} km)")
        return {
            'encontrado': False,
            'distancia': mejor_distancia,
            'necesita_entrenar': True,
            'coordenadas_objetivo': coordenadas
        }

async def entrenar_modelo_nuevo(coordenadas):
    """Entrenar un nuevo modelo usando las funciones de model_trainer y data_collector"""
    from .data_collector import collect_data
    from .model_trainer import train_climate_models, save_models, FEATURE_COLUMNS, TARGET_PARAMETERS
    
    lat, lon = coordenadas
    print(f"🔄 Entrenando nuevo modelo para ({lat}, {lon})...")
    
    try:
        # Recolectar datos usando data_collector
        print("📊 Recolectando datos usando data_collector...")
        df = await collect_data(coordenadas)
        
        if df.empty:
            raise Exception("No se pudieron obtener datos históricos")
        
        print(f"✓ Datos recolectados: {len(df)} registros")
        
        # Preparar características usando la misma lógica que model_trainer
        print("🔧 Preparando características...")
        df_prepared = prepare_features_for_training(df, FEATURE_COLUMNS, TARGET_PARAMETERS)
        
        # Entrenar modelos usando model_trainer
        print("🤖 Entrenando modelos usando model_trainer...")
        modelos_entrenados, metrics = train_climate_models(df_prepared)
        
        if not modelos_entrenados:
            raise Exception("No se pudieron entrenar modelos válidos")
        
        # Guardar modelos usando model_trainer
        print("💾 Guardando modelos...")
        save_models(modelos_entrenados, coordenadas)
        
        print(f"✅ Nuevo modelo entrenado exitosamente para ({lat}, {lon})")
        return modelos_entrenados
        
    except Exception as e:
        print(f"❌ Error entrenando modelo: {e}")
        return {}

def prepare_features_for_training(df, feature_columns, target_parameters):
    """Preparar características para entrenamiento - compatible con model_trainer"""
    df = df.copy()
    
    # Crear características temporales cíclicas (sin Season)
    df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
    df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
    
    # Limpiar datos: eliminar filas con demasiados NaN
    df_clean = df.dropna(subset=target_parameters, thresh=len(target_parameters)//2)
    
    # Rellenar valores NaN en características de entrada
    for feature in feature_columns:
        if feature in df_clean.columns:
            if df_clean[feature].isna().any():
                if feature in ['Year', 'Month', 'Latitude', 'Longitude']:
                    df_clean[feature] = df_clean[feature].fillna(df_clean[feature].median())
                else:
                    df_clean[feature] = df_clean[feature].fillna(0.0)
    
    # Rellenar valores NaN en parámetros objetivo
    default_values = {
        'Precipitation_mm_per_day': 1.0, 'Temperature_C': 23.0,
        'Temperature_Max_C': 29.0, 'Temperature_Min_C': 17.0,
        'Humidity_Percent': 65.0, 'Wind_Speed_ms': 2.0,
        'Pressure_kPa': 80.0, 'Cloud_Cover_Percent': 50.0
    }
    
    for param in target_parameters:
        if param in df_clean.columns:
            median_value = df_clean[param].median()
            if pd.isna(median_value):
                median_value = default_values.get(param, 0.0)
            df_clean[param] = df_clean[param].fillna(median_value)
    
    # Verificar que no quedan NaN en características
    df_clean[feature_columns] = df_clean[feature_columns].fillna(0.0)
    
    print(f"✓ Datos preparados: {len(df_clean)} registros limpios de {len(df)} originales")
    return df_clean

async def obtener_o_entrenar_modelo(coordenadas, distancia_maxima=100):
    """Función principal: buscar modelo ideal o entrenar uno nuevo"""
    print("🌤️  SISTEMA DE MODELOS CLIMÁTICOS")
    print("=" * 40)
    
    resultado = buscar_modelo_ideal(coordenadas, distancia_maxima)
    
    if resultado['encontrado']:
        print(f"🎯 Usando modelo existente (distancia: {resultado['distancia']:.2f} km)")
        return resultado['modelos']
    elif resultado['necesita_entrenar']:
        print("🔨 Entrenando nuevo modelo...")
        models = await entrenar_modelo_nuevo(coordenadas)
        if models:
            print("✅ Nuevo modelo listo para usar")
            return models
        else:
            print("❌ No se pudo entrenar modelo")
            return {}
    else:
        print("❌ No se encontraron modelos y no se pudo entrenar uno nuevo")
        return {}

# Clase ClimatePredictor para compatibilidad
class ClimatePredictor:
    def __init__(self):
        pass
    
    async def predict_for_date(self, lat, lon, target_date):
        """Método de compatibilidad"""
        coordenadas = (lat, lon)
        modelos = await obtener_o_entrenar_modelo(coordenadas)
        
        if not modelos:
            return {
                "error": "No se pudieron obtener modelos para esta ubicación",
                "date": target_date,
                "latitude": lat,
                "longitude": lon
            }
        
        # Hacer predicción simple
        from datetime import datetime
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        year, month = target_dt.year, target_dt.month
        
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        
        features = pd.DataFrame([{
            'Year': year, 'Month': month, 'Latitude': lat, 'Longitude': lon,
            'Month_sin': month_sin, 'Month_cos': month_cos
        }])
        
        predictions = {}
        for param_name, model in modelos.items():
            try:
                pred_value = model.predict(features)[0]
                predictions[param_name] = float(pred_value)
            except:
                predictions[param_name] = 0.0
        
        return {
            "date": target_date,
            "latitude": lat,
            "longitude": lon,
            "predictions": predictions
        }