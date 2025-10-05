document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. SELECTORES DE ELEMENTOS DEL DOM ---
    const searchForm = document.querySelector('.search-form');
    const citySearchInput = document.getElementById('city-search-input');
    const dateInput = document.getElementById('date');
    const suggestionsContainer = document.getElementById('suggestions-container');
    const locationNameElement = document.getElementById('location-name');

    const mainCard = {
        day: document.querySelector('.current-weather-card .card-header h2'),
        date: document.querySelector('.current-weather-card .card-header .time'),
        temp: document.querySelector('.current-weather-card .temperature'),
        icon: document.querySelector('.current-weather-card .weather-icon'),
        realFeel: document.querySelector('.weather-details p:nth-child(1)'),
        wind: document.querySelector('.weather-details p:nth-child(2)'),
        pressure: document.querySelector('.weather-details p:nth-child(3)'),
        humidity: document.querySelector('.weather-details p:nth-child(4)')
    };
    const miniCards = document.querySelectorAll('.mini-card');

    // --- VARIABLES GLOBALES ---
    let map;
    let marker;
    let currentTileLayer;
    // Removido API_KEY - ya no usamos APIs externas, solo nuestro backend
    let currentForecastData = null;
    let newSummaryChartInstance = null;

    // --- FUNCIÓN PARA OBTENER LA FECHA DE HOY EN FORMATO YYYY-MM-DD ---
    function getTodayDateString() {
        const today = new Date();
        const year = today.getFullYear();
        const month = (today.getMonth() + 1).toString().padStart(2, '0');
        const day = today.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    // --- LÓGICA DE NAVEGACIÓN ACTIVA ---
    const navButtons = document.querySelectorAll('.time-nav button');
    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            navButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        });
    });

    // --- LÓGICA DEL MAPA ---
    function getMapTileUrl() {
        const theme = document.body.getAttribute('data-theme') || 'dark';
        if (theme === 'light') {
            return 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
        }
        return 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    }

    function initMap(lat, lon, cityName) {
        if (map) {
            updateMap(lat, lon, cityName);
            return;
        }
        map = L.map('mi_mapa').setView([lat, lon], 13);
        currentTileLayer = L.tileLayer(getMapTileUrl(), {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        }).addTo(map);
        marker = L.marker([lat, lon]).addTo(map).bindPopup(cityName).openPopup();
        locationNameElement.textContent = cityName;
    }
    
    function updateMapTheme() {
        if (map && currentTileLayer) {
            map.removeLayer(currentTileLayer);
            currentTileLayer = L.tileLayer(getMapTileUrl(), {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            }).addTo(map);
        }
    }
    
    function updateMap(lat, lon, cityName) {
        map.setView([lat, lon], 13);
        marker.setLatLng([lat, lon]).setPopupContent(cityName).openPopup();
        locationNameElement.textContent = cityName;
    }

    // --- FUNCIÓN PARA ACTUALIZAR TODA LA UI DEL CLIMA (CORREGIDA) ---
    function updateWeatherUI(forecastData, selectedDateStr) {
        const forecastDays = forecastData.forecast.forecastday;
        
        let selectedIndex = forecastDays.findIndex(day => day.date === selectedDateStr);
        if (selectedIndex === -1) {
            console.warn("La fecha seleccionada está fuera del rango de pronóstico. Mostrando el primer día.");
            selectedIndex = 0;
            dateInput.value = forecastDays[0].date;
        }

        const selectedDayData = forecastDays[selectedIndex];
        const dateObj = new Date(selectedDayData.date + 'T12:00:00');
        const dayName = dateObj.toLocaleDateString('es-ES', { weekday: 'long' });

        // 1. Actualizar la tarjeta principal
        mainCard.day.textContent = dayName.charAt(0).toUpperCase() + dayName.slice(1);
        mainCard.date.textContent = dateObj.toLocaleDateString('es-ES', { day: 'numeric', month: 'long' });
        mainCard.temp.textContent = `${Math.round(selectedDayData.day.avgtemp_c)}°`;
        mainCard.icon.src = `https:${selectedDayData.day.condition.icon}`;
        mainCard.icon.alt = selectedDayData.day.condition.text;
        mainCard.realFeel.textContent = `Sensación: ${Math.round(selectedDayData.day.avgtemp_c)}°`;
        mainCard.wind.textContent = `Viento: ${selectedDayData.day.maxwind_kph} km/h`;
        mainCard.pressure.textContent = `Presión: ${forecastData.current.pressure_mb}mb`;
        mainCard.humidity.textContent = `Humedad: ${selectedDayData.day.avghumidity}%`;

        // 2. CORREGIDO: Actualizar las 2 mini-cards con los 2 días posteriores al DÍA SELECCIONADO
        const miniCardsArray = Array.from(miniCards).reverse();
        
        for (let i = 0; i < 2; i++) {
            const miniCard = miniCardsArray[i];
            const forecastIndex = selectedIndex + i + 1; 
            
            miniCard.style.display = 'none';
            miniCard.onclick = null;

            if (forecastIndex < forecastDays.length) {
                const dayData = forecastDays[forecastIndex];
                const miniDateObj = new Date(dayData.date + 'T12:00:00');
                
                miniCard.querySelector('header h2').textContent = miniDateObj.toLocaleDateString('es-ES', { weekday: 'short' }).toUpperCase().replace('.', '');
                miniCard.querySelector('img').src = `https:${dayData.day.condition.icon}`;
                miniCard.querySelector('img').alt = dayData.day.condition.text;
                miniCard.querySelector('footer h3').textContent = `${Math.round(dayData.day.avgtemp_c)}°`;
                miniCard.style.display = 'flex';

                // RESTAURADO: Hacer la tarjeta clickeable
            }
        }
        
        // RESTAURADO: Actualizar los límites del input date
        if (forecastDays.length > 0) {
            dateInput.min = forecastDays[0].date;
            dateInput.max = forecastDays[forecastDays.length - 1].date;
        }
    }

    // --- FUNCIÓN PARA ACTUALIZAR LA TARJETA PRINCIPAL CON DATOS DE LA API DE PREDICCIÓN ---
    function updateMainCardWithPrediction(predictionData, weatherData, selectedDate) {
        try {
            // Verificar que tenemos datos de predicción
            if (!predictionData || !predictionData.predictions) {
                console.warn('No hay datos de predicción disponibles, usando datos de WeatherAPI');
                return; // Mantenemos los datos actuales de WeatherAPI
            }

            const pred = predictionData.predictions;
            const dateObj = new Date(selectedDate + 'T12:00:00');
            const dayName = dateObj.toLocaleDateString('es-ES', { weekday: 'long' });

            // Actualizar día y fecha
            mainCard.day.textContent = dayName.charAt(0).toUpperCase() + dayName.slice(1);
            mainCard.date.textContent = dateObj.toLocaleDateString('es-ES', { day: 'numeric', month: 'long' });

            // Usar datos de predicción del backend
            mainCard.temp.textContent = `${Math.round(pred.temperature_c || pred.temperature_max_c || 0)}°`;
            
            // Mantener icono de WeatherAPI si está disponible, o usar uno basado en la predicción
            if (weatherData && weatherData.forecast) {
                const weatherDay = weatherData.forecast.forecastday.find(day => day.date === selectedDate);
                if (weatherDay) {
                    mainCard.icon.src = `https:${weatherDay.day.condition.icon}`;
                    mainCard.icon.alt = weatherDay.day.condition.text;
                } else {
                    // Usar icono genérico basado en precipitación
                    if (pred.precipitation_mm_per_day > 5) {
                        mainCard.icon.src = "https://www.amcharts.com/wp-content/themes/amcharts4/css/img/icons/weather/animated/rainy-1.svg";
                        mainCard.icon.alt = "Lluvia esperada";
                    } else if (pred.cloud_cover_percent > 70) {
                        mainCard.icon.src = "https://www.amcharts.com/wp-content/themes/amcharts4/css/img/icons/weather/animated/cloudy-day-1.svg";
                        mainCard.icon.alt = "Nublado";
                    } else {
                        mainCard.icon.src = "https://www.amcharts.com/wp-content/themes/amcharts4/css/img/icons/weather/animated/day.svg";
                        mainCard.icon.alt = "Despejado";
                    }
                }
            }

            // Actualizar detalles con datos de predicción
            const realFeelTemp = pred.temperature_c || pred.temperature_max_c || 0;
            mainCard.realFeel.textContent = `Sensación: ${Math.round(realFeelTemp)}°`;
            mainCard.wind.textContent = `Viento: ${Math.round((pred.wind_speed_ms || 0) * 3.6)} km/h`; // Convertir m/s a km/h
            mainCard.pressure.textContent = `Presión: ${Math.round((pred.pressure_kpa || 0) * 10)}mb`; // Convertir kPa a mb
            mainCard.humidity.textContent = `Humedad: ${Math.round(pred.humidity_percent || 0)}%`;

            // Agregar información adicional de predicción
            console.log('Datos de predicción aplicados:', {
                temperatura: pred.temperature_c,
                precipitacion: pred.precipitation_mm_per_day,
                humedad: pred.humidity_percent,
                viento: pred.wind_speed_ms,
                presion: pred.pressure_kpa,
                nubosidad: pred.cloud_cover_percent
            });

        } catch (error) {
            console.error('Error actualizando tarjeta principal con predicción:', error);
            // En caso de error, mantener los datos actuales
        }
    }

    // --- FUNCIÓN PRINCIPAL PARA OBTENER CLIMA ---
    async function getWeatherForCity(cityOrCoords) {
        try {
            // Convertir nombre de ciudad a coordenadas usando configuración global
            let lat, lon, name, region, country;
            
            if (typeof cityOrCoords === 'string') {
                // Si es string, buscar coordenadas por nombre de ciudad
                const locationData = window.findLocationByName(cityOrCoords);
                if (locationData) {
                    lat = locationData.lat;
                    lon = locationData.lon;
                    name = locationData.name;
                    region = locationData.region;
                    country = locationData.country;
                } else {
                    throw new Error('Ubicación no encontrada');
                }
            } else {
                // Si ya son coordenadas
                lat = cityOrCoords.lat;
                lon = cityOrCoords.lon;
                name = cityOrCoords.name || 'Ubicación personalizada';
                region = cityOrCoords.region || '';
                country = cityOrCoords.country || '';
            }

            // Obtener predicción de tu backend
            const selectedDate = dateInput.value || getTodayDateString();
            const prediction = await weatherAPI.getPrediction(lat, lon, selectedDate);
            
            if (prediction && prediction.success) {
                // Crear datos de forecast simulado basado en la predicción
                currentForecastData = createForecastDataFromPrediction(prediction, name, region, country);
                
                // Actualizar mapa y UI
                initMap(lat, lon, `${name}, ${region}`);
                updateWeatherUI(currentForecastData, selectedDate);
                
                // Mostrar información adicional de la predicción
                showPredictionInfo(prediction);
            } else {
                throw new Error('No se pudo obtener la predicción del clima');
            }

        } catch (error) {
            console.error('Error al buscar la ubicación:', error);
            alert('Error al obtener el clima. Por favor, intenta con otra ubicación.');
        }
    }

    // --- FUNCIONES PARA COMUNICAR CON LA API BACKEND ---
    async function sendDataToApi({ date, name, region, country, lat, lon }) {
        const aiPromptEl = document.getElementById('ai-prompt');
        if (aiPromptEl) aiPromptEl.textContent = 'Generando predicción...';

        try {
            // Usar la API client en lugar de fetch directo
            const result = await weatherAPI.getPrediction(lat, lon, date);

            // Verificar si tenemos datos reales o datos demo
            const isDemo = result.note && result.note.includes('demostración');
            
            if (aiPromptEl) {
                // Mostrar un prompt resumido en la sección new-chart-card
                const preds = result.predictions || {};
                const lines = [];
                lines.push(`Predicción para ${name}, ${region || country} el ${result.prediction_date || date}:`);
                
                if (isDemo) {
                    lines.push('(Modo demostración - Backend no disponible)');
                }
                
                for (const [k, v] of Object.entries(preds)) {
                    lines.push(`- ${k.replace(/_/g, ' ')}: ${v}`);
                }
                lines.push(`(Generado: ${new Date(result.generated_at || new Date()).toLocaleString('es-ES')})`);
                aiPromptEl.textContent = lines.join('\n');
            }

            // Actualizar gráfico newSummaryChart con al menos temperatura y precipitación si existen
            const labels = ['Predicción'];
            const datasets = [];
            const preds = result.predictions || {};
            
            if ('temperature_c' in preds) {
                datasets.push({ 
                    label: 'Temp (°C)', 
                    data: [preds.temperature_c], 
                    borderColor: 'rgba(255,99,132,1)', 
                    backgroundColor: 'rgba(255,99,132,0.2)' 
                });
            }
            if ('precipitation_mm_per_day' in preds) {
                datasets.push({ 
                    label: 'Precipitación (mm/d)', 
                    data: [preds.precipitation_mm_per_day], 
                    borderColor: 'rgba(54,162,235,1)', 
                    backgroundColor: 'rgba(54,162,235,0.2)' 
                });
            }
            if (datasets.length === 0) {
                // Datos alternativos: mostrar humedad y nubosidad si no hay temp/precip
                if ('humidity_percent' in preds) {
                    datasets.push({ 
                        label: 'Humedad (%)', 
                        data: [preds.humidity_percent], 
                        borderColor: 'rgba(75,192,192,1)', 
                        backgroundColor: 'rgba(75,192,192,0.2)' 
                    });
                }
                if ('cloud_cover_percent' in preds) {
                    datasets.push({ 
                        label: 'Nubosidad (%)', 
                        data: [preds.cloud_cover_percent], 
                        borderColor: 'rgba(201,203,207,1)', 
                        backgroundColor: 'rgba(201,203,207,0.2)' 
                    });
                }
            }

            // Actualizar el gráfico
            const ctx = document.getElementById('newSummaryChart');
            if (ctx && datasets.length > 0) {
                const config = { 
                    type: 'bar', 
                    data: { labels, datasets }, 
                    options: { 
                        responsive: true, 
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: isDemo ? 'Predicción (Modo Demo)' : 'Predicción IA'
                            }
                        }
                    } 
                };

                if (newSummaryChartInstance) {
                    // Reemplazar los datos y actualizar
                    newSummaryChartInstance.data = config.data;
                    newSummaryChartInstance.options = config.options;
                    newSummaryChartInstance.update();
                } else {
                    newSummaryChartInstance = new Chart(ctx, config);
                }
            }

            // NUEVO: Actualizar la tarjeta principal con datos de predicción
            updateMainCardWithPrediction(result, currentForecastData, date);

            return result;

        } catch (error) {
            console.error('Error obteniendo predicción:', error);
            if (aiPromptEl) {
                aiPromptEl.textContent = `Error: No se pudo conectar al backend. Mostrando datos de WeatherAPI.`;
            }
            // En caso de error, la tarjeta principal mantendrá los datos de WeatherAPI
            throw error;
        }
    }

    // --- LÓGICA PARA SUGERENCIAS DE BÚSQUEDA ---
    async function getSearchSuggestions(query) {
        if (query.length < 3) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        try {
            // Usar ubicaciones predefinidas de la configuración global
            const suggestions = window.getFilteredSuggestions(query);
            displaySuggestions(suggestions);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            suggestionsContainer.style.display = 'none';
        }
    }
    
    function displaySuggestions(suggestions) {
        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        suggestionsContainer.innerHTML = '';
        suggestions.forEach(location => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.textContent = `${location.name}, ${location.region}, ${location.country}`;
            item.addEventListener('click', () => {
                citySearchInput.value = location.name;
                getWeatherForCity(location.name);
                suggestionsContainer.style.display = 'none';
            });
            suggestionsContainer.appendChild(item);
        });
        suggestionsContainer.style.display = 'block';
    }
    
    citySearchInput.addEventListener('input', () => getSearchSuggestions(citySearchInput.value));
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-wrapper')) {
            suggestionsContainer.style.display = 'none';
        }
    });

    // --- EVENT LISTENERS ---
    searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const cityName = citySearchInput.value.trim();
        if (cityName) {
            getWeatherForCity(cityName);
            suggestionsContainer.style.display = 'none';
        }
    });

    // RESTAURADO: Event listener para el calendario
    dateInput.addEventListener('change', () => {
        if (currentForecastData) {
            updateWeatherUI(currentForecastData, dateInput.value);
        }
    });

    // --- INICIALIZACIÓN DE GRÁFICOS ---
    const chartOptions = { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: false, grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: 'var(--text-muted)' } }, x: { grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: 'var(--text-muted)' } } }, plugins: { legend: { display: false } } };
    const chartData = { labels: ['4 PM','5 PM','6 PM','7 PM','8 PM','9 PM','10 PM'], datasets: [{ label: 'Temperatura (°C)', data: [24,24,23,22,21,20,19], fill: true, backgroundColor: 'rgba(54, 162, 235, 0.2)', borderColor: 'rgba(54, 162, 235, 1)', tension: 0.4 }] };

    const ctx1 = document.getElementById('summaryChart');
    new Chart(ctx1, { type: 'line', data: chartData, options: chartOptions });

    const ctx2 = document.getElementById('newSummaryChart');
    new Chart(ctx2, { type: 'line', data: chartData, options: chartOptions });

    // --- FUNCIONES AUXILIARES PARA BACKEND ---
    
    // Crear datos de forecast simulado basado en la predicción
    function createForecastDataFromPrediction(prediction, name, region, country) {
        const pred = prediction.predictions;
        const predDate = prediction.prediction_date;
        
        return {
            location: {
                name: name,
                region: region,
                country: country,
                lat: prediction.location.latitude,
                lon: prediction.location.longitude
            },
            current: {
                temp_c: pred.temperature_c,
                condition: {
                    text: getWeatherConditionText(pred),
                    icon: getWeatherIcon(pred)
                },
                wind_kph: pred.wind_speed_ms * 3.6,
                pressure_mb: pred.pressure_kpa * 10,
                humidity: pred.humidity_percent,
                feelslike_c: pred.temperature_c + (pred.humidity_percent > 70 ? 2 : -1),
                is_day: 1
            },
            forecast: {
                forecastday: [{
                    date: predDate,
                    day: {
                        maxtemp_c: pred.temperature_max_c,
                        mintemp_c: pred.temperature_min_c,
                        avgtemp_c: pred.temperature_c,
                        totalprecip_mm: pred.precipitation_mm_per_day,
                        avghumidity: pred.humidity_percent,
                        condition: {
                            text: getWeatherConditionText(pred),
                            icon: getWeatherIcon(pred)
                        }
                    },
                    hour: generateHourlyData(pred)
                }]
            }
        };
    }
    
    // Generar texto de condición climática basado en la predicción
    function getWeatherConditionText(pred) {
        if (pred.precipitation_mm_per_day > 10) return 'Lluvia';
        if (pred.precipitation_mm_per_day > 1) return 'Llovizna';
        if (pred.cloud_cover_percent > 80) return 'Nublado';
        if (pred.cloud_cover_percent > 50) return 'Parcialmente nublado';
        return 'Despejado';
    }
    
    // Obtener icono de clima basado en la predicción
    function getWeatherIcon(pred) {
        if (pred.precipitation_mm_per_day > 10) return '//cdn.weatherapi.com/weather/64x64/day/302.png';
        if (pred.precipitation_mm_per_day > 1) return '//cdn.weatherapi.com/weather/64x64/day/296.png';
        if (pred.cloud_cover_percent > 80) return '//cdn.weatherapi.com/weather/64x64/day/119.png';
        if (pred.cloud_cover_percent > 50) return '//cdn.weatherapi.com/weather/64x64/day/116.png';
        return '//cdn.weatherapi.com/weather/64x64/day/113.png';
    }
    
    // Generar datos por horas simulados
    function generateHourlyData(pred) {
        const hours = [];
        for (let i = 0; i < 24; i++) {
            const temp = pred.temperature_c + Math.sin(i * Math.PI / 12) * (pred.temperature_max_c - pred.temperature_min_c) / 2;
            hours.push({
                time: `${i.toString().padStart(2, '0')}:00`,
                temp_c: Math.round(temp * 10) / 10,
                condition: {
                    text: getWeatherConditionText(pred),
                    icon: getWeatherIcon(pred)
                },
                wind_kph: pred.wind_speed_ms * 3.6,
                humidity: pred.humidity_percent,
                pressure_mb: pred.pressure_kpa * 10
            });
        }
        return hours;
    }
    
    // Mostrar información de la predicción
    function showPredictionInfo(prediction) {
        // Buscar elemento AI prompt para mostrar info
        const aiPromptEl = document.getElementById('ai-prompt');
        if (aiPromptEl) {
            aiPromptEl.innerHTML = `
                <strong>🤖 Predicción ML generada</strong><br>
                Fecha: ${prediction.prediction_date}<br>
                Ubicación: ${prediction.location.latitude.toFixed(4)}, ${prediction.location.longitude.toFixed(4)}<br>
                <small>Generado: ${new Date(prediction.generated_at).toLocaleString()}</small>
            `;
        }
        
        // También mostrar en consola
        console.log('✅ Predicción ML cargada:', prediction);
    }

    // --- FUNCIÓN DE INICIALIZACIÓN ---
    function initializeApp() {
        dateInput.value = getTodayDateString();
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    getWeatherForCity(`${position.coords.latitude},${position.coords.longitude}`);
                },
                () => {
                    console.warn("El usuario denegó la geolocalización. Cargando ubicación por defecto.");
                    getWeatherForCity('Huajuapan de León');
                }
            );
        } else {
            console.error("La geolocalización no es soportada por este navegador.");
            getWeatherForCity('Huajuapan de León');
        }
    }

    initializeApp();

    // --- FUNCIONALIDAD DE CAMBIO DE TEMA ---
    const themeToggleBtn = document.querySelector('.theme-switcher');
    
    // Cargar tema guardado o usar el tema oscuro por defecto
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', currentTheme);
    
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Actualizar el mapa con el nuevo tema
        updateMapTheme();
    });
});

