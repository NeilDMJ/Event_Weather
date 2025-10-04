# backend/app/services/nasa_power.py
import aiohttp

BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"

async def get_climate_projection(lat: float, lon: float, start: int, end: int):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "community": "RE",
        "parameters": "PRECTOT",  # Total precipitation (mm/month)
        "format": "JSON"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            if resp.status != 200:
                return {"error": f"NASA POWER API devolvió status {resp.status}"}
            data = await resp.json()
            # Extraer solo los datos relevantes
            parameter = data.get("properties", {}).get("parameter", {})
            return parameter.get("PRECTOT", {})
