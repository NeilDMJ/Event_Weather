import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

class ClimateModelTrainer:
    def __init__(self, model):
        self.data = None
        self.models = {}
        self.best_model = None
        self.metrics = {}

    def load_data(self, filepath):
        self.data = pd.read_csv(filepath)
        self.data['Date'] = pd.to_datetime(self.data['Date'], format='%Y%m')
        self.data.sort_values(by='Date', inplace=True)
        self.data.reset_index(drop=True, inplace=True)

    def prepare_features(self,csv_path):
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m')
        df['Month'] = df['Date'].dt.month
        df['Year'] = df['Date'].dt.year
        df['DayOfYear'] = df['Date'].dt.dayofyear
        df['Lat_Lon'] = df['Latitude'].astype(str) + "_" + df['Longitude'].astype(str)
        self.data = df

    def split_data(self, test_size=0.2):
        X = self.data.drop(columns=['Date', 'Precipitation_mm_per_day'])
        y = self.data['Precipitation_mm_per_day']
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    def train_models(self,models_list):
        for model in models_list:
            model.fit(self.X_train, self.y_train)
            self.models[model.__class__.__name__] = model

    def evaluate_models(self):
        for name, model in self.models.items():
            y_pred = model.predict(self.X_test)
            mse = mean_squared_error(self.y_test, y_pred)
            mae = mean_absolute_error(self.y_test, y_pred)
            r2 = r2_score(self.y_test, y_pred)
            self.metrics[name] = {"MSE": mse, "MAE": mae, "R2": r2}

    def select_best_model(self):
        if not self.metrics:
            print("No models evaluated.")
            return None
        self.best_model = min(self.metrics, key=lambda k: self.metrics[k]["MSE"])
        print(f"Best model: {self.best_model} with MSE: {self.metrics[self.best_model]['MSE']}")
        return self.models[self.best_model]


    def predict(self, new_data):
        if not self.best_model:
            print("No best model selected.")
            return None
        # Asegurarse de que new_data tenga las mismas características que los datos de entrenamiento
        new_data = new_data.reindex(columns=self.X_train.columns, fill_value=0)
        return self.best_model.predict(new_data)