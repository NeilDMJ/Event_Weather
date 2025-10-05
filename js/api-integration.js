/**
 * Extensión del app.js original para integrar con tu API
 * Este archivo muestra cómo modificar tu frontend existente
 */

// Agregar después de las variables globales existentes
const BACKEND_API_URL = 'http://localhost:8000';
let weatherAPIClient = null;

// Inicializar cliente de la API
function initWeatherAPI() {
    weatherAPIClient = new WeatherAPIClient(BACKEND_API_URL);
    
    // Verificar estado de la API al cargar
    weatherAPIClient.healthCheck().then(status => {
        console.log('🔌 Estado de la API:', status);
        showAPIStatus();
    });
}

// Función para obtener predicción mejorada
async function getEnhancedPrediction(lat, lon, date) {
    if (!weatherAPIClient) {
        console.warn('Cliente de API no inicializado');
        return null;
    }
    
    try {
        const prediction = await weatherAPIClient.getPrediction(lat, lon, date);
        return prediction;
    } catch (error) {
        console.error('Error obteniendo predicción:', error);
        return null;
    }
}

// Función para mostrar datos de predicción en la UI
function displayPredictionData(prediction, weatherData) {
    if (!prediction || !prediction.predictions) {
        return weatherData; // Retornar datos originales si no hay predicción
    }
    
    // Crear datos mejorados combinando WeatherAPI + tu predicción ML
    const enhancedData = { ...weatherData };
    const pred = prediction.predictions;
    
    // Actualizar la tarjeta principal con datos de predicción ML
    if (pred.temperature_c) {
        const mainTemp = document.querySelector('.current-weather-card .temperature');
        if (mainTemp) {
            mainTemp.textContent = `${Math.round(pred.temperature_c)}°`;
            
            // Agregar indicador de ML
            let mlBadge = document.querySelector('.ml-prediction-badge');
            if (!mlBadge) {
                mlBadge = document.createElement('span');
                mlBadge.className = 'ml-prediction-badge';
                mlBadge.innerHTML = '🤖 ML';
                mlBadge.style.cssText = `
                    font-size: 10px;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
                    padding: 2px 6px;
                    border-radius: 10px;
                    margin-left: 8px;
                    vertical-align: top;
                `;
                mainTemp.appendChild(mlBadge);
            }
        }
    }
    
    // Actualizar detalles del clima
    const weatherDetails = document.querySelectorAll('.weather-details p');
    if (weatherDetails.length >= 4) {
        if (pred.humidity_percent) {
            weatherDetails[3].textContent = `Humedad: ${Math.round(pred.humidity_percent)}%`;
        }
        if (pred.wind_speed_ms) {
            const windKmh = pred.wind_speed_ms * 3.6; // Convertir m/s a km/h
            weatherDetails[1].textContent = `Viento: ${Math.round(windKmh)} km/h`;
        }
        if (pred.pressure_kpa) {
            const pressureMb = pred.pressure_kpa * 10; // Convertir kPa a mb aproximadamente
            weatherDetails[2].textContent = `Presión: ${Math.round(pressureMb)}mb`;
        }
    }
    
    // Mostrar información adicional de la predicción
    showPredictionDetails(prediction);
    
    return enhancedData;
}

// Mostrar detalles completos de la predicción
function showPredictionDetails(prediction) {
    // Remover panel anterior si existe
    const existingPanel = document.getElementById('prediction-details');
    if (existingPanel) {
        existingPanel.remove();
    }
    
    const detailsPanel = document.createElement('div');
    detailsPanel.id = 'prediction-details';
    detailsPanel.style.cssText = `
        position: fixed;
        top: 10px;
        left: 10px;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 15px;
        border-radius: 10px;
        font-size: 12px;
        z-index: 1000;
        max-width: 300px;
        line-height: 1.4;
    `;
    
    const pred = prediction.predictions;
    detailsPanel.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 10px; color: #4CAF50;">
            🤖 Predicción ML - ${prediction.prediction_date}
        </div>
        <div><strong>Ubicación:</strong> ${prediction.location.latitude}, ${prediction.location.longitude}</div>
        <div><strong>Temperatura:</strong> ${pred.temperature_c}°C</div>
        <div><strong>Máx/Mín:</strong> ${pred.temperature_max_c}°C / ${pred.temperature_min_c}°C</div>
        <div><strong>Precipitación:</strong> ${pred.precipitation_mm_per_day} mm/día</div>
        <div><strong>Viento:</strong> ${pred.wind_speed_ms} m/s</div>
        <div><strong>Humedad:</strong> ${pred.humidity_percent}%</div>
        <div><strong>Nubosidad:</strong> ${pred.cloud_cover_percent}%</div>
        <div style="margin-top: 10px; font-size: 10px; color: #ccc;">
            Generado: ${new Date(prediction.generated_at).toLocaleString()}
        </div>
        <button onclick="document.getElementById('prediction-details').remove()" 
                style="position: absolute; top: 5px; right: 8px; background: none; border: none; color: white; cursor: pointer;">✕</button>
    `;
    
    document.body.appendChild(detailsPanel);
    
    // Auto-ocultar después de 10 segundos
    setTimeout(() => {
        if (detailsPanel.parentNode) {
            detailsPanel.style.opacity = '0.7';
        }
    }, 10000);
}

// Modificar la función existente getWeatherForCity
async function getWeatherForCityEnhanced(cityOrCoords) {
    try {
        // 1. Obtener datos básicos de WeatherAPI (función original)
        const apiUrl = `https://api.weatherapi.com/v1/forecast.json?key=${API_KEY}&q=${cityOrCoords}&days=14&aqi=no&alerts=no&lang=es`;
        const response = await fetch(apiUrl);
        
        if (!response.ok) throw new Error('Ubicación no encontrada');
        
        const weatherData = await response.json();
        currentForecastData = weatherData;

        const { lat, lon, name, region } = weatherData.location;
        
        // 2. Intentar obtener predicción ML para la fecha seleccionada
        if (weatherAPIClient && dateInput.value) {
            const prediction = await getEnhancedPrediction(lat, lon, dateInput.value);
            
            if (prediction) {
                // 3. Combinar datos y mostrar
                const enhancedData = displayPredictionData(prediction, weatherData);
                currentForecastData = enhancedData;
            }
        }
        
        // 4. Actualizar mapa y UI
        initMap(lat, lon, `${name}, ${region}`);
        updateWeatherUI(currentForecastData, dateInput.value);

    } catch (error) {
        console.error('Error al buscar la ubicación:', error);
        alert('Ubicación no encontrada. Por favor, intenta con otro nombre.');
    }
}

// Ejemplo de cómo modificar el event listener del formulario de búsqueda
/*
searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const cityName = citySearchInput.value.trim();
    if (cityName) {
        getWeatherForCityEnhanced(cityName); // Usar función mejorada
        suggestionsContainer.style.display = 'none';
    }
});
*/

// Inicializar API al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    initWeatherAPI();
    // ... resto de tu código de inicialización
});