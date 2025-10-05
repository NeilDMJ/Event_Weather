#!/bin/bash

echo "🔍 Verificando configuración para deployment en Vercel..."
echo "========================================================="

PROJECT_DIR="/home/dante/Documents/Proyectos/event_weather"
cd "$PROJECT_DIR"

# Verificar archivos esenciales
echo ""
echo "📁 Verificando archivos esenciales:"

files_to_check=(
    "vercel.json"
    "package.json"
    "frontend/index.html"
    "frontend/css/style.css"
    "frontend/js/app.js"
    "frontend/js/api-client.js"
)

all_files_exist=true

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - FALTANTE"
        all_files_exist=false
    fi
done

echo ""
echo "📋 Verificando configuración de Vercel:"

# Verificar vercel.json
if [ -f "vercel.json" ]; then
    echo "✅ vercel.json existe"
    if grep -q "frontend" vercel.json; then
        echo "✅ Configuración de frontend encontrada"
    else
        echo "⚠️  Configuración de frontend no encontrada en vercel.json"
    fi
else
    echo "❌ vercel.json no encontrado"
fi

echo ""
echo "🌐 Verificando referencias de URL en el frontend:"

# Verificar URLs en los archivos JS
if [ -f "frontend/js/api-client.js" ]; then
    if grep -q "localhost:8000" frontend/js/api-client.js; then
        echo "⚠️  URL localhost encontrada en api-client.js"
        echo "   Cambiar a URL de producción del backend antes del deployment"
    else
        echo "✅ No hay URLs localhost en api-client.js"
    fi
fi

echo ""
echo "📊 Estadísticas del proyecto:"
echo "-----------------------------"

if [ -d "frontend" ]; then
    html_files=$(find frontend -name "*.html" | wc -l)
    css_files=$(find frontend -name "*.css" | wc -l)
    js_files=$(find frontend -name "*.js" | wc -l)
    
    echo "📄 Archivos HTML: $html_files"
    echo "🎨 Archivos CSS: $css_files"
    echo "⚡ Archivos JS: $js_files"
    
    # Tamaño del frontend
    frontend_size=$(du -sh frontend 2>/dev/null | cut -f1)
    echo "📦 Tamaño frontend: $frontend_size"
fi

echo ""
echo "🔧 Comandos de deployment:"
echo "-------------------------"
echo ""
echo "1. Instalar Vercel CLI (si no lo tienes):"
echo "   npm i -g vercel"
echo ""
echo "2. Hacer deployment:"
echo "   vercel"
echo ""
echo "3. O deployment automático:"
echo "   - Push a GitHub"
echo "   - Importar en vercel.com"
echo ""

if [ "$all_files_exist" = true ]; then
    echo "🎉 LISTO PARA DEPLOYMENT"
    echo "========================"
    echo "Todos los archivos esenciales están presentes."
    echo "Puedes proceder con el deployment en Vercel."
else
    echo "⚠️  HAY ARCHIVOS FALTANTES"
    echo "=========================="
    echo "Revisa los archivos marcados como faltantes antes del deployment."
fi

echo ""
echo "📋 Checklist final:"
echo "-------------------"
echo "□ Todos los archivos existen"
echo "□ vercel.json configurado"
echo "□ URLs de backend actualizadas"
echo "□ Código pusheado a GitHub"
echo "□ Repositorio conectado a Vercel"
echo ""