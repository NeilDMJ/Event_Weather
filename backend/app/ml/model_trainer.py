import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
from datetime import datetime

class ClimateModelTrainer:
    def __init__(self):
        self.data = None
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.metrics = {}
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_columns = None

    def load_data(self, filepath):
        """Cargar datos desde CSV"""
        print(f"Cargando datos desde: {filepath}")
        self.data = pd.read_csv(filepath)
        print(f"Datos cargados: {len(self.data)} registros, {len(self.data.columns)} columnas")
        print(f"Columnas disponibles: {list(self.data.columns)}")
        return self.data

    def prepare_features(self):
        """Preparar características para el modelo"""
        if self.data is None:
            raise ValueError("Primero debes cargar los datos con load_data()")
        
        df = self.data.copy()
        
        # Convertir Date a datetime si no está ya convertido
        if df['Date'].dtype == 'object':
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m')
        
        # Crear características temporales adicionales
        df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
        df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
        
        # Crear características de temporada
        df['Season'] = df['Month'].map({
            12: 0, 1: 0, 2: 0,  # Invierno
            3: 1, 4: 1, 5: 1,   # Primavera
            6: 2, 7: 2, 8: 2,   # Verano
            9: 3, 10: 3, 11: 3  # Otoño
        })
        
        # Crear características de lag (valores previos)
        df = df.sort_values(['Latitude', 'Longitude', 'Date'])
        df['Temp_lag1'] = df.groupby(['Latitude', 'Longitude'])['Temperature_C'].shift(1)
        df['Humidity_lag1'] = df.groupby(['Latitude', 'Longitude'])['Humidity_Percent'].shift(1)
        df['Precipitation_lag1'] = df.groupby(['Latitude', 'Longitude'])['Precipitation_mm_per_day'].shift(1)
        
        # Crear medias móviles
        df['Temp_ma3'] = df.groupby(['Latitude', 'Longitude'])['Temperature_C'].rolling(window=3, min_periods=1).mean().reset_index(level=[0,1], drop=True)
        df['Humidity_ma3'] = df.groupby(['Latitude', 'Longitude'])['Humidity_Percent'].rolling(window=3, min_periods=1).mean().reset_index(level=[0,1], drop=True)
        
        # Crear características de rango de temperatura
        df['Temp_Range'] = df['Temperature_Max_C'] - df['Temperature_Min_C']
        
        # Eliminar filas con valores NaN (principalmente del lag)
        df = df.dropna()
        
        self.data = df
        print(f"Características preparadas: {len(df)} registros después de limpieza")
        print(f"Nuevas columnas creadas: {[col for col in df.columns if col not in ['Date', 'Year', 'Month', 'Latitude', 'Longitude', 'Precipitation_mm_per_day', 'Temperature_C', 'Temperature_Max_C', 'Temperature_Min_C', 'Humidity_Percent', 'Wind_Speed_ms', 'Pressure_kPa', 'Cloud_Cover_Percent']]}")
        
        return df

    def split_data(self, test_size=0.2, temporal_split=True):
        """Dividir datos en entrenamiento y prueba"""
        if self.data is None:
            raise ValueError("Primero debes preparar las características con prepare_features()")
        
        # Definir características (excluir variables no predictoras)
        exclude_cols = ['Date', 'Precipitation_mm_per_day']
        self.feature_columns = [col for col in self.data.columns if col not in exclude_cols]
        
        X = self.data[self.feature_columns]
        y = self.data['Precipitation_mm_per_day']
        
        if temporal_split:
            # División temporal (más realista para series de tiempo)
            sort_data = self.data.sort_values('Date')
            split_idx = int(len(sort_data) * (1 - test_size))
            
            self.X_train = X.iloc[:split_idx]
            self.X_test = X.iloc[split_idx:]
            self.y_train = y.iloc[:split_idx]
            self.y_test = y.iloc[split_idx:]
            
            print(f"División temporal: {len(self.X_train)} entrenamiento, {len(self.X_test)} prueba")
        else:
            # División aleatoria
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            print(f"División aleatoria: {len(self.X_train)} entrenamiento, {len(self.X_test)} prueba")
        
        return self.X_train, self.X_test, self.y_train, self.y_test

    def train_models(self, custom_models=None):
        """Entrenar múltiples modelos"""
        if self.X_train is None:
            raise ValueError("Primero debes dividir los datos con split_data()")
        
        if custom_models is None:
            # Modelos por defecto con hiperparámetros optimizados
            models = {
                'RandomForest': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                ),
                'GradientBoosting': GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                ),
                'LinearRegression': LinearRegression()
            }
        else:
            models = custom_models
        
        print("Entrenando modelos...")
        for name, model in models.items():
            print(f"Entrenando {name}...")
            model.fit(self.X_train, self.y_train)
            self.models[name] = model
            print(f"✓ {name} entrenado")
        
        print(f"Se entrenaron {len(self.models)} modelos")
        return self.models

    def evaluate_models(self):
        """Evaluar todos los modelos entrenados"""
        if not self.models:
            raise ValueError("Primero debes entrenar modelos con train_models()")
        
        print("\nEvaluando modelos...")
        print("-" * 60)
        
        for name, model in self.models.items():
            # Predicciones
            y_pred_train = model.predict(self.X_train)
            y_pred_test = model.predict(self.X_test)
            
            # Métricas en entrenamiento
            train_mse = mean_squared_error(self.y_train, y_pred_train)
            train_mae = mean_absolute_error(self.y_train, y_pred_train)
            train_r2 = r2_score(self.y_train, y_pred_train)
            
            # Métricas en prueba
            test_mse = mean_squared_error(self.y_test, y_pred_test)
            test_mae = mean_absolute_error(self.y_test, y_pred_test)
            test_r2 = r2_score(self.y_test, y_pred_test)
            
            self.metrics[name] = {
                "train_MSE": train_mse,
                "train_MAE": train_mae,
                "train_R2": train_r2,
                "test_MSE": test_mse,
                "test_MAE": test_mae,
                "test_R2": test_r2
            }
            
            print(f"{name}:")
            print(f"  Entrenamiento - MSE: {train_mse:.4f}, MAE: {train_mae:.4f}, R²: {train_r2:.4f}")
            print(f"  Prueba        - MSE: {test_mse:.4f}, MAE: {test_mae:.4f}, R²: {test_r2:.4f}")
            print()
        
        return self.metrics

    def select_best_model(self, metric='test_R2', higher_better=True):
        """Seleccionar el mejor modelo basado en una métrica"""
        if not self.metrics:
            raise ValueError("Primero debes evaluar modelos con evaluate_models()")
        
        if higher_better:
            best_score = max(self.metrics.values(), key=lambda x: x[metric])[metric]
            self.best_model_name = [name for name, metrics in self.metrics.items() 
                                  if metrics[metric] == best_score][0]
        else:
            best_score = min(self.metrics.values(), key=lambda x: x[metric])[metric]
            self.best_model_name = [name for name, metrics in self.metrics.items() 
                                  if metrics[metric] == best_score][0]
        
        self.best_model = self.models[self.best_model_name]
        
        print(f"Mejor modelo: {self.best_model_name}")
        print(f"Métrica {metric}: {best_score:.4f}")
        
        return self.best_model

    def save_model(self, model_dir="models/trained"):
        """Guardar el mejor modelo"""
        if self.best_model is None:
            raise ValueError("Primero debes seleccionar el mejor modelo con select_best_model()")
        
        os.makedirs(model_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar modelo
        model_path = f"{model_dir}/climate_model_{self.best_model_name}_{timestamp}.joblib"
        joblib.dump(self.best_model, model_path)
        
        # Guardar información del modelo
        info_path = f"{model_dir}/model_info_{self.best_model_name}_{timestamp}.txt"
        with open(info_path, 'w') as f:
            f.write(f"Modelo: {self.best_model_name}\n")
            f.write(f"Fecha entrenamiento: {datetime.now()}\n")
            f.write(f"Características: {self.feature_columns}\n")
            f.write(f"Métricas: {self.metrics[self.best_model_name]}\n")
        
        print(f"Modelo guardado en: {model_path}")
        print(f"Información guardada en: {info_path}")
        
        return model_path

    def predict(self, new_data):
        """Hacer predicciones con el mejor modelo"""
        if self.best_model is None:
            raise ValueError("Primero debes seleccionar el mejor modelo con select_best_model()")
        
        # Asegurar que new_data tenga las mismas características
        if isinstance(new_data, pd.DataFrame):
            new_data = new_data.reindex(columns=self.feature_columns, fill_value=0)
        
        predictions = self.best_model.predict(new_data)
        return predictions

    def get_feature_importance(self):
        """Obtener importancia de características (si el modelo la soporta)"""
        if self.best_model is None:
            raise ValueError("Primero debes seleccionar el mejor modelo")
        
        if hasattr(self.best_model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.best_model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("Top 10 características más importantes:")
            print(importance_df.head(10))
            return importance_df
        else:
            print(f"El modelo {self.best_model_name} no soporta importancia de características")
            return None


# Script de entrenamiento automático
if __name__ == "__main__":
    print("Entrenamiento Automático de Modelos de Predicción Climática")
    print("=" * 65)
    
    try:
        # Inicializar el entrenador
        trainer = ClimateModelTrainer()
        
        # 1. Verificar y cargar datos
        data_path = "data/raw/climate_data.csv"
        if not os.path.exists(data_path):
            print(f" Error: No se encontró el archivo {data_path}")
            print(" Ejecuta primero: python app/ml/data_collector.py")
            exit(1)
        
        print(f"Cargando datos desde: {data_path}")
        trainer.load_data(data_path)
        
        # 2. Preparar características
        print("\nPreparando características...")
        trainer.prepare_features()
        
        # 3. Dividir datos (división temporal para series de tiempo)
        print("\nDividiendo datos...")
        trainer.split_data(test_size=0.2, temporal_split=True)
        
        # 4. Entrenar modelos
        print("\nEntrenando modelos...")
        trainer.train_models()
        
        # 5. Evaluar modelos
        print("\nEvaluando modelos...")
        trainer.evaluate_models()
        
        # 6. Seleccionar mejor modelo
        print("\nSeleccionando mejor modelo...")
        best_model = trainer.select_best_model(metric='test_R2', higher_better=True)
        
        # 7. Mostrar importancia de características
        print("\nImportancia de características:")
        trainer.get_feature_importance()
        
        # 8. Guardar modelo
        print("\nGuardando modelo...")
        model_path = trainer.save_model()
        
        # 9. Resumen final
        print("\n" + "=" * 65)
        print("ENTRENAMIENTO COMPLETADO EXITOSAMENTE!")
        print("=" * 65)
        print(f"Modelo guardado en: {model_path}")
        print(f"Mejor modelo: {trainer.best_model_name}")
        print(f"R² en prueba: {trainer.metrics[trainer.best_model_name]['test_R2']:.4f}")
        print(f"MAE en prueba: {trainer.metrics[trainer.best_model_name]['test_MAE']:.4f}")
        
        # 10. Ejemplo de predicción
        print("\nEjemplo de predicciones:")
        sample_data = trainer.X_test.head(3)
        predictions = trainer.predict(sample_data)
        actual_values = trainer.y_test.head(3).values
        
        print("-" * 50)
        for i, (pred, actual) in enumerate(zip(predictions, actual_values)):
            error = abs(pred - actual)
            print(f"Muestra {i+1}: Pred={pred:.3f}, Real={actual:.3f}, Error={error:.3f}")
        print("-" * 50)
        
        print("\nEl modelo está listo para ser usado en predicciones!")
        
    except Exception as e:
        print(f"\nError durante el entrenamiento: {str(e)}")
        print("Verifica que:")
        print("   - Los datos estén disponibles en data/raw/climate_data.csv")
        print("   - Las dependencias estén instaladas (pandas, scikit-learn, joblib)")
        print("   - Tengas permisos de escritura en el directorio models/")
        exit(1)