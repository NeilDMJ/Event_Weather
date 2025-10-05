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
        map = L.map('mi_mapa').setView([lat, lon], 13);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        }).addTo(map);
        marker = L.marker([lat, lon]).addTo(map).bindPopup(cityName).openPopup();
        locationNameElement.textContent = cityName;
    }
    
    function updateMap(lat, lon, cityName) {
        map.setView([lat, lon], 13);
        marker.setLatLng([lat, lon]).setPopupContent(cityName).openPopup();
        locationNameElement.textContent = cityName;
    }

    // --- FUNCIÓN PARA ACTUALIZAR TODA LA UI DEL CLIMA (CON 6 DÍAS POSTERIORES) ---
    function updateWeatherUI(forecastData, selectedDateStr) {
        const forecastDays = forecastData.forecast.forecastday;
        
        // Encontrar el índice del día seleccionado
        let selectedIndex = forecastDays.findIndex(day => day.date === selectedDateStr);
        if (selectedIndex === -1) {
            console.warn("La fecha seleccionada está fuera del rango de pronóstico. Mostrando el primer día.");
            selectedIndex = 0;
            dateInput.value = forecastDays[0].date;
        }

        const selectedDayData = forecastDays[selectedIndex];
        const dateObj = new Date(selectedDayData.date + 'T12:00:00');
        const dayName = dateObj.toLocaleDateString('es-ES', { weekday: 'long' });

        // 1. Actualizar la tarjeta principal (día actual seleccionado)
        mainCard.day.textContent = dayName.charAt(0).toUpperCase() + dayName.slice(1);
        mainCard.date.textContent = dateObj.toLocaleDateString('es-ES', { day: 'numeric', month: 'long' });
        mainCard.temp.textContent = `${Math.round(selectedDayData.day.avgtemp_c)}°`;
        mainCard.icon.src = selectedDayData.day.condition.icon;
        mainCard.icon.alt = selectedDayData.day.condition.text;
        mainCard.realFeel.textContent = `Sensación: ${Math.round(selectedDayData.day.avgtemp_c)}°`;
        mainCard.wind.textContent = `Viento: ${selectedDayData.day.maxwind_kph} km/h`;
        mainCard.pressure.textContent = `Presión: ${forecastData.current.pressure_mb}mb`;
        mainCard.humidity.textContent = `Humedad: ${selectedDayData.day.avghumidity}%`;

        // 2. Actualizar las 6 mini-cards con los SIGUIENTES 6 días posteriores al seleccionado
        for (let i = 0; i < 6; i++) {
            const cardIndex = selectedIndex + 1 + i; // Comienza desde el día SIGUIENTE al seleccionado
            const miniCard = miniCards[i];
            
            // Ocultar por defecto
            miniCard.style.display = 'none';
            miniCard.classList.remove('selected');
            miniCard.onclick = null;

            // Si el índice es válido Y está dentro del rango del forecast, mostrar la card
            if (cardIndex >= 0 && cardIndex < forecastDays.length) {
                const dayData = forecastDays[cardIndex];
                const miniDateObj = new Date(dayData.date + 'T12:00:00');
                
                miniCard.querySelector('header h2').textContent = miniDateObj.toLocaleDateString('es-ES', { weekday: 'short' }).toUpperCase().replace('.', '');
                miniCard.querySelector('img').src = dayData.day.condition.icon;
                miniCard.querySelector('img').alt = dayData.day.condition.text;
                miniCard.querySelector('footer h3').textContent = `${Math.round(dayData.day.avgtemp_c)}°`;
                miniCard.style.display = 'flex';

                // Hacer la tarjeta clickeable - al hacer clic, ese día se convierte en el principal
                miniCard.onclick = () => {
                    dateInput.value = dayData.date;
                    updateWeatherUI(currentForecastData, dayData.date);
                };
            }
        }
        
        // Actualizar los límites del input date basado en los datos disponibles
        if (forecastDays.length > 0) {
            dateInput.min = forecastDays[0].date;
            dateInput.max = forecastDays[forecastDays.length - 1].date;
        }
    }

    // --- FUNCIÓN PRINCIPAL PARA OBTENER CLIMA ---
    async function getWeatherForCity(cityOrCoords) {
        const apiUrl = `https://api.weatherapi.com/v1/forecast.json?key=${API_KEY}&q=${cityOrCoords}&days=14&aqi=no&alerts=no&lang=es`;
        
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Ubicación no encontrada');
            
            const data = await response.json();
            currentForecastData = data;

            const { lat, lon, name, region } = data.location;
            initMap(lat, lon, `${name}, ${region}`);
            updateWeatherUI(currentForecastData, dateInput.value);

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

    dateInput.addEventListener('change', () => {
        if (currentForecastData) {
            const forecastDays = currentForecastData.forecast.forecastday;
            const selectedDate = dateInput.value;
            
            // Verificar si la fecha seleccionada está dentro del rango disponible
            const dateExists = forecastDays.some(day => day.date === selectedDate);
            
            if (dateExists) {
                updateWeatherUI(currentForecastData, selectedDate);
            } else {
                alert('La fecha seleccionada no está disponible. Por favor, selecciona una fecha dentro del rango permitido.');
                dateInput.value = forecastDays[0].date;
                updateWeatherUI(currentForecastData, forecastDays[0].date);
            }
        }
    });

    // --- INICIALIZACIÓN DEL GRÁFICO ---
    const ctx = document.getElementById('summaryChart');
    new Chart(ctx, { 
        type: 'line', 
        data: { 
            labels: ['4 PM','5 PM','6 PM','7 PM','8 PM','9 PM','10 PM'], 
            datasets: [{ 
                label: 'Temperatura (°C)', 
                data: [24,24,23,22,21,20,19], 
                fill: true, 
                backgroundColor: 'rgba(54, 162, 235, 0.2)', 
                borderColor: 'rgba(54, 162, 235, 1)', 
                tension: 0.4, 
                pointBackgroundColor: '#fff', 
                pointBorderColor: 'rgba(54, 162, 235, 1)' 
            }] 
        }, 
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            scales: { 
                y: { 
                    beginAtZero: false, 
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }, 
                    ticks: { color: 'var(--text-muted)' } 
                }, 
                x: { 
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }, 
                    ticks: { color: 'var(--text-muted)' } 
                } 
            }, 
            plugins: { 
                legend: { display: false } 
            } 
        } 
    });

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
});