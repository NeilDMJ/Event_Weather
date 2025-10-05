import pandas as pd
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.nasapower import get_complete_climate_projection

async def collect_data(location,year):
    all_data = []

    lat, lon = location
    try:
        data = await get_complete_climate_projection(lat, lon, year-5, year)
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
    

#guardar los datos en un archivo csv backend/app/ml/data/raw/climate_dataa + "location".csv
def guardar_datos_csv(df):
    filename = f"backend/app/ml/data/raw/climate_data_{df.latitude.iloc[0]}_{df.longitude.iloc[0]}.csv"
    df.to_csv(filename, index=False)

    print(f"Datos guardados en {filename}")