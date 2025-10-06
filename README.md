# Event_Weather
Event_Weather está construido sobre una arquitectura moderna y modular para garantizar su fiabilidad y escalabilidad.

**Fuentes de Datos:** Utiliza el conjunto de datos POWER (Prediction Of Worldwide Energy Resources) de la NASA como fuente principal, analizando variables clave como precipitación, temperatura, humedad, viento y nubosidad.

**Backend:** Un servidor de alto rendimiento desarrollado en FastAPI (Python) gestiona la obtención de datos, el procesamiento y la comunicación segura con la interfaz de usuario.

**Módulo de Machine Learning:** Implementa un patrón de "obtener o entrenar". Para cada nueva ubicación consultada, el sistema crea y almacena en caché un modelo predictivo específico, optimizando el rendimiento. Una técnica clave de ingeniería de características (feature engineering) es la codificación del mes con valores de seno y coseno, lo que permite al modelo comprender la estacionalidad de manera global sin sesgos hemisféricos.

**Capa de Inteligencia Artificial:** Un servicio dedicado de Gemini AI se encarga de transformar los datos numéricos brutos en información comprensible y útil, ofreciendo tres tipos de resultados:

**Descripción Narrativa:** Un pronóstico detallado y fácil de leer.

**Frontend:** Una interfaz de cliente ligera construida con JavaScript, HTML y CSS que consume la API para mostrar los resultados al usuario.

**Despliegue:** El proyecto está contenido en Docker, lo que asegura su portabilidad y facilita su despliegue a escala.

## Use of Artificial Intelligence (AI)
El proyecto utilizó una herramienta de Inteligencia Artificial para generar datos y texto descriptivo.
Herramienta de IA utilizada: Se empleó un servicio dedicado de Gemini AI.

**Ubicación en el proyecto:** La IA está integrada como una "Capa de IA" (AI Layer) dentro de la arquitectura del sistema. Su función es tomar los datos numéricos del pronóstico meteorológico (generados por el modelo de Machine Learning) y transformarlos en texto comprensible para el usuario.

**Funciones específicas y reconocimiento:** El texto descriptivo del proyecto reconoce explícitamente el uso de Gemini para generar los siguientes contenidos a través de puntos de acceso (API) específicos:

/predict/ai-description: Genera una narrativa detallada y legible del pronóstico, traduciendo los números brutos en una descripción clara.

/predict/event-planning: Genera consejos de planificación personalizados y adaptados al tipo de evento especificado por el usuario (boda, festival, etc.).

/predict/summary: Genera un resumen conciso de 2-3 frases sobre el pronóstico, ideal para alertas o actualizaciones rápidas.

## Sources 
#### Uso de la api de Nasa Power:  [Nasa Power](https://power.larc.nasa.gov/)

#### Pagina web del resultado del proyecto: [Web Page](https://savidevs-weather-app.vercel.app/)

