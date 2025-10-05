-- Schema para base de datos de modelos climáticos
-- PostgreSQL

-- Tabla principal de modelos
CREATE TABLE trained_models (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    variable_name VARCHAR(100) NOT NULL, -- Temperature_C, Humidity_Percent, etc.
    model_data BYTEA NOT NULL, -- Modelo serializado
    model_metadata JSONB, -- Métricas, parámetros, etc.
    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accuracy_score DECIMAL(5, 4),
    mean_absolute_error DECIMAL(10, 6),
    r2_score DECIMAL(5, 4),
    data_points_count INTEGER,
    geographic_hash VARCHAR(50), -- Para búsquedas rápidas por región
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas eficientes
CREATE INDEX idx_geographic_location ON trained_models (latitude, longitude);
CREATE INDEX idx_variable_name ON trained_models (variable_name);
CREATE INDEX idx_geographic_hash ON trained_models (geographic_hash);
CREATE INDEX idx_accuracy ON trained_models (accuracy_score DESC);

-- Tabla para caché de predicciones
CREATE TABLE prediction_cache (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    prediction_date DATE NOT NULL,
    predictions JSONB NOT NULL,
    model_versions JSONB, -- IDs de modelos usados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(latitude, longitude, prediction_date)
);

-- Tabla de métricas de uso
CREATE TABLE model_usage_stats (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES trained_models(id),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    average_response_time DECIMAL(8, 3), -- ms
    success_rate DECIMAL(5, 4)
);

-- Función para calcular hash geográfico (para agrupar por regiones)
CREATE OR REPLACE FUNCTION calculate_geo_hash(lat DECIMAL, lon DECIMAL)
RETURNS VARCHAR(50) AS $$
BEGIN
    -- Simplificado: redondear a 0.1 grados (aprox 11km)
    RETURN ROUND(lat, 1)::TEXT || ',' || ROUND(lon, 1)::TEXT;
END;
$$ LANGUAGE plpgsql;