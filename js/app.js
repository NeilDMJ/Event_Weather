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
    const API_KEY = '95d485525131456b8e1231409250410';
    let currentForecastData = null;

    // --- FUNCIÓN DE DETECCIÓN DE NAVEGADOR PARA DEBUGGING ---
    function detectBrowser() {
        const userAgent = navigator.userAgent;
        if (userAgent.includes('Firefox')) {
            console.log('Detectado Firefox - aplicando configuraciones específicas para el mapa');
            return 'firefox';
        } else if (userAgent.includes('Edg')) {
            console.log('Detectado Edge');
            return 'edge';
        } else if (userAgent.includes('OPR') || userAgent.includes('Opera')) {
            console.log('Detectado Opera');
            return 'opera';
        } else if (userAgent.includes('Chrome') && userAgent.includes('Brave')) {
            console.log('Detectado Brave - aplicando configuraciones específicas para el mapa');
            return 'brave';
        } else if (userAgent.includes('Chrome')) {
            console.log('Detectado Chrome');
            return 'chrome';
        }
        return 'unknown';
    }

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
    function initMap(lat, lon, cityName) {
        if (map) {
            updateMap(lat, lon, cityName);
            return;
        }

        // Esperar a que el contenedor esté visible y tenga dimensiones
        const mapContainer = document.getElementById('mi_mapa');
        if (!mapContainer || mapContainer.offsetWidth === 0) {
            setTimeout(() => initMap(lat, lon, cityName), 100);
            return;
        }

        const browser = detectBrowser();
        const isFirefoxOrBrave = browser === 'firefox' || browser === 'brave';

        try {
            // Configuraciones específicas para Firefox y Brave
            const mapOptions = {
                zoomControl: true,
                scrollWheelZoom: true,
                doubleClickZoom: true,
                boxZoom: true,
                keyboard: true,
                dragging: true,
                touchZoom: true,
                preferCanvas: isFirefoxOrBrave, // Usar canvas en lugar de SVG para mejor rendimiento
                renderer: isFirefoxOrBrave ? L.canvas() : undefined
            };

            map = L.map('mi_mapa', mapOptions).setView([lat, lon], 13);

            // Configuración del tile layer con opciones específicas para navegadores problemáticos
            const tileOptions = {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                maxZoom: 18,
                subdomains: ['a', 'b', 'c', 'd'],
                crossOrigin: true
            };

            if (isFirefoxOrBrave) {
                tileOptions.detectRetina = false; // Desactivar detección de retina en navegadores problemáticos
                tileOptions.updateWhenIdle = true; // Actualizar tiles solo cuando el mapa esté quieto
            }

            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', tileOptions).addTo(map);

            marker = L.marker([lat, lon]).addTo(map).bindPopup(cityName).openPopup();
            locationNameElement.textContent = cityName;

            // Forzar recalculación del tamaño después de la inicialización
            // Tiempo extendido para Firefox y Brave
            const invalidateDelay = isFirefoxOrBrave ? 500 : 250;
            setTimeout(() => {
                if (map) {
                    map.invalidateSize();
                    console.log(`Mapa invalidado después de ${invalidateDelay}ms para ${browser}`);
                }
            }, invalidateDelay);

        } catch (error) {
            console.error('Error al inicializar el mapa:', error);
            // Reintentar en caso de error con delay más largo para navegadores problemáticos
            const retryDelay = isFirefoxOrBrave ? 1000 : 500;
            setTimeout(() => initMap(lat, lon, cityName), retryDelay);
        }
    }
    
    function updateMap(lat, lon, cityName) {
        try {
            map.setView([lat, lon], 13);
            marker.setLatLng([lat, lon]).setPopupContent(cityName).openPopup();
            locationNameElement.textContent = cityName;
            
            // Asegurar que el mapa se redibuje correctamente
            setTimeout(() => {
                if (map) {
                    map.invalidateSize();
                }
            }, 100);
        } catch (error) {
            console.error('Error al actualizar el mapa:', error);
            // En caso de error, reinicializar el mapa
            map = null;
            marker = null;
            initMap(lat, lon, cityName);
        }
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
                miniCard.onclick = () => {
                    dateInput.value = dayData.date;
                    updateWeatherUI(currentForecastData, dayData.date);
                };
            }
        }
        
        // RESTAURADO: Actualizar los límites del input date
        if (forecastDays.length > 0) {
            dateInput.min = forecastDays[0].date;
            dateInput.max = forecastDays[forecastDays.length - 1].date;
        }
    }

    // --- FUNCIÓN PRINCIPAL PARA OBTENER CLIMA ---
    async function getWeatherForCity(cityOrCoords) {
        // Pedimos 14 días para tener un buen rango para el calendario
        const apiUrl = `https://api.weatherapi.com/v1/forecast.json?key=${API_KEY}&q=${cityOrCoords}&days=14&aqi=no&alerts=no&lang=es`;
        
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Ubicación no encontrada');
            
            const data = await response.json();
            currentForecastData = data;

            const { lat, lon, name, region } = data.location;
            
            // Actualizar UI del clima primero
            updateWeatherUI(currentForecastData, dateInput.value);
            
            // Inicializar mapa con un pequeño delay para permitir que el DOM se estabilice
            setTimeout(() => {
                initMap(lat, lon, `${name}, ${region}`);
            }, 150);

        } catch (error) {
            console.error('Error al buscar la ubicación:', error);
            alert('Ubicación no encontrada. Por favor, intenta con otro nombre.');
        }
    }

    // --- LÓGICA PARA SUGERENCIAS DE BÚSQUEDA ---
    async function getSearchSuggestions(query) {
        if (query.length < 3) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        const apiUrl = `https://api.weatherapi.com/v1/search.json?key=${API_KEY}&q=${query}`;
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) return;
            const suggestions = await response.json();
            displaySuggestions(suggestions);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
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


    // --- FUNCIÓN DE INICIALIZACIÓN ---
    function initializeApp() {
        dateInput.value = getTodayDateString();
        
        // Agregar listener para resize de ventana
        window.addEventListener('resize', () => {
            if (map) {
                setTimeout(() => {
                    map.invalidateSize();
                }, 100);
            }
        });

        // Agregar observer para detectar cambios en el contenedor del mapa
        if (window.ResizeObserver) {
            const mapContainer = document.getElementById('mi_mapa');
            if (mapContainer) {
                const resizeObserver = new ResizeObserver(() => {
                    if (map) {
                        setTimeout(() => {
                            map.invalidateSize();
                        }, 50);
                    }
                });
                resizeObserver.observe(mapContainer);
            }
        }

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
});

