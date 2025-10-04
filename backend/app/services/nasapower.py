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

async def get_complete_climate_projection(lat: float, lon: float, start: int, end: int):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "parameters": "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M,WS2M,PS,CLOUD_AMT",  # Varios parámetros
        "community": "RE",        # Renewable Energy
        "format": "JSON"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            if resp.status != 200:
                return {
                    "error": f"NASA POWER API devolvió {resp.status}",
                    "url": str(resp.url)
                }

            data = await resp.json()
            props = data.get("properties", {})
            parameters = props.get("parameter", {})
            
            # Extraer y filtrar cada parámetro
            result = {}
            param_info = {
                "PRECTOTCORR": {"units": "mm/day", "description": "Precipitación Corregida"},
                "T2M": {"units": "°C", "description": "Temperatura a 2 metros"},
                "T2M_MAX": {"units": "°C", "description": "Temperatura Máxima a 2 metros"},
                "T2M_MIN": {"units": "°C", "description": "Temperatura Mínima a 2 metros"},
                "RH2M": {"units": "%", "description": "Humedad Relativa a 2 metros"},
                "WS2M": {"units": "m/s", "description": "Velocidad del Viento a 2 metros"},
                "PS": {"units": "kPa", "description": "Presión Superficial"},
                "CLOUD_AMT": {"units": "%", "description": "Nubosidad"}
            }
            
            for param, info in param_info.items():
                raw_data = parameters.get(param, {})
                filtered = {k: v for k, v in raw_data.items() if v != -999.0}
                result[param] = {
                    "data": filtered,
                    "units": info["units"],
                    "description": info["description"],
                    "valid_records": len(filtered)
                }
            
            return {
                "parameters": result,
                "metadata": {
                    "data_source": data.get("header", {}).get("sources", []),
                    "total_parameters": len(result)
                }
            }
        
async def get_temperature_projection(lat: float, lon: float, start: int, end: int):
    params  = {
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "parameters": "T2M,T2M_MAX,T2M_MIN",  # Parámetros de temperatura
        "community": "RE",        # Renewable Energy
        "format": "JSON"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            if resp.status != 200:
                return{
                    "error": f"NASA POWER API devolvió {resp.status}",
                    "url": str(resp.url)
                }
            data = await resp.json()
            props = data.get("properties", {})
            parameters = props.get("parameter", {})

            result ={}
            term_params = {
                "T2M": {"units": "°C", "description": "Temperatura a 2 metros"},
                "T2M_MAX": {"units": "°C", "description": "Temperatura Máxima a 2 metros"},
                "T2M_MIN": {"units": "°C", "description": "Temperatura Mínima a 2 metros"}
            }

            for param, info in term_params.items():
                raw_data = parameters.get(param, {})
                filtered = {k: v for k, v in raw_data.items() if v != -999.0}
                result[param] = {
                    "data": filtered,
                    "units": info["units"],
                    "description": info["description"],
                    "valid_records": len(filtered)
                }
            return {
                "parameters": result,
                "metadata": {
                    "data_source": data.get("header", {}).get("sources", []),
                    "total_parameters": len(result)
                }
            }

async def get_atmospheric_projection(lat: float, lon: float, start: int, end: int):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "parameters": "RH2M,WS2M,WS10M,WS50M,WD2M,WD10M,WD50M,PS",
        "community": "RE",
        "format": "JSON"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            if resp.status != 200:
                return {
                    "error": f"NASA POWER API devolvió {resp.status}",
                    "url": str(resp.url)
                }

            data = await resp.json()
            props = data.get("properties", {})
            parameters = props.get("parameter", {})
            
            result = {}
            atm_params = {
                "RH2M": {"units": "%", "description": "Humedad Relativa a 2 metros"},
                "WS2M": {"units": "m/s", "description": "Velocidad del Viento a 2 metros"},
                "WS10M": {"units": "m/s", "description": "Velocidad del Viento a 10 metros"},
                "WS50M": {"units": "m/s", "description": "Velocidad del Viento a 50 metros"},
                "WD2M": {"units": "grados", "description": "Dirección del Viento a 2 metros"},
                "WD10M": {"units": "grados", "description": "Dirección del Viento a 10 metros"},
                "WD50M": {"units": "grados", "description": "Dirección del Viento a 50 metros"},
                "PS": {"units": "kPa", "description": "Presión Superficial"}
            }
            
            for param, info in atm_params.items():
                raw_data = parameters.get(param, {})
                filtered = {k: v for k, v in raw_data.items() if v != -999.0}
                result[param] = {
                    "data": filtered,
                    "units": info["units"],
                    "description": info["description"],
                    "valid_records": len(filtered)
                }
            
            return {
                "atmospheric": result,
                "metadata": {
                    "data_source": data.get("header", {}).get("sources", [])
                }
            }

async def get_solar_projection(lat: float, lon: float, start: int, end: int):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "parameters": "ALLSKY_SFC_SW_DWN,ALLSKY_SFC_LW_DWN,CLOUD_AMT",
        "community": "RE",
        "format": "JSON"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            if resp.status != 200:
                return {
                    "error": f"NASA POWER API devolvió {resp.status}",
                    "url": str(resp.url)
                }

            data = await resp.json()
            props = data.get("properties", {})
            parameters = props.get("parameter", {})
            
            result = {}

            solar_params ={
                "ALLSKY_SFC_SW_DWN": {
                    "units": "kW-hr/m^2/day", 
                    "description": "Irradiancia de Onda Corta Descendente"
                },
                "ALLSKY_SFC_LW_DWN": {
                    "units": "kW-hr/m^2/day", 
                    "description": "Irradiancia de Onda Larga Descendente"
                },
                "CLOUD_AMT": {
                    "units": "%", 
                    "description": "Nubosidad"
                }
            }
            
            for param, info in solar_params.items():
                raw_data = parameters.get(param, {})
                filtered = {k: v for k, v in raw_data.items() if v != -999.0}
                result[param] = {
                    "data": filtered,
                    "units": info["units"],
                    "description": info["description"],
                    "valid_records": len(filtered)
                }
            
            return {
                "solar": result,
                "metadata": {
                    "data_source": data.get("header", {}).get("sources", [])
                }
            }
        
#http://127.0.0.1:8000/climate?lat=17.866667&lon=-97.783333&start=2020&end=2025
