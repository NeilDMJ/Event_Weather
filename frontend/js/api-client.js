/**
 * Cliente para conectar con la API de predicción climática
 * URL base: http://localhost:8000
 */

class WeatherAPIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    /**
     * Realizar petición HTTP con manejo de errores
     */
    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            console.log(` Petición a: ${url}`);
            
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(' Respuesta recibida:', data);
            return data;
            
        } catch (error) {
            console.error(' Error en petición:', error);
            throw error;
        }
    }

    /**
     * Obtener información de la API
     */
    async getAPIInfo() {
        return await this.request('/');
    }

    /**
     * Obtener predicción climática futura
     */
    async getPrediction(lat, lon, date) {
        const endpoint = `/predict?lat=${lat}&lon=${lon}&date=${date}`;
        return await this.request(endpoint);
    }

    /**
     * Obtener datos climáticos históricos
     */
    async getClimateData(lat, lon, startYear = 2020, endYear = 2025) {
        const endpoint = `/climate?lat=${lat}&lon=${lon}&start=${startYear}&end=${endYear}`;
        return await this.request(endpoint);
    }

    /**
     * Obtener datos climáticos completos
     */
    async getCompleteClimateData(lat, lon, startYear = 2020, endYear = 2030) {
        const endpoint = `/climate/complete?lat=${lat}&lon=${lon}&start=${startYear}&end=${endYear}`;
        return await this.request(endpoint);
    }

    /**
     * Obtener datos de temperatura
     */
    async getTemperatureData(lat, lon, startYear = 2020, endYear = 2030) {
        const endpoint = `/climate/temperature?lat=${lat}&lon=${lon}&start=${startYear}&end=${endYear}`;
        return await this.request(endpoint);
    }

    /**
     * Obtener datos atmosféricos
     */
    async getAtmosphericData(lat, lon, startYear = 2020, endYear = 2030) {
        const endpoint = `/climate/atmosferic?lat=${lat}&lon=${lon}&start=${startYear}&end=${endYear}`;
        return await this.request(endpoint);
    }

    /**
     * Obtener datos solares
     */
    async getSolarData(lat, lon, startYear = 2020, endYear = 2030) {
        const endpoint = `/climate/solar?lat=${lat}&lon=${lon}&start=${startYear}&end=${endYear}`;
        return await this.request(endpoint);
    }

    /**
     * Verificar si la API está funcionando
     */
    async healthCheck() {
        try {
            const info = await this.getAPIInfo();
            return {
                status: 'online',
                message: info.message,
                version: info.version
            };
        } catch (error) {
            return {
                status: 'offline',
                error: error.message
            };
        }
    }
}

// Crear instancia global del cliente
const weatherAPI = new WeatherAPIClient();

// Función helper para mostrar el estado de la API
async function showAPIStatus() {
    const status = await weatherAPI.healthCheck();
    
    const statusDiv = document.createElement('div');
    statusDiv.id = 'api-status';
    statusDiv.style.cssText = `
        position: fixed;
        bottom: 10px;
        right: 10px;
        padding: 10px 15px;
        border-radius: 20px;
        font-size: 12px;
        z-index: 1000;
        ${status.status === 'online' 
            ? 'background: #4CAF50; color: white;' 
            : 'background: #f44336; color: white;'
        }
    `;
    
    statusDiv.innerHTML = status.status === 'online' 
        ? `🟢 API Online - ${status.version}` 
        : `🔴 API Offline - ${status.error}`;
    
    // Remover status anterior si existe
    const existingStatus = document.getElementById('api-status');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    document.body.appendChild(statusDiv);
    
    // Auto-hide después de 5 segundos si está online
    if (status.status === 'online') {
        setTimeout(() => {
            statusDiv.style.opacity = '0.3';
        }, 5000);
    }
}

// Ejemplo de uso:
/*
// Verificar estado de la API
showAPIStatus();

// Obtener predicción
weatherAPI.getPrediction(17.8270, -97.8043, '2025-12-25')
    .then(prediction => {
        console.log('Predicción:', prediction);
    })
    .catch(error => {
        console.error('Error:', error);
    });

// Obtener datos históricos
weatherAPI.getClimateData(17.8270, -97.8043, 2020, 2025)
    .then(data => {
        console.log('Datos históricos:', data);
    });
*/