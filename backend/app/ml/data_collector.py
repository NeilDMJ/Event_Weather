import pandas as pd
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.nasapower import get_climate_projection

locations = [
    (17.82703226502565, -97.80431094116672), #UTM
]

async def collect_data(locations):
    all_data = []

    for lat,lon in locations:
        try:
            data = await get_climate_projection(lat,lon,2020,2024)
            if "data" in data and data["data"]:
                # Crear lista vacía para los registros
                records_list = []
                data_dict = data["data"]  # Este es el diccionario con los datos
                
                for date_str, precipitation in data_dict.items():
                    year = int(date_str[:4])
                    month = int(date_str[4:6])

                    records_list.append({
                        "Date": date_str,
                        "Year": year,
                        "Month": month,
                        "Precipitation_mm_per_day": precipitation,
                        "Latitude": lat,
                        "Longitude": lon
                    })
                
                df_location = pd.DataFrame(records_list)
                all_data.append(df_location)
                print(f"Datos recolectados para lat: {lat}, lon: {lon}: {len(records_list)} registros")

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

