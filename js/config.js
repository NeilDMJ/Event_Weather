/**
 * Configuración global para Event Weather
 * Solo Backend - Sin APIs externas
 */

// Configuración de la aplicación
window.EventWeatherConfig = {
    // URL del backend - auto-detecta entorno
    BACKEND_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8004' 
        : 'https://event-weather-backend.vercel.app',
    
    // Configuración de la app
    APP_NAME: 'Event Weather',
    VERSION: '2.0.0',
    
    // Ubicaciones predefinidas para búsquedas sin API externa
    PREDEFINED_LOCATIONS: {
        'oaxaca': { lat: 17.0654, lon: -96.7236, name: 'Oaxaca', region: 'Oaxaca', country: 'México' },
        'cdmx': { lat: 19.4326, lon: -99.1332, name: 'Ciudad de México', region: 'CDMX', country: 'México' },
        'guadalajara': { lat: 20.6597, lon: -103.3496, name: 'Guadalajara', region: 'Jalisco', country: 'México' },
        'monterrey': { lat: 25.6866, lon: -100.3161, name: 'Monterrey', region: 'Nuevo León', country: 'México' },
        'cancun': { lat: 21.1619, lon: -86.8515, name: 'Cancún', region: 'Quintana Roo', country: 'México' },
        'merida': { lat: 20.9674, lon: -89.5926, name: 'Mérida', region: 'Yucatán', country: 'México' },
        'tijuana': { lat: 32.5027, lon: -117.0037, name: 'Tijuana', region: 'Baja California', country: 'México' },
        'puebla': { lat: 19.0414, lon: -98.2063, name: 'Puebla', region: 'Puebla', country: 'México' },
        'leon': { lat: 21.1289, lon: -101.6860, name: 'León', region: 'Guanajuato', country: 'México' },
        'juarez': { lat: 31.6904, lon: -106.4245, name: 'Ciudad Juárez', region: 'Chihuahua', country: 'México' },
        'acapulco': { lat: 16.8531, lon: -99.8237, name: 'Acapulco', region: 'Guerrero', country: 'México' },
        'veracruz': { lat: 19.1738, lon: -96.1342, name: 'Veracruz', region: 'Veracruz', country: 'México' },
        'toluca': { lat: 19.2926, lon: -99.6568, name: 'Toluca', region: 'Estado de México', country: 'México' },
        'chihuahua': { lat: 28.6353, lon: -106.0889, name: 'Chihuahua', region: 'Chihuahua', country: 'México' },
        'tampico': { lat: 22.2331, lon: -97.8614, name: 'Tampico', region: 'Tamaulipas', country: 'México' }
    },
    
    // Lista de ubicaciones para sugerencias
    LOCATION_SUGGESTIONS: [
        { name: 'Oaxaca', region: 'Oaxaca', country: 'México' },
        { name: 'Ciudad de México', region: 'CDMX', country: 'México' },
        { name: 'Guadalajara', region: 'Jalisco', country: 'México' },
        { name: 'Monterrey', region: 'Nuevo León', country: 'México' },
        { name: 'Cancún', region: 'Quintana Roo', country: 'México' },
        { name: 'Mérida', region: 'Yucatán', country: 'México' },
        { name: 'Tijuana', region: 'Baja California', country: 'México' },
        { name: 'Puebla', region: 'Puebla', country: 'México' },
        { name: 'León', region: 'Guanajuato', country: 'México' },
        { name: 'Ciudad Juárez', region: 'Chihuahua', country: 'México' },
        { name: 'Acapulco', region: 'Guerrero', country: 'México' },
        { name: 'Veracruz', region: 'Veracruz', country: 'México' },
        { name: 'Toluca', region: 'Estado de México', country: 'México' },
        { name: 'Chihuahua', region: 'Chihuahua', country: 'México' },
        { name: 'Tampico', region: 'Tamaulipas', country: 'México' }
    ],
    
    // Configuración de iconos climáticos (usando iconos libres)
    WEATHER_ICONS: {
        clear: '☀️',
        cloudy: '☁️',
        partlyCloudy: '⛅',
        rain: '🌧️',
        drizzle: '🌦️',
        snow: '❄️',
        thunderstorm: '⛈️',
        fog: '🌫️',
        wind: '💨'
    },
    
    // Mensajes de la aplicación
    MESSAGES: {
        LOADING: 'Cargando datos...',
        ERROR_LOCATION: 'Ubicación no encontrada. Intenta con otra ciudad.',
        ERROR_BACKEND: 'Error conectando con el servidor. Usando datos de demostración.',
        BACKEND_DEMO: 'Modo demostración - Backend no disponible',
        BACKEND_ONLINE: 'Conectado al backend',
        ML_PREDICTION: 'Predicción generada con Machine Learning'
    }
};

// Función para buscar ubicación por nombre
window.findLocationByName = function(cityName) {
    const config = window.EventWeatherConfig;
    const searchKey = cityName.toLowerCase()
        .replace(/\s+/g, '')
        .replace('ciudad', '')
        .replace('de', '')
        .replace('san', '')
        .replace('santa', '');
    
    // Buscar en ubicaciones predefinidas
    for (const [key, location] of Object.entries(config.PREDEFINED_LOCATIONS)) {
        const locationKey = key.toLowerCase();
        const locationName = location.name.toLowerCase();
        
        if (locationKey.includes(searchKey) || 
            searchKey.includes(locationKey) ||
            locationName.includes(searchKey) ||
            searchKey.includes(locationName.replace(/\s+/g, ''))) {
            return location;
        }
    }
    
    return null;
};

// Función para obtener sugerencias filtradas
window.getFilteredSuggestions = function(query) {
    const config = window.EventWeatherConfig;
    const searchQuery = query.toLowerCase();
    
    return config.LOCATION_SUGGESTIONS.filter(location => 
        location.name.toLowerCase().includes(searchQuery) ||
        location.region.toLowerCase().includes(searchQuery)
    ).slice(0, 5);
};

console.log('Configuración Event Weather cargada - Solo Backend');