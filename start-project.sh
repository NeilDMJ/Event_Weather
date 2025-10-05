#!/bin/bash

# Script para iniciar el proyecto completo
# Uso: ./start-project.sh

echo " Iniciando Weather Prediction App..."
echo "======================================"

# Directorio base del proyecto
PROJECT_DIR="/home/dante/Documents/Proyectos/event_weather"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Verificar que estamos en el directorio correcto
if [ ! -d "$PROJECT_DIR" ]; then
    echo " Error: No se encontró el directorio del proyecto en $PROJECT_DIR"
    exit 
fi

echo "📁 Directorio del proyecto: $PROJECT_DIR"

# Función para iniciar el backend
start_backend() {
    echo ""
    echo " Iniciando Backend FastAPI..."
    echo "--------------------------------"
    
    cd "$BACKEND_DIR"
    
    # Verificar que existe el entorno virtual
    if [ ! -d "env" ]; then
        echo " Error: No se encontró el entorno virtual en $BACKEND_DIR/env"
        echo "   Crea el entorno virtual primero: python -m venv env"
        exit 
    fi
    
    # Activar entorno virtual e iniciar servidor
    source env/bin/activate
    
    echo " Entorno virtual activado"
    echo " Iniciando servidor en http://localhost:"
    echo " Documentación disponible en http://localhost:/docs"
    echo ""
    echo "Para detener el servidor, presiona Ctrl+C"
    echo "=============================================="
    
    # Iniciar servidor FastAPI
    uvicorn app.main:app --reload --host ... --port 
}

# Función para iniciar el frontend
start_frontend() {
    echo ""
    echo " Iniciando Frontend..."
    echo "------------------------"
    
    cd "$FRONTEND_DIR"
    
    echo " Servidor frontend disponible en http://localhost:"
    echo "🧪 Página de pruebas en http://localhost:/test-api.html"
    echo ""
    echo "Para detener el servidor, presiona Ctrl+C"
    echo "==========================================="
    
    # Iniciar servidor HTTP simple
    python -m http.server 
}

# Función para mostrar ayuda
show_help() {
    echo ""
    echo "Uso: $ [opción]"
    echo ""
    echo "Opciones:"
    echo "  backend     Iniciar solo el backend (puerto )"
    echo "  frontend    Iniciar solo el frontend (puerto )"
    echo "  test        Abrir página de pruebas de la API"
    echo "  help        Mostrar esta ayuda"
    echo ""
    echo "Sin opciones: Muestra instrucciones para inicio manual"
    echo ""
}

# Función para mostrar URLs importantes
show_urls() {
    echo ""
    echo " URLs importantes:"
    echo "==================="
    echo " Backend API:              http://localhost:"
    echo " Documentación API:        http://localhost:/docs"
    echo " Frontend:                 http://localhost:"
    echo "🧪 Pruebas API:              http://localhost:/test-api.html"
    echo " Dashboard original:       http://localhost:/index.html"
    echo ""
}

# Función para abrir página de pruebas
open_test_page() {
    echo "🧪 Abriendo página de pruebas..."
    
    if command -v xdg-open > /dev/null; then
        xdg-open "http://localhost:/test-api.html"
    elif command -v open > /dev/null; then
        open "http://localhost:/test-api.html"
    else
        echo " Abre manualmente: http://localhost:/test-api.html"
    fi
}

# Procesar argumentos
case "$" in
    "backend")
        start_backend
        ;;
    "frontend")
        start_frontend
        ;;
    "test")
        open_test_page
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    "")
        echo "Para iniciar el proyecto completo:"
        echo ""
        echo "  Terminal  - Backend:"
        echo "   cd $BACKEND_DIR"
        echo "   source env/bin/activate"
        echo "   uvicorn app.main:app --reload --host ... --port "
        echo ""
        echo "  Terminal  - Frontend:"
        echo "   cd $FRONTEND_DIR"
        echo "   python -m http.server "
        echo ""
        echo "O usa los comandos directos:"
        echo "   $ backend    # Solo backend"
        echo "   $ frontend   # Solo frontend"
        echo "   $ test       # Abrir pruebas"
        
        show_urls
        ;;
    *)
        echo " Opción desconocida: $"
        show_help
        exit 
        ;;
esac