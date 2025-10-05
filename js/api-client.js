/**
 * Cliente para conectar con la API de predicción climática
 * URL base: Configurable para desarrollo/producción
 */

class WeatherAPIClient {
    constructor(baseURL = null) { 
        // Auto-detectar backend o usar modo demo
        this.baseURL = baseURL || this.detectBackendURL();
        this.isProduction = !this.baseURL.includes('localhost');
        console.log(`API configurada en: ${this.baseURL}`);
    }

    /**
     * Detectar automáticamente la URL del backend
     */
    detectBackendURL() {
        // Primero verificar si estamos en desarrollo local
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'http://localhost:8004';
        }
        
        // URLs conocidas del backend (actualizar según deployment real)
        const possibleBackends = [
            'https://servios.utm.mx/apiclima'
        ];
        
        // Por ahora retornar la primera opción (actualizar después de verificar cuál funciona)
        return possibleBackends[0];
    }

    /**
     * Realizar petición HTTP con manejo de errores
     */
    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            console.log(`Petición a: ${url}`);
            
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
            console.log('Respuesta recibida:', data);
            return data;
            
        } catch (error) {
            console.warn('Error en petición (usando datos mock):', error);
            // Retornar datos mock para development/demo
            return this.getMockData(endpoint);
        }
    }

    /**
     * Datos mock para cuando no hay backend disponible
     */
    getMockData(endpoint) {
        if (endpoint.includes('/predict')) {
            return {
                success: true,
                location: { latitude: 17.827, longitude: -97.8043 },
                prediction_date: "2025-12-25",
                predictions: {
                    temperature_c: 23.5,
                    temperature_max_c: 28.2,
                    temperature_min_c: 18.8,
                    precipitation_mm_per_day: 2.3,
                    humidity_percent: 65.5,
                    wind_speed_ms: 2.1,
                    pressure_kpa: 81.2,
                    cloud_cover_percent: 45.8
                },
                generated_at: new Date().toISOString(),
                note: "Datos de demostración - Backend no disponible"
            };
        }
        
        if (endpoint.includes('/climate')) {
            return {
                location: { lat: 17.827, lon: -97.8043 },
                projection: {
                    "2024-01": { precipitation: 45.2, temperature: 22.1 },
                    "2024-02": { precipitation: 38.7, temperature: 24.3 },
                    "2024-03": { precipitation: 52.1, temperature: 26.8 }
                },
                note: "Datos de demostración - Backend no disponible"
            };
        }

        return {
            message: "Event Weather API - Demo Mode",
            version: "2.0.0",
            status: "demo",
            note: "Backend no disponible - Mostrando datos de demostración"
        };
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
            const isDemo = info.status === 'demo' || info.note?.includes('demostración');
            
            return {
                status: isDemo ? 'demo' : 'online',
                message: isDemo ? 'Modo demostración activo' : info.message,
                version: info.version || '2.0.0',
                isDemo: isDemo
            };
        } catch (error) {
            return {
                status: 'demo',
                message: 'Modo demostración - Backend no disponible',
                version: '2.0.0-demo',
                isDemo: true,
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
            : status.status === 'demo'
            ? 'background: #FF9800; color: white;'
            : 'background: #f44336; color: white;'
        }
    `;
    
    const icon = status.status === 'online' ? '🟢' : 
                 status.status === 'demo' ? '🟡' : '🔴';
    
    const text = status.status === 'online' ? 'API Online' :
                 status.status === 'demo' ? 'Modo Demo' : 'API Offline';
    
    statusDiv.innerHTML = `${icon} ${text} - ${status.version}`;
    
    // Agregar tooltip en modo demo
    if (status.isDemo) {
        statusDiv.title = 'Usando datos de demostración. Backend no disponible.';
    }
    
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
