#!/bin/bash

echo "Iniciando servidor local para pruebas..."
echo "========================================"

# Verificar si estamos en el directorio correcto
if [ ! -f "index.html" ]; then
    echo "No se encontró index.html"
    echo "   Ejecutar desde la raíz del proyecto event_weather"
    exit 1
fi

echo "Archivos del proyecto encontrados:"
echo "   $(ls -1 *.html | wc -l) archivos HTML"
echo "   $(ls -1 css/*.css 2>/dev/null | wc -l) archivos CSS"
echo "   $(ls -1 js/*.js 2>/dev/null | wc -l) archivos JS"
echo ""

echo "Iniciando servidor en puerto 3000..."
echo "Abrir en el navegador: http://localhost:3000"

echo ""
echo "Iniciando servidor en puerto 3000..."
echo "Abrir en el navegador: http://localhost:3000"
echo ""
echo "URLs de prueba:"
echo ""
echo "URLs disponibles:"
echo "   Dashboard: http://localhost:3000/"
echo "   Test API:  http://localhost:3000/test-api.html"
echo ""
echo "Para detener: Ctrl+C"
echo "======================================"

# Iniciar servidor HTTP simple
python3 -m http.server 3000