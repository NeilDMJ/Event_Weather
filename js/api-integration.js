/**
 * Integración con tu API backend - Sin APIs externas
 * Este archivo configura el cliente para usar únicamente tu backend
 */

// Configuración del backend - AUTO-DETECTA URL
const BACKEND_API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8004' 
    : 'https://servicios.utm.mx/apiclima'; // o tu URL de producción

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
function displayPredictionData(prediction) {
    if (!prediction || !prediction.predictions) {
        return null;
    }
    
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
    
    return prediction;
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

// Inicializar API al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    initWeatherAPI();
});