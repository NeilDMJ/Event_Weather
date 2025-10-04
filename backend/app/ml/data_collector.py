import pandas as pd
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.nasapower import get_complete_climate_projection

locations = [
    (17.82703226502565, -97.80431094116672), #UTM
    (17.866667, -97.783333), #Centro de Oaxaca
    (17.060816, -96.726588), #Puerto Escondido
    (16.8531, -99.8901),     #Huatulco
    (16.4333, -98.6000),     #Salina Cruz
    (16.5000, -97.5000),     #Ejemplo de ubicación
]

async def collect_data(locations):
    all_data = []

    for lat, lon in locations:
        try:
            data = await get_complete_climate_projection(lat, lon, 2020, 2024)
            if "parameters" in data and data["parameters"]:
                # Crear lista vacía para los registros
                records_list = []
                parameters = data["parameters"]
                
                # Obtener todas las fechas disponibles (usando PRECTOTCORR como referencia)
                if "PRECTOTCORR" in parameters and parameters["PRECTOTCORR"]["data"]:
                    dates = list(parameters["PRECTOTCORR"]["data"].keys())
                    
                    for date_str in dates:
                        year = int(date_str[:4])
                        month = int(date_str[4:6])
                        
                        # Crear un registro con todos los parámetros para esta fecha
                        record = {
                            "Date": date_str,
                            "Year": year,
                            "Month": month,
                            "Latitude": lat,
                            "Longitude": lon
                        }
                        
                        # Agregar cada parámetro climático
                        for param_name, param_data in parameters.items():
                            if date_str in param_data["data"]:
                                # Usar nombres más descriptivos para las columnas
                                column_name = {
                                    "PRECTOTCORR": "Precipitation_mm_per_day",
                                    "T2M": "Temperature_C",
                                    "T2M_MAX": "Temperature_Max_C",
                                    "T2M_MIN": "Temperature_Min_C",
                                    "RH2M": "Humidity_Percent",
                                    "WS2M": "Wind_Speed_ms",
                                    "PS": "Pressure_kPa",
                                    "CLOUD_AMT": "Cloud_Cover_Percent"
                                }.get(param_name, param_name)
                                
                                record[column_name] = param_data["data"][date_str]
                        
                        records_list.append(record)
                    
                    df_location = pd.DataFrame(records_list)
                    all_data.append(df_location)
                    print(f"Datos recolectados para lat: {lat}, lon: {lon}: {len(records_list)} registros con {len(parameters)} parámetros")
                else:
                    print(f"No se encontraron datos de precipitación para lat: {lat}, lon: {lon}")

        except Exception as e:
            print(f"Error al recolectar datos para lat: {lat}, lon: {lon} - {e}")

#combinar los datos
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()  # Retorna un DataFrame vacío si no hay datos
    
if __name__ == "__main__":
    print("Recoleccion de datos")
    data = asyncio.run(collect_data(locations))
    if not data.empty:
        print(f"Datos recolectados: {len(data)} registros")
        print(data.head())

        # Crear directorio data/raw si no existe
        os.makedirs("data/raw", exist_ok=True)
        
        # Guardar en la carpeta data/raw
        data.to_csv("data/raw/climate_data.csv", index=False)
        print("Datos guardados en data/raw/climate_data.csv")

