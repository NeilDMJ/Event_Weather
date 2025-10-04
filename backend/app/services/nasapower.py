# backend/app/services/nasa_power.py
import aiohttp

BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"

async def get_climate_projection(lat: float, lon: float, start: int, end: int):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "parameters": "PRECTOTCORR",  # Precipitación total mensual corregida (mm/day)
        "community": "RE",        # Renewable Energy
        "format": "JSON"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            if resp.status != 200:
                return {
                    "error": f"NASA POWER API devolvió {resp.status}",
                    "url": str(resp.url)  # útil para depuración
                }

            data = await resp.json()
            props = data.get("properties", {})
            parameters = props.get("parameter", {})
            
            # Intentar obtener PRECTOTCORR primero, luego PRECTOT como fallback
            prectot = parameters.get("PRECTOTCORR") or parameters.get("PRECTOT", {})
            
            # Filtrar valores -999.0 (datos no disponibles)
            filtered_data = {k: v for k, v in prectot.items() if v != -999.0}
            
            return {
                "data": filtered_data,
                "metadata": {
                    "units": "mm/day",
                    "parameter": "PRECTOTCORR" if "PRECTOTCORR" in parameters else "PRECTOT",
                    "description": "Precipitation Corrected" if "PRECTOTCORR" in parameters else "Total Precipitation",
                    "total_records": len(prectot),
                    "valid_records": len(filtered_data),
                    "data_source": data.get("header", {}).get("sources", [])
                }
            }

#http://127.0.0.1:8000/climate?lat=17.866667&lon=-97.783333&start=2020&end=2025
