# Entrenar un modelo de ML Gradiente Boosting Regressor basado en los datos extraidos por data_collector.py
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Parámetros climáticos a predecir
TARGET_PARAMETERS = [
    'Precipitation_mm_per_day',
    'Temperature_C', 
    'Temperature_Max_C', 
    'Temperature_Min_C',
    'Humidity_Percent',
    'Wind_Speed_ms',
    'Pressure_kPa',
    'Cloud_Cover_Percent'
]

# Características de entrada (sin Season para evitar problemas con hemisferios)
FEATURE_COLUMNS = [
    'Year', 'Month', 'Latitude', 'Longitude', 
    'Month_sin', 'Month_cos'
]

def train_single_model(X, y, param_name):
    """Entrenar un modelo GradientBoostingRegressor para un parámetro específico"""
    try:
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        
        # Crear y entrenar modelo
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Evaluar modelo
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Métricas
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        
        metrics = {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'test_mae': test_mae,
            'test_rmse': test_rmse,
            'train_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        print(f"  ✓ {param_name}:")
        print(f"    - R² (entrenamiento): {train_r2:.3f}")
        print(f"    - R² (prueba): {test_r2:.3f}")
        print(f"    - MAE: {test_mae:.3f}")
        print(f"    - RMSE: {test_rmse:.3f}")
        
        return model, metrics
        
    except Exception as e:
        print(f"  Error entrenando {param_name}: {e}")
        return None

def train_climate_models(df):
    """Entrenar modelos para todos los parámetros climáticos"""
    print(f"🤖 Entrenando modelos para {len(TARGET_PARAMETERS)} parámetros...")
    
    # Preparar características de entrada
    X = df[FEATURE_COLUMNS]
    
    models = {}
    all_metrics = {}
    
    for param in TARGET_PARAMETERS:
        if param not in df.columns:
            print(f"  ⚠️  Parámetro {param} no encontrado en datos")
            continue
            
        # Verificar que hay suficientes datos
        y = df[param]
        if len(y) < 50:
            print(f"  ⚠️  {param}: Insuficientes datos ({len(y)} muestras)")
            continue
        
        # Entrenar modelo
        model, metrics = train_single_model(X, y, param)

        if model is not None:
            models[param] = model
            all_metrics[param] = metrics
    
    print(f"✅ Entrenamiento completado: {len(models)}/{len(TARGET_PARAMETERS)} modelos exitosos")
    return models, all_metrics


def save_models(models, location, models_dir="../models/trained"):
    """Guardar modelos entrenados con información de ubicación y timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lat, lon = location
    
    # Crear directorio de modelos si no existe
    os.makedirs(models_dir, exist_ok=True)
    
    saved_files = []
    
    for param_name, model in models.items():
        # Guardar modelo
        model_filename = f"{models_dir}/model_{param_name}_{timestamp}.joblib"
        joblib.dump(model, model_filename)
        saved_files.append(model_filename)
        
        # Guardar información del modelo
        info_filename = f"{models_dir}/model_info_{param_name}_{timestamp}.txt"
        with open(info_filename, 'w') as f:
            f.write(f"Modelo: {param_name}\n")
            f.write(f"Algoritmo: GradientBoostingRegressor\n")
            f.write(f"Ubicación entrenamiento: {lat}, {lon}\n")
            f.write(f"Fecha entrenamiento: {datetime.now().isoformat()}\n")
            f.write(f"Características: {FEATURE_COLUMNS}\n")
        
        saved_files.append(info_filename)
        print(f"✓ Modelo guardado: {param_name}")
    
    print(f"💾 Total archivos guardados: {len(saved_files)} en {models_dir}")
    return saved_files