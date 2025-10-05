# 🌤️ Event Weather - Dashboard Climático con ML

![Weather Dashboard](https://img.shields.io/badge/Status-Active-success)
![Version](https://img.shields.io/badge/Version-2.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)

Dashboard climático con predicciones de Machine Learning usando datos de NASA POWER.

## 🚀 Deployment en Vercel

### Pasos para desplegar:

1. **Fork o clona este repositorio**
2. **Conecta tu repositorio con Vercel:**
   - Ve a [vercel.com](https://vercel.com)
   - Importa tu repositorio de GitHub
   - Selecciona la carpeta raíz del proyecto

3. **Configuración automática:**
   - Vercel detectará automáticamente el `vercel.json`
   - No necesitas configuración adicional

### 📂 Estructura del proyecto:

```
event_weather/
├── frontend/          # Frontend estático
│   ├── index.html     # Dashboard principal
│   ├── test-api.html  # Página de pruebas
│   ├── css/           # Estilos
│   └── js/            # Scripts
├── backend/           # API FastAPI (no se despliega en Vercel)
├── vercel.json        # Configuración de Vercel
└── package.json       # Metadatos del proyecto
```

## 🌐 URLs importantes:

- **Frontend en Vercel:** https://tu-proyecto.vercel.app
- **Dashboard principal:** https://tu-proyecto.vercel.app/
- **Página de pruebas:** https://tu-proyecto.vercel.app/test-api.html

## ⚙️ Configuración

### Frontend (Vercel):
- ✅ Desplegado automáticamente
- ✅ CDN global
- ✅ HTTPS automático

### Backend (separado):
- 🔧 Desplegar en Railway, Render, o similar
- 🔧 Actualizar URL del backend en `js/api-client.js`

## 🛠️ Desarrollo local

```bash
# Clonar repositorio
git clone <tu-repo>
cd event_weather

# Iniciar frontend
cd frontend
python3 -m http.server 3000

# Iniciar backend (separado)
cd backend
source env/bin/activate
uvicorn app.main:app --reload --port 8000
```

## 📋 Solución de problemas

### Error 404 en Vercel:

1. **Verificar vercel.json:** El archivo debe estar en la raíz
2. **Estructura de carpetas:** Mantener frontend/ como subdirectorio
3. **Rutas:** Verificar que las rutas en vercel.json sean correctas

### API no funciona:

1. **CORS:** Verificar configuración en el backend
2. **URL:** Actualizar URL del backend en el frontend
3. **Backend:** Desplegar backend por separado

## 🔧 Comandos útiles

```bash
# Despliegue manual con Vercel CLI
npx vercel

# Ver logs de Vercel
npx vercel logs

# Configurar variables de entorno
npx vercel env add
```

## 📝 Notas técnicas

- **Frontend:** HTML/CSS/JS puro, compatible con Vercel Static
- **Backend:** FastAPI con ML models (requiere servidor Python)
- **APIs externas:** WeatherAPI para datos básicos
- **ML:** Modelos propios para predicciones avanzadas

## 🎯 Features

- ✅ Dashboard responsivo
- ✅ Mapas interactivos (Leaflet)
- ✅ Gráficos dinámicos (Chart.js)
- ✅ Predicciones ML
- ✅ Búsqueda de ciudades
- ✅ Datos históricos

---

**Desarrollado por:** SaviDevs  
**Version:** 2.0.0  
**Licencia:** MIT