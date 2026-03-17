DROP TABLE IF EXISTS advisories;
DROP TABLE IF EXISTS weather_logs;
DROP TABLE IF EXISTS sensor_readings;
DROP TABLE IF EXISTS farm_nodes;
DROP TABLE IF EXISTS farmers;

CREATE TABLE farmers(
    id INTEGER PRIMARY KEY NOT NULL,
    phone_number VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);

CREATE TABLE farm_nodes(
    node_id VARCHAR(255) PRIMARY KEY NOT NULL,
    farmer_id INTEGER NOT NULL,
    latitude DECIMAL(8, 2) NOT NULL,
    longitude DECIMAL(8, 2) NOT NULL,
    crop_type VARCHAR(255) NULL,
    installed_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,

    FOREIGN KEY (farmer_id) REFERENCES farmers(id)
);

CREATE TABLE sensor_readings(
    id BIGINT PRIMARY KEY NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    moisture_pct DECIMAL(8, 2) NOT NULL,
    ph DECIMAL(8, 2) NOT NULL,
    nitrogen_mg_kg INTEGER NOT NULL,
    phosphorus_mg_kg INTEGER NOT NULL,
    potassium_mg_kg INTEGER NOT NULL,
    soil_temp_c DECIMAL(8, 2) NOT NULL,
    air_temp_c DECIMAL(8, 2) NOT NULL,
    air_humid_pct DECIMAL(8, 2) NOT NULL,

    FOREIGN KEY (node_id) REFERENCES farm_nodes(node_id)
);

CREATE TABLE weather_logs(
    id BIGINT PRIMARY KEY NOT NULL,
    reading_id BIGINT NOT NULL,
    forecast_rain_7d_mm DECIMAL(8, 2) NOT NULL,
    forecast_avg_temp_c DECIMAL(8, 2) NOT NULL,

    FOREIGN KEY (reading_id) REFERENCES sensor_readings(id)
);

CREATE TABLE advisories(
    id BIGINT PRIMARY KEY NOT NULL,
    reading_id BIGINT NOT NULL,
    ai_model VARCHAR(255) NOT NULL,
    message_content TEXT NOT NULL,
    sent_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    status VARCHAR(255) NOT NULL,

    FOREIGN KEY (reading_id) REFERENCES sensor_readings(id)
);
