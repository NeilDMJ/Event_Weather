document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. SELECTORES DE ELEMENTOS DEL DOM ---
    const searchForm = document.querySelector('.search-form');
    const citySearchInput = document.getElementById('city-search-input');
    const suggestionsContainer = document.getElementById('suggestions-container');
    const locationNameElement = document.getElementById('location-name');

    // Variables para el mapa y el marcador
    let map;
    let marker;
    const API_KEY = '95d485525131456b8e1231409250410'; // <-- ¡IMPORTANTE! Reemplaza esto

    // --- LÓGICA DE ACTUALIZACIÓN DE FECHA Y HORA ---
    function updateDateTime() {
        const now = new Date();
        const timeOptions = { hour: '2-digit', minute: '2-digit', hour12: true };
        try {
            document.getElementById('current-time').textContent = now.toLocaleTimeString('es-ES', timeOptions);
        } catch(e) { console.error("Elemento de hora no encontrado"); }
    }
    updateDateTime();
    setInterval(updateDateTime, 60000);

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

    // --- FUNCIÓN PRINCIPAL PARA OBTENER CLIMA Y COORDENADAS ---
    async function getWeatherForCity(city) {
        const apiUrl = `https://api.weatherapi.com/v1/forecast.json?key=${API_KEY}&q=${city}&days=5&aqi=no&alerts=no&lang=es`;
        
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error('Ciudad no encontrada');
            }
            const data = await response.json();
            const { lat, lon, name, region } = data.location;
            updateMap(lat, lon, `${name}, ${region}`);
            // Aquí en el futuro, actualizarias las tarjetas del clima con `data`
        } catch (error) {
            console.error('Error al buscar la ciudad:', error);
            alert('Ciudad no encontrada. Por favor, intenta con otro nombre.');
        }
    }

    // --- LÓGICA PARA SUGERENCIAS DE BÚSQUEDA ---
    
    // Función para obtener sugerencias
    async function getSearchSuggestions(query) {
        if (query.length < 3) { // Solo buscar si hay al menos 3 caracteres
            suggestionsContainer.innerHTML = '';
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

    // Función para mostrar las sugerencias en el DOM
    function displaySuggestions(suggestions) {
        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        suggestionsContainer.innerHTML = ''; // Limpiar sugerencias anteriores
        suggestions.forEach(location => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            suggestionItem.textContent = `${location.name}, ${location.region}, ${location.country}`;
            
            suggestionItem.addEventListener('click', () => {
                citySearchInput.value = location.name;
                getWeatherForCity(location.name);
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.style.display = 'none';
            });
            
            suggestionsContainer.appendChild(suggestionItem);
        });

        suggestionsContainer.style.display = 'block'; // Mostrar el contenedor
    }

    // Event listener para el input de búsqueda que se activa al escribir
    citySearchInput.addEventListener('input', () => {
        getSearchSuggestions(citySearchInput.value);
    });

    // Ocultar sugerencias si se hace clic fuera
    document.addEventListener('click', (event) => {
        if (!event.target.closest('.search-wrapper')) {
            suggestionsContainer.style.display = 'none';
        }
    });

    // --- EVENT LISTENER PARA EL FORMULARIO DE BÚSQUEDA ---
    searchForm.addEventListener('submit', (event) => {
        event.preventDefault(); 
        const cityName = citySearchInput.value.trim();
        if (cityName) {
            getWeatherForCity(cityName);
            suggestionsContainer.innerHTML = '';
            suggestionsContainer.style.display = 'none';
        }
    });

    // --- INICIALIZACIÓN DEL GRÁFICO ---
    const ctx = document.getElementById('summaryChart');
    new Chart(ctx, { 
        type: 'line', data: { labels: ['4 PM','5 PM','6 PM','7 PM','8 PM','9 PM','10 PM'], datasets: [{ label: 'Temperatura (°C)', data: [24,24,23,22,21,20,19], fill: true, backgroundColor: 'rgba(54, 162, 235, 0.2)', borderColor: 'rgba(54, 162, 235, 1)', tension: 0.4, pointBackgroundColor: '#fff', pointBorderColor: 'rgba(54, 162, 235, 1)' }] }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: false, grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: 'var(--text-muted)' } }, x: { grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: 'var(--text-muted)' } } }, plugins: { legend: { display: false } } }
    });

    // --- INICIALIZACIÓN AL CARGAR LA PÁGINA ---
    initMap(17.804, -97.772, 'Huajuapan de León');
    getWeatherForCity('Huajuapan de León');
});

