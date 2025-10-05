"""
Servicio de Gemini AI para generar descripciones climáticas inteligentes
"""
import os
import google.generativeai as genai
from typing import Dict, Any, Optional
from datetime import datetime


class GeminiClimateService:
    """
    Servicio para generar análisis y descripciones climáticas usando Gemini AI
    """
    
    def __init__(self, api_key: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 512):
        """
        Inicializar el servicio de Gemini
        
        Args:
            api_key: API key de Google Gemini. Si no se provee, se busca en variables de entorno
            temperature: Temperatura de generación (creatividad) entre 0.0 y 1.0
            max_tokens: Máximo de tokens de salida
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "No se encontró API key de Gemini. "
                "Proporciona una API key o configura la variable de entorno GEMINI_API_KEY"
            )
        
        # Configurar Gemini
        genai.configure(api_key=self.api_key)
        
        # Configurar el modelo - usando gemini-2.5-flash (estable, rápido y eficiente)
        # Nota: Los modelos se especifican sin el prefijo "models/"
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Configuración de generación OPTIMIZADA para velocidad
        self.generation_config = {
            'temperature': temperature,  # Reducido para respuestas más directas
            'top_p': 0.8,  # Reducido de 0.95 para mayor velocidad
            'top_k': 20,   # Reducido de 40 para mayor velocidad
            'max_output_tokens': max_tokens,  # Reducido para respuestas más rápidas
        }
        
        # Configuración de seguridad - Más permisivo para datos climáticos técnicos
        # Los datos meteorológicos no representan riesgo, así que usamos BLOCK_ONLY_HIGH
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
        ]
    
    def _build_climate_prompt(self, prediction_data: Dict[str, Any]) -> str:
        """
        Construir el prompt OPTIMIZADO para Gemini basado en los datos de predicción
        
        Args:
            prediction_data: Diccionario con los datos de predicción climática
            
        Returns:
            str: Prompt formateado y optimizado para respuesta rápida
        """
        predictions = prediction_data.get('predictions', {})
        date = prediction_data.get('prediction_date', 'N/A')
        
        # Extraer valores de predicción
        temp = predictions.get('temperature_c', 0)
        temp_max = predictions.get('temperature_max_c', 0)
        temp_min = predictions.get('temperature_min_c', 0)
        humidity = predictions.get('humidity_percent', 0)
        precipitation = predictions.get('precipitation_mm_per_day', 0)
        wind_speed = predictions.get('wind_speed_ms', 0)
        cloud_cover = predictions.get('cloud_cover_percent', 0)
        
        # PROMPT OPTIMIZADO: Más conciso, instrucciones claras y directas
        prompt = f"""Analiza este pronóstico para {date}:
Temp: {temp_min}-{temp_max}°C (prom {temp}°C), Humedad: {humidity}%, Lluvia: {precipitation}mm, Viento: {wind_speed}m/s, Nubes: {cloud_cover}%

Responde EN ESPAÑOL con exactamente 4 secciones cortas:
1. RESUMEN (2 líneas): Clima general esperado
2. DETALLES (3 líneas): Temperatura, lluvia, viento
3. RECOMENDACIONES (3 puntos): Qué llevar/hacer
4. CONFORT (1 línea): Nivel (Excelente/Bueno/Regular/Malo)

Sé directo y conciso."""

        return prompt
    
    def _build_simple_prompt(self, prediction_data: Dict[str, Any]) -> str:
        """
        Construir un prompt ULTRA-SIMPLE y seguro (fallback si el optimizado es bloqueado)
        Sin formateo especial, sin caracteres especiales, máxima compatibilidad con filtros.
        """
        predictions = prediction_data.get('predictions', {})
        date = prediction_data.get('prediction_date', 'N/A')
        
        temp = predictions.get('temperature_c', 0)
        temp_max = predictions.get('temperature_max_c', 0)
        temp_min = predictions.get('temperature_min_c', 0)
        humidity = predictions.get('humidity_percent', 0)
        precipitation = predictions.get('precipitation_mm_per_day', 0)
        wind_speed = predictions.get('wind_speed_ms', 0)
        
        # Prompt extremadamente simple sin caracteres especiales
        return f"""Describe el clima para la fecha {date}.

Datos meteorologicos:
Temperatura minima {temp_min} grados, maxima {temp_max} grados, promedio {temp} grados.
Humedad relativa {humidity} por ciento.
Precipitacion {precipitation} milimetros.
Velocidad del viento {wind_speed} metros por segundo.

Resume el clima esperado en 4 lineas. Incluye recomendaciones practicas."""
    
    def _build_event_planning_prompt(
        self, 
        prediction_data: Dict[str, Any], 
        event_type: str
    ) -> str:
        """
        Construir prompt específico para planificación de eventos
        
        Args:
            prediction_data: Datos de predicción climática
            event_type: Tipo de evento (outdoor, sports, wedding, concert, etc.)
            
        Returns:
            str: Prompt especializado para planificación de eventos
        """
        location = prediction_data.get('location', {})
        lat = location.get('latitude', 'N/A')
        lon = location.get('longitude', 'N/A')
        date = prediction_data.get('prediction_date', 'N/A')
        predictions = prediction_data.get('predictions', {})
        
        temp = predictions.get('temperature_c', 0)
        temp_max = predictions.get('temperature_max_c', 0)
        temp_min = predictions.get('temperature_min_c', 0)
        humidity = predictions.get('humidity_percent', 0)
        precipitation = predictions.get('precipitation_mm_per_day', 0)
        wind_speed = predictions.get('wind_speed_ms', 0)
        cloud_cover = predictions.get('cloud_cover_percent', 0)
        
        prompt = f"""Eres un consultor experto en planificación de eventos. Analiza las condiciones climáticas predichas para un evento tipo "{event_type}".

**Ubicación del Evento:** Latitud {lat}, Longitud {lon}
**Fecha del Evento:** {date}
**Tipo de Evento:** {event_type}

**Pronóstico Climático:**
- Temperatura: {temp_min}°C - {temp_max}°C (promedio {temp}°C)
- Humedad: {humidity}%
- Precipitación: {precipitation} mm
- Viento: {wind_speed} m/s
- Nubes: {cloud_cover}%

Proporciona:

1. **Viabilidad del Evento** (1-2 líneas): ¿Es viable realizar este evento? (Excelente/Bueno/Regular/No recomendado)

2. **Riesgos Climáticos** (2-3 puntos): Principales desafíos o riesgos relacionados con el clima.

3. **Recomendaciones Específicas** (4-5 puntos): Sugerencias prácticas para el tipo de evento (equipamiento, horarios, alternativas).

4. **Plan B** (2-3 líneas): Sugerencias de contingencia si las condiciones empeoran.

Sé específico y práctico."""

        return prompt
    
    async def generate_climate_description(
        self, 
        prediction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generar descripción climática usando Gemini (OPTIMIZADO + ROBUSTO)
        
        Args:
            prediction_data: Datos de predicción del endpoint /predict
            
        Returns:
            Dict con la respuesta de Gemini y metadatos
        """
        try:
            # Construir el prompt optimizado
            prompt = self._build_climate_prompt(prediction_data)
            
            # Generar respuesta con configuración optimizada + safety settings
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # Verificar si la respuesta fue bloqueada
            if not response.candidates or len(response.candidates) == 0:
                raise ValueError("No se generó respuesta válida")
            
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            
            # finish_reason: 1=STOP (éxito), 2=SAFETY (bloqueado), 3=RECITATION, etc.
            if finish_reason == 2:  # SAFETY block
                # Intentar con prompt ultra-simple sin formateo
                simple_prompt = self._build_simple_prompt(prediction_data)
                response = self.model.generate_content(
                    simple_prompt,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                candidate = response.candidates[0] if response.candidates else None
                
                if not candidate or candidate.finish_reason != 1:
                    # Si falla de nuevo, generar descripción manual
                    return self._generate_fallback_description(prediction_data)
            
            # Extracción segura del texto
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                generated_text = candidate.content.parts[0].text
            elif hasattr(response, 'text'):
                generated_text = response.text
            else:
                # Fallback manual
                return self._generate_fallback_description(prediction_data)
            
            return {
                "success": True,
                "description": generated_text,
                "prediction_data": prediction_data,
                "generated_at": datetime.now().isoformat(),
                "model": "gemini-2.5-flash"
            }
            
        except Exception as e:
            # Si falla completamente, generar descripción manual
            return self._generate_fallback_description(prediction_data)
    
    async def generate_event_planning_advice(
        self,
        prediction_data: Dict[str, Any],
        event_type: str = "outdoor"
    ) -> Dict[str, Any]:
        """
        Generar consejos de planificación para eventos
        
        Args:
            prediction_data: Datos de predicción del endpoint /predict
            event_type: Tipo de evento a planificar
            
        Returns:
            Dict con la respuesta especializada de Gemini
        """
        try:
            # Construir el prompt específico para eventos
            prompt = self._build_event_planning_prompt(prediction_data, event_type)
            
            # Generar respuesta sin configuraciones problemáticas
            response = self.model.generate_content(prompt)
            
            # Verificar respuesta válida
            if response.candidates and response.candidates[0].finish_reason == 1:
                if hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts:
                    generated_text = response.candidates[0].content.parts[0].text
                else:
                    generated_text = response.text
            else:
                # Fallback: prompt simple
                simple_prompt = f"Dame consejos para un evento tipo {event_type} con temperatura {prediction_data.get('predictions', {}).get('temperature_c')}°C"
                response = self.model.generate_content(simple_prompt)
                generated_text = response.text
            
            return {
                "success": True,
                "event_type": event_type,
                "advice": generated_text,
                "prediction_data": prediction_data,
                "generated_at": datetime.now().isoformat(),
                "model": "gemini-2.5-flash"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "advice": "No se pudo generar el análisis para el evento.",
                "event_type": event_type,
                "prediction_data": prediction_data,
                "generated_at": datetime.now().isoformat()
            }
    
    async def generate_simple_summary(
        self,
        prediction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generar un resumen simple y conciso del clima
        
        Args:
            prediction_data: Datos de predicción del endpoint /predict
            
        Returns:
            Dict con un resumen corto y directo
        """
        try:
            predictions = prediction_data.get('predictions', {})
            date = prediction_data.get('prediction_date', 'N/A')
            
            temp = predictions.get('temperature_c', 0)
            temp_max = predictions.get('temperature_max_c', 0)
            temp_min = predictions.get('temperature_min_c', 0)
            precipitation = predictions.get('precipitation_mm_per_day', 0)
            cloud_cover = predictions.get('cloud_cover_percent', 0)
            
            prompt = f"""Resume el clima para {date}: Temperatura {temp_min}-{temp_max}°C, Lluvia {precipitation}mm, Nubes {cloud_cover}%. Responde en 2 líneas."""

            response = self.model.generate_content(prompt)
            
            # Manejo robusto de respuesta
            if response.candidates and response.candidates[0].finish_reason == 1:
                if hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts:
                    summary_text = response.candidates[0].content.parts[0].text
                else:
                    summary_text = response.text
            else:
                summary_text = response.text
            
            return {
                "success": True,
                "summary": summary_text,
                "date": date,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": "Resumen no disponible.",
                "generated_at": datetime.now().isoformat()
            }
    
    def _generate_fallback_description(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generar descripción manual cuando Gemini falla o bloquea la respuesta.
        Esta es la última opción de fallback para garantizar siempre una respuesta.
        
        Args:
            prediction_data: Datos de predicción
            
        Returns:
            Dict con descripción generada manualmente
        """
        predictions = prediction_data.get('predictions', {})
        date = prediction_data.get('prediction_date', 'N/A')
        
        temp = predictions.get('temperature_c', 0)
        temp_max = predictions.get('temperature_max_c', 0)
        temp_min = predictions.get('temperature_min_c', 0)
        humidity = predictions.get('humidity_percent', 0)
        precipitation = predictions.get('precipitation_mm_per_day', 0)
        wind_speed = predictions.get('wind_speed_ms', 0)
        cloud_cover = predictions.get('cloud_cover_percent', 0)
        
        # Generar descripción basada en reglas
        description_parts = []
        
        # 1. RESUMEN
        if precipitation > 5:
            weather_summary = f"Se espera un día lluvioso con {precipitation:.1f}mm de precipitación."
        elif cloud_cover > 70:
            weather_summary = f"Día mayormente nublado con {cloud_cover:.0f}% de cobertura de nubes."
        elif temp_max > 30:
            weather_summary = f"Día caluroso con temperaturas alcanzando los {temp_max:.1f}°C."
        elif temp_max < 15:
            weather_summary = f"Día fresco con temperaturas máximas de {temp_max:.1f}°C."
        else:
            weather_summary = f"Día con clima moderado y temperatura promedio de {temp:.1f}°C."
        
        description_parts.append(f"**RESUMEN DEL CLIMA**\n{weather_summary}")
        
        # 2. DETALLES
        details = f"""**CONDICIONES DETALLADAS**
La temperatura oscilará entre {temp_min:.1f}°C y {temp_max}°C, con un promedio de {temp:.1f}°C. """
        
        if precipitation > 1:
            details += f"Se esperan {precipitation:.1f}mm de lluvia. "
        else:
            details += "No se espera lluvia significativa. "
            
        if wind_speed > 5:
            details += f"Vientos moderados de {wind_speed:.1f} m/s."
        else:
            details += f"Vientos ligeros de {wind_speed:.1f} m/s."
        
        description_parts.append(details)
        
        # 3. RECOMENDACIONES
        recommendations = ["**RECOMENDACIONES PRÁCTICAS**"]
        
        if precipitation > 3:
            recommendations.append("- Llevar paraguas o impermeable")
            recommendations.append("- Considerar actividades bajo techo")
        
        if temp_max > 28:
            recommendations.append("- Usar ropa ligera y protector solar")
            recommendations.append("- Mantenerse hidratado")
        elif temp_max < 18:
            recommendations.append("- Llevar una chaqueta o abrigo")
        
        if wind_speed > 7:
            recommendations.append("- Tener precaución con objetos ligeros en exteriores")
        
        if humidity > 80:
            recommendations.append("- El ambiente se sentirá húmedo y pesado")
        
        if len(recommendations) == 1:  # Solo el título
            recommendations.append("- Condiciones generalmente favorables")
            recommendations.append("- Vestimenta casual apropiada")
        
        description_parts.append("\n".join(recommendations))
        
        # 4. NIVEL DE CONFORT
        comfort_score = 0
        if 20 <= temp <= 26:
            comfort_score += 2
        if precipitation < 2:
            comfort_score += 2
        if wind_speed < 5:
            comfort_score += 1
        if 40 <= humidity <= 70:
            comfort_score += 1
        
        if comfort_score >= 5:
            comfort = "**NIVEL DE CONFORT**: Excelente - Condiciones ideales para actividades al aire libre."
        elif comfort_score >= 3:
            comfort = "**NIVEL DE CONFORT**: Bueno - Condiciones favorables con precauciones menores."
        elif comfort_score >= 2:
            comfort = "**NIVEL DE CONFORT**: Regular - Condiciones aceptables pero con algunas molestias."
        else:
            comfort = "**NIVEL DE CONFORT**: Malo - Condiciones adversas, planificar con cuidado."
        
        description_parts.append(comfort)
        
        # Unir todas las partes
        full_description = "\n\n".join(description_parts)
        
        return {
            "success": True,
            "description": full_description,
            "prediction_data": prediction_data,
            "generated_at": datetime.now().isoformat(),
            "model": "fallback-rules-based",
            "note": "Descripción generada mediante reglas (Gemini no disponible)"
        }


# Instancia global del servicio (se inicializa bajo demanda)
_gemini_service: Optional[GeminiClimateService] = None


def get_gemini_service() -> GeminiClimateService:
    """
    Obtener instancia singleton del servicio de Gemini
    
    Returns:
        GeminiClimateService: Instancia del servicio
    """
    global _gemini_service
    
    if _gemini_service is None:
        _gemini_service = GeminiClimateService()
    
    return _gemini_service
