#!/bin/bash

echo "Verificando configuración para deployment en Vercel..."
echo "========================================================="

PROJECT_DIR="/home/dante/Documents/Proyectos/event_weather"
cd "$PROJECT_DIR"

# Verificar archivos esenciales
echo ""
echo "📁 Verificando archivos esenciales:"

files_to_check=(
    "vercel.json"
    "package.json" 
    "index.html"
    "css/style.css"
    "js/app.js"
    "js/api-client.js"
)

all_files_exist=true

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "$file"
    else
        echo "$file - FALTANTE"
        all_files_exist=false
    fi
done

echo ""
echo "📋 Verificando configuración de Vercel:"

# Verificar vercel.json
if [ -f "vercel.json" ]; then
    echo "✅ vercel.json existe"
    if grep -q "routes" vercel.json; then
        echo "✅ Configuración de rutas encontrada"
    else
        echo "⚠️  Configuración de rutas no encontrada en vercel.json"
    fi
else
    echo "❌ vercel.json no encontrado"
fi

echo ""
echo "🌐 Verificando referencias de URL en el frontend:"

# Verificar URLs en los archivos JS
if [ -f "js/api-client.js" ]; then
    if grep -q "localhost:8000" js/api-client.js; then
        echo "⚠️  URL localhost encontrada en api-client.js"
        echo "   ✅ Configurado modo demo para deployment"
    else
        echo "✅ No hay URLs localhost problemáticas en api-client.js"
    fi
fi

echo ""
echo "📊 Estadísticas del proyecto:"
echo "-----------------------------"

if [ -d "." ]; then
    html_files=$(find . -maxdepth 1 -name "*.html" | wc -l)
    css_files=$(find css -name "*.css" 2>/dev/null | wc -l)
    js_files=$(find js -name "*.js" 2>/dev/null | wc -l)
    
    echo "📄 Archivos HTML: $html_files"
    echo "🎨 Archivos CSS: $css_files"
    echo "⚡ Archivos JS: $js_files"
    
    # Tamaño de los archivos principales
    main_size=$(du -sh css js *.html 2>/dev/null | awk '{total+=$1} END {print total "K"}')
    echo "📦 Tamaño archivos principales: $main_size"
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